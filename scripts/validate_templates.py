#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "cfn-lint>=1.0.0",
# ]
# ///
"""
Validate AWS CloudFormation templates with strict parsing using cfn-lint.

Usage:
    uv run scripts/validate_templates.py [template_paths...]
    uv run scripts/validate_templates.py --strict  # Fail on warnings too

If no paths are provided, validates all .yaml and .yml files in the repository
(excluding hidden directories and scripts/).

Exit codes:
    0 - All templates valid
    1 - Errors found
    2 - Errors found (cfn-lint)
    4 - Warnings found (only with --strict)
"""

import subprocess
import sys
from pathlib import Path


def find_templates(root: Path) -> list[Path]:
    """Find all CloudFormation template files."""
    templates = []
    for pattern in ("**/*.yaml", "**/*.yml"):
        for path in root.glob(pattern):
            # Skip hidden directories and scripts
            if any(part.startswith(".") for part in path.parts):
                continue
            if "scripts" in path.parts:
                continue
            templates.append(path)
    return sorted(templates)


def main() -> int:
    """Main entry point."""
    root = Path(__file__).parent.parent
    strict = "--strict" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--strict"]

    if args:
        templates = [Path(p) for p in args]
    else:
        templates = find_templates(root)

    if not templates:
        print("No templates found to validate.")
        return 0

    print(f"Validating {len(templates)} CloudFormation template(s)...")
    if strict:
        print("(strict mode: warnings will cause failure)\n")
    else:
        print("(use --strict to fail on warnings)\n")

    has_errors = False
    has_warnings = False

    for template in templates:
        print(f"  Checking: {template.relative_to(root)}")

        cmd = ["cfn-lint", "--", str(template)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("    ✅ Valid")
        elif result.returncode == 4:
            # Warnings only
            has_warnings = True
            print("    ⚠️  Warnings:")
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    print(f"      {line}")
        else:
            # Errors
            has_errors = True
            print("    ❌ Errors:")
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    print(f"      {line}")

        if result.stderr:
            print(f"    stderr: {result.stderr}")

    print()

    if has_errors:
        print("❌ Validation failed: errors found")
        return 1
    elif has_warnings and strict:
        print("❌ Validation failed: warnings found (strict mode)")
        return 1
    elif has_warnings:
        print("⚠️  Validation passed with warnings")
        return 0
    else:
        print("✅ All templates are valid!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
