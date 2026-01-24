#!/bin/bash
#
# Validate CloudFormation templates using AWS CLI.
# This script mirrors the pre-commit hook for local use.
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] [FILE...]

Validate AWS CloudFormation templates using the AWS CLI.

Arguments:
  FILE...     One or more template files to validate.
              If not specified, validates all .yaml/.yml files in the repo.

Options:
  -h, --help  Show this help message and exit.

Examples:
  $(basename "$0")                           # Validate all templates
  $(basename "$0") vpc/eks/default/stack.yaml  # Validate specific file
  $(basename "$0") runner/*.yaml             # Validate multiple files

Requirements:
  - AWS CLI must be installed and configured
  - Valid AWS credentials (for cloudformation:ValidateTemplate)

EOF
    exit 0
}

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        -h|--help)
            usage
            ;;
    esac
done

# Check for AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed.${NC}"
    echo "Install it from: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Get files to validate
if [ $# -gt 0 ]; then
    FILES="$@"
else
    # Find all yaml files, excluding hidden dirs and scripts
    FILES=$(find "$REPO_ROOT" -type f \( -name "*.yaml" -o -name "*.yml" \) \
        -not -path "$REPO_ROOT/.*" \
        -not -path "$REPO_ROOT/scripts/*" \
        | sort)
fi

if [ -z "$FILES" ]; then
    echo "No templates found to validate."
    exit 0
fi

echo -e "${GREEN}Validating CloudFormation templates...${NC}"
echo

errors=0
for file in $FILES; do
    # Handle both absolute and relative paths
    if [[ "$file" = /* ]]; then
        filepath="$file"
    else
        filepath="$REPO_ROOT/$file"
    fi

    if [ ! -f "$filepath" ]; then
        echo -e "  ${YELLOW}⚠ Skipping (not found): $file${NC}"
        continue
    fi

    echo -n "  Checking: $file ... "

    if output=$(aws --no-cli-pager cloudformation validate-template \
        --template-body "file://$filepath" 2>&1); then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        echo "$output" | sed 's/^/    /'
        ((errors++)) || true
    fi
done

echo

if [ $errors -gt 0 ]; then
    echo -e "${RED}❌ Validation failed: $errors template(s) have errors${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All templates are valid!${NC}"
    exit 0
fi
