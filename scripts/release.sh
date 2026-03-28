#!/bin/bash
# ============================================
# Open Trader - Release Helper Script
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔥 Open Trader - Release Helper${NC}"
echo ""

# Get current version from git tags
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo -e "${YELLOW}Versión actual: ${CURRENT_VERSION}${NC}"

# Function to bump version
bump_version() {
    local version=$1
    local bump_type=$2
    
    # Remove 'v' prefix
    version=${version#v}
    
    IFS='.' read -r -a parts <<< "$version"
    major=${parts[0]}
    minor=${parts[1]}
    patch=${parts[2]}
    
    case $bump_type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
    esac
    
    echo "v${major}.${minor}.${patch}"
}

# Menu
echo "Selecciona tipo de versión:"
echo "1) Patch (bug fixes) - ej: v0.1.0 → v0.1.1"
echo "2) Minor (new features) - ej: v0.1.0 → v0.2.0"
echo "3) Major (breaking changes) - ej: v0.1.0 → v1.0.0"
echo "4) Custom version"
echo ""
read -p "Opción (1-4): " choice

case $choice in
    1)
        NEW_VERSION=$(bump_version $CURRENT_VERSION patch)
        ;;
    2)
        NEW_VERSION=$(bump_version $CURRENT_VERSION minor)
        ;;
    3)
        NEW_VERSION=$(bump_version $CURRENT_VERSION major)
        ;;
    4)
        read -p "Nueva versión (ej: v0.2.0): " NEW_VERSION
        ;;
    *)
        echo -e "${RED}Opción inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Nueva versión: ${NEW_VERSION}${NC}"
echo ""

# Get release notes
echo "Escribe las notas de release (Ctrl+D para terminar):"
RELEASE_NOTES=$(cat)

# Update CHANGELOG.md
TODAY=$(date +%Y-%m-%d)

# Create temporary file with new entry
NEW_ENTRY="## [${NEW_VERSION}] - ${TODAY}

### Added
${RELEASE_NOTES}

"

# Insert after "## [Unreleased]"
sed -i "/## \[Unreleased\]/a\\
$NEW_ENTRY" CHANGELOG.md

echo -e "${GREEN}✅ CHANGELOG.md actualizado${NC}"

# Update version in main.py
sed -i "s/version=\"[^\"]*\"/version=\"${NEW_VERSION}\"/" backend/main.py

echo -e "${GREEN}✅ Versión actualizada en main.py${NC}"

# Git operations
echo ""
echo -e "${YELLOW}Git operations:${NC}"
echo "1. git add -A"
echo "2. git commit -m \"Release ${NEW_VERSION}\""
echo "3. git tag -a ${NEW_VERSION} -m \"${RELEASE_NOTES}\""
echo "4. git push origin main --tags"
echo ""
read -p "¿Ejecutar? (y/n): " confirm

if [[ $confirm == "y" || $confirm == "Y" ]]; then
    git add -A
    git commit -m "Release ${NEW_VERSION}"
    git tag -a ${NEW_VERSION} -m "${RELEASE_NOTES}"
    git push origin main --tags
    echo ""
    echo -e "${GREEN}🚀 Release ${NEW_VERSION} publicado!${NC}"
else
    echo "Operación cancelada"
fi
