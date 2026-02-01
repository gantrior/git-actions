#!/usr/bin/env bash
set -euo pipefail

# generate-release-notes.sh
# Generate release notes from git history
# Usage: generate-release-notes.sh <new_version> <last_tag>

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <new_version> <last_tag>" >&2
  exit 1
fi

NEW_VERSION="$1"
LAST_TAG="$2"

# Get commits since last tag
if [ "$LAST_TAG" = "v0.0.0" ]; then
  # First release - show a welcome message instead of full history
  COMMITS="- Initial release of Actions As Markdown framework"
else
  COMMITS=$(git log --oneline --pretty=format:"- %s" "$LAST_TAG"..HEAD)
  # If no commits (tag is at HEAD), indicate this is a workflow-triggered release
  if [ -z "$COMMITS" ]; then
    COMMITS="- Release workflow updates"
  fi
fi

# Create release notes
cat > release_notes.md << EOF
This is the latest set of releases that you can use with your agent of choice. We recommend using the Specify CLI to scaffold your projects, however you can download these independently and manage them yourself.

## Changelog

$COMMITS

EOF

echo "Generated release notes:"
cat release_notes.md
