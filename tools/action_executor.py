#!/usr/bin/env python3
"""Action executor CLI tool.

This tool executes pending actions from daily files and commits results.
It's designed to run in GitHub Actions workflows after PRs are merged.

Usage:
    python tools/action_executor.py --file actions/2026-01-15.md --commit
    python tools/action_executor.py --file actions/*.md  # Execute all files
"""

import argparse
import glob
import os
import subprocess
import sys

from tools.executor import execute_actions_from_file


def setup_git_config():
    """Configure git for automated commits."""
    try:
        # Set git user for automation
        subprocess.run(
            ["git", "config", "user.name", "GitHub Actions"], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "actions@github.com"], check=True, capture_output=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to configure git: {e}")


def get_environment():
    """Detect execution environment."""
    if os.environ.get("CI") == "true":
        return "ci"
    return "local"


def main():
    parser = argparse.ArgumentParser(description="Execute pending actions from daily files")
    parser.add_argument(
        "--file", required=True, help="Path to daily action file(s) to execute (supports wildcards)"
    )
    parser.add_argument(
        "--allowlist",
        default="actions/allowlist.yaml",
        help="Path to allowlist file (default: actions/allowlist.yaml)",
    )
    parser.add_argument(
        "--commit", action="store_true", help="Commit results to git after each action execution"
    )
    parser.add_argument(
        "--no-commit", action="store_true", help="Do not commit results (useful for testing)"
    )

    args = parser.parse_args()

    # Determine commit behavior
    should_commit = args.commit and not args.no_commit

    # Setup git if committing
    if should_commit:
        setup_git_config()

    # Print environment info
    env = get_environment()
    print(f"🔧 Environment: {env}")
    print(f"📝 Commit mode: {'enabled' if should_commit else 'disabled'}")

    # Expand glob patterns
    files = glob.glob(args.file)

    if not files:
        print(f"❌ No files found matching: {args.file}")
        return 1

    # Execute actions in each file
    total_executed = 0
    total_successful = 0
    total_failed = 0
    total_skipped = 0

    for file_path in files:
        # Skip non-markdown files
        if not file_path.endswith(".md"):
            continue

        # Skip if file doesn't exist
        if not os.path.exists(file_path):
            continue

        print(f"\n{'=' * 60}")
        print(f"📋 Executing actions from: {file_path}")
        print("=" * 60)

        try:
            report = execute_actions_from_file(
                file_path=file_path, allowlist_path=args.allowlist, commit=should_commit
            )

            # Print detailed report
            report.print_summary()

            # Update totals
            total_executed += report.executed_actions
            total_successful += report.successful_actions
            total_failed += report.failed_actions
            total_skipped += report.skipped_actions

            # Print individual results
            if report.results:
                print("\nDetailed results:")
                for result in report.results:
                    if result.status == "success":
                        print(f"  ✅ {result.action_id} ({result.action_name}): Success")
                    elif result.status == "error":
                        print(f"  ❌ {result.action_id} ({result.action_name}): {result.error}")
                    elif result.status == "skipped":
                        print(
                            f"  ⏭️  {result.action_id} ({result.action_name}): Skipped - {result.error}"
                        )

        except FileNotFoundError as e:
            print(f"❌ File not found: {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error executing {file_path}: {str(e)}")
            import traceback

            traceback.print_exc()
            return 1

    # Print final summary
    print(f"\n{'=' * 60}")
    print("📊 Final Summary")
    print("=" * 60)
    print(f"   Total executed: {total_executed}")
    print(f"   Successful: {total_successful}")
    print(f"   Failed: {total_failed}")
    print(f"   Skipped: {total_skipped}")

    # Exit with error if any actions failed
    if total_failed > 0:
        print(f"\n❌ {total_failed} action(s) failed")
        return 1

    print("\n✅ All actions executed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
