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

        # Determine if file was changed (for immutability check)
        # If no base ref provided, assume all files are changed (strict mode)
        file_changed = True
        if changed_files is not None:
            file_changed = file_path in changed_files
            if not file_changed:
                print("   ℹ️  File not modified in PR, skipping immutability check")

        try:
            result = validate_daily_file(
                file_path=file_path,
                allowlist_path=args.allowlist,
                schemas_dir=args.schemas,
                mode="pr",  # Strict PR mode
                file_changed=file_changed,
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
