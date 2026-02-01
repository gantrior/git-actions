#!/usr/bin/env python3
"""PR validation CLI tool.

This tool validates action files in PR mode (strict validation,
no execution). It's designed to run in GitHub Actions workflows
to validate PRs before merge.

Usage:
    python tools/pr_validator.py --file actions/2026-01-15.md
    python tools/pr_validator.py --file actions/*.md  # Validate all files
    python tools/pr_validator.py --file "actions/*.md" --base-ref origin/main
"""

import argparse
import glob
import os
import subprocess
import sys

from tools.parser import parse_daily_file
from tools.validator import validate_daily_file


def get_changed_files(base_ref: str) -> set:
    """Get list of files changed compared to base ref.

    Args:
        base_ref: Git reference to compare against (e.g., 'origin/main')

    Returns:
        Set of file paths that have been modified
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref],
            capture_output=True,
            text=True,
            check=True,
        )
        return set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not get changed files from git: {e}")
        return set()


def get_file_content_from_ref(file_path: str, ref: str) -> str | None:
    """Get the content of a file at a specific git ref.

    Args:
        file_path: Path to the file
        ref: Git reference (e.g., 'origin/main')

    Returns:
        File content as string, or None if file doesn't exist at that ref
    """
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{file_path}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        # File doesn't exist at that ref (new file)
        return None


def get_checked_actions_modified(file_path: str, base_ref: str) -> set:
    """Get the IDs of checked actions that were modified in the PR.

    Compares the current file content with the base ref to determine
    which checked actions have been modified. Only returns IDs of actions
    that are checked AND have different content from the base.

    Args:
        file_path: Path to the file to check
        base_ref: Git reference to compare against

    Returns:
        Set of action IDs that are checked and were modified
    """
    # Get base content
    base_content = get_file_content_from_ref(file_path, base_ref)
    if base_content is None:
        # File is new, so no checked actions could have been modified
        return set()

    # Read current content
    try:
        with open(file_path) as f:
            current_content = f.read()
    except FileNotFoundError:
        return set()

    # Parse actions from both versions
    try:
        base_actions = parse_daily_file(base_content, filename=file_path)
        current_actions = parse_daily_file(current_content, filename=file_path)
    except Exception:
        # If parsing fails, fall back to conservative behavior
        return set()

    # Build map of base actions by ID
    base_actions_map = {}
    for action in base_actions:
        base_actions_map[action.id] = action

    # Find checked actions that were modified
    modified_checked = set()
    for action in current_actions:
        if not action.is_checked:
            continue

        # Get base version of this action
        base_action = base_actions_map.get(action.id)
        if base_action is None:
            # Action is checked but didn't exist in base - this is suspicious
            # (how can a new action already be checked?)
            modified_checked.add(action.id)
            continue

        # Compare action content (inputs, outputs, meta)
        # Note: We compare the serialized forms to detect any changes
        if (
            action.inputs != base_action.inputs
            or action.outputs != base_action.outputs
            or action.meta != base_action.meta
            or action.name != base_action.name
            or action.version != base_action.version
        ):
            modified_checked.add(action.id)

    return modified_checked


def main():
    parser = argparse.ArgumentParser(description="Validate action files for PR review")
    parser.add_argument(
        "--file",
        required=True,
        help="Path to daily action file(s) to validate (supports wildcards)",
    )
    parser.add_argument(
        "--allowlist",
        default="actions/allowlist.yaml",
        help="Path to allowlist file (default: actions/allowlist.yaml)",
    )
    parser.add_argument(
        "--schemas",
        default="schemas/",
        help="Directory containing JSON schemas (default: schemas/)",
    )
    parser.add_argument(
        "--base-ref",
        default=None,
        help="Git base ref to compare against (e.g., 'origin/main'). "
        "When provided, immutability checks are only applied to files that "
        "have been modified compared to this ref.",
    )

    args = parser.parse_args()

    # Expand glob patterns
    files = glob.glob(args.file)

    if not files:
        print(f"❌ No files found matching: {args.file}")
        return 1

    # Get changed files if base ref is provided
    changed_files = None
    if args.base_ref:
        changed_files = get_changed_files(args.base_ref)
        if changed_files:
            print(f"📝 Files changed compared to {args.base_ref}: {len(changed_files)}")

    # Validate each file
    all_valid = True
    total_errors = 0

    for file_path in files:
        # Skip non-markdown files
        if not file_path.endswith(".md"):
            continue

        # Skip if file doesn't exist
        if not os.path.exists(file_path):
            continue

        print(f"\n📋 Validating: {file_path}")

        # Determine which checked actions were modified (for immutability check)
        # If no base ref provided, use legacy file_changed behavior (strict mode)
        modified_checked_actions = None
        file_changed = True

        if args.base_ref:
            # Use content-based comparison for precise immutability checking
            modified_checked_actions = get_checked_actions_modified(file_path, args.base_ref)
            if modified_checked_actions:
                print(f"   ⚠️  Checked actions modified: {modified_checked_actions}")
            else:
                print("   ℹ️  No checked actions were modified")
            # file_changed is still needed for backward compatibility
            if changed_files is not None:
                file_changed = file_path in changed_files

        try:
            result = validate_daily_file(
                file_path=file_path,
                allowlist_path=args.allowlist,
                schemas_dir=args.schemas,
                mode="pr",  # Strict PR mode
                file_changed=file_changed,
                modified_checked_actions=modified_checked_actions,
            )

            if result.is_valid:
                print(f"✅ {file_path}: All actions are valid")
                if result.warnings:
                    for warning in result.warnings:
                        print(f"   ⚠️  {warning}")
            else:
                print(f"❌ {file_path}: Validation failed")
                result.print_report()
                all_valid = False
                total_errors += len(result.errors)

        except FileNotFoundError as e:
            print(f"❌ File not found: {e}")
            all_valid = False
            total_errors += 1
        except Exception as e:
            print(f"❌ Unexpected error validating {file_path}: {str(e)}")
            all_valid = False
            total_errors += 1

    # Print summary
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ All validations passed!")
        return 0
    else:
        print(f"❌ Validation failed with {total_errors} error(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
