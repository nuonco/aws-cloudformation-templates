#!/usr/bin/env bash
#
# Publish */stack.yaml files to s3://nuon-artifacts/aws-cloudformation-templates/<subpath>/<stack>/stack.yaml
#
#   scripts/publish.sh <subpath> --retention <release|preview> [--markdown-out <file>] [--force] [<stack>...]
#
# Publishes every stack by default. Pass stack directories (e.g. runner/asg) to publish only those.
# Release subpaths are immutable unless --force is passed.

set -euo pipefail

BUCKET="${BUCKET:-nuon-artifacts}"
REGION="${AWS_REGION:-us-west-2}"
PREFIX="aws-cloudformation-templates"

subpath=""
retention=""
markdown_out=""
force="false"
only=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --retention)    retention="$2"; shift 2 ;;
    --markdown-out) markdown_out="$2"; shift 2 ;;
    --force)        force="true"; shift ;;
    -h|--help)      sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)             echo "unknown flag: $1" >&2; exit 2 ;;
    *)              if [[ -z "$subpath" ]]; then subpath="$1"; else only+=("${1#./}"); fi; shift ;;
  esac
done

if [[ -z "$subpath" ]]; then
  echo "error: <subpath> is required (e.g. v1.2.3 or preview/pr-42/abc1234)" >&2
  exit 2
fi
case "$retention" in
  release|preview) ;;
  *) echo "error: --retention must be release or preview" >&2; exit 2 ;;
esac
subpath="${subpath#/}"; subpath="${subpath%/}"
if [[ "$subpath" == *..* || -z "$subpath" ]]; then
  echo "error: invalid subpath: $subpath" >&2
  exit 2
fi

cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

if [[ -n "${only[*]:-}" ]]; then
  for stack in "${only[@]}"; do
    stack="${stack%/}"
    if [[ ! -f "$stack/stack.yaml" ]]; then
      echo "error: $stack/stack.yaml not found" >&2
      exit 2
    fi
  done
  stacks=$(printf '%s\n' "${only[@]%/}" | sort -u)
else
  stacks=$(find . -name stack.yaml -not -path './.git/*' | sed 's|^\./||; s|/stack\.yaml$||' | sort)
fi
if [[ -z "$stacks" ]]; then
  echo "error: no stack.yaml files found" >&2
  exit 1
fi

echo "> publishing to s3://$BUCKET/$PREFIX/$subpath/ (retention=$retention)"
urls=()
for stack in $stacks; do
  key="$PREFIX/$subpath/$stack/stack.yaml"
  url="https://$BUCKET.s3.$REGION.amazonaws.com/$key"

  if [[ "$retention" == "release" && "$force" != "true" ]]; then
    if aws s3api head-object --bucket "$BUCKET" --key "$key" >/dev/null 2>&1; then
      echo "error: $key already exists; releases are immutable (use --force to overwrite)" >&2
      exit 1
    fi
  fi

  aws s3api put-object \
    --bucket "$BUCKET" \
    --key "$key" \
    --body "$stack/stack.yaml" \
    --content-type "application/x-yaml" \
    --tagging "nuon-retention=$retention" \
    >/dev/null
  echo "  $stack -> $url"
  urls+=("$stack|$url")
done

if [[ -n "$markdown_out" ]]; then
  {
    echo "| stack | url |"
    echo "| --- | --- |"
    for entry in "${urls[@]}"; do
      echo "| \`${entry%%|*}\` | ${entry#*|} |"
    done
  } > "$markdown_out"
fi
