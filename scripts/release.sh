#!/bin/bash
# release.sh - Create a new release
# Usage: ./scripts/release.sh [patch|minor|major]
# Examples:
#   ./scripts/release.sh        # patch (0.1.0 -> 0.1.1)
#   ./scripts/release.sh minor # minor (0.1.0 -> 0.2.0)
#   ./scripts/release.sh major # major (0.1.0 -> 1.0.0)

set -e

# Get current version
CURRENT=$(grep 'CURRENT_VERSION = "' gui/main.py | sed 's/.*CURRENT_VERSION = "//;s/"//')
echo "Current version: $CURRENT"

# Parse version parts
IFS='.' read -r major minor patch <<< "$CURRENT"

# Bump version
BUMP_TYPE=${1:-patch}
case $BUMP_TYPE in
    major) major=$((major + 1)); minor=0; patch=0 ;;
    minor) minor=$((minor + 1)); patch=0 ;;
    patch) patch=$((patch + 1)) ;;
    *) echo "Invalid bump type: $BUMP_TYPE"; exit 1 ;;
esac

NEW_VERSION="$major.$minor.$patch"
echo "New version: $NEW_VERSION"

# Update version in gui/main.py
sed -i "s/CURRENT_VERSION = \".*\"/CURRENT_VERSION = \"$NEW_VERSION\"/" gui/main.py
sed -i "s/ee-invoice-generator GUI v.*/ee-invoice-generator GUI v$NEW_VERSION/" gui/main.py

# Commit
git add -A
git commit -m "Release v$NEW_VERSION"

# Create tag
git tag -a "v$NEW_VERSION" -m "v$NEW_VERSION"

# Push
echo ""
echo "Pushing to GitHub..."
git push origin master && git push origin "v$NEW_VERSION"

echo ""
echo "✅ Release v$NEW_VERSION created and pushed!"
echo "   GitHub Actions will build the .exe and create the release."
