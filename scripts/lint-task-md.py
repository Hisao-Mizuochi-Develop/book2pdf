#!/usr/bin/env python3
"""
Markdown pipe-table column alignment validator.

Validates that all pipe-table rows within the same section have
consistent | (pipe) counts. Exits with code 1 if mismatches found.

Target files: docs/**/*.md, */docs/**/*.md, and any *.md in the project.
"""

import sys
from pathlib import Path
from typing import List, Tuple

EXCLUDED_DIRS = {"node_modules", "reference", "kindle_env", ".venv", "venv", "dist", "build", "test-results", "test_cases"}


def is_excluded(md_file: Path) -> bool:
    """Check if file path contains excluded directories."""
    return any(part in EXCLUDED_DIRS for part in md_file.parts)


def find_md_files() -> List[Path]:
    """Find all Markdown files in the project."""
    root = Path(".").resolve()
    md_files = []

    # Target patterns
    patterns = ["docs/**/*.md", "*/docs/**/*.md"]
    for pattern in patterns:
        for f in root.glob(pattern):
            if not is_excluded(f):
                md_files.append(f)

    # Also check any other .md files that might contain tables
    for md_file in root.rglob("*.md"):
        if md_file in md_files or is_excluded(md_file):
            continue
        # Check if file contains pipe-table patterns
        content = md_file.read_text(encoding="utf-8")
        if "|" in content and "---" in content:
            md_files.append(md_file)

    # Remove duplicates and sort
    seen = set()
    unique_files = []
    for f in md_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    return sorted(unique_files)


def validate_file(file_path: Path) -> List[Tuple[int, int, int]]:
    """
    Validate a single Markdown file.
    Returns list of (line_number, current_nf, expected_nf) for mismatches.
    """
    mismatches = []
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Track pipe counts per section
    # A section is bounded by ## headings or --- horizontal rules
    # (excluding table delimiter lines)
    section_expected_nf = None
    in_code_block = False

    for line_num, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        # Toggle code block state on fenced blocks (``` or ~~~)
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Section boundary: ## / ### heading or --- (but not table delimiter like |---|)
        if stripped.startswith("## ") or stripped.startswith("### "):
            section_expected_nf = None
            continue

        if stripped == "---":
            # Horizontal rule (not table delimiter)
            section_expected_nf = None
            continue

        # Check if this is a table row (starts with |)
        if stripped.startswith("|"):
            # Temporarily replace escaped pipes so they don't split cells
            temp = stripped.replace("\\|", "\x00ESCPI\x00")
            # Count pipes (NF in awk -F'|')
            parts = temp.split("|")
            nf = len(parts)

            # First table row in section sets the expectation
            if section_expected_nf is None:
                section_expected_nf = nf
            elif nf != section_expected_nf:
                mismatches.append((line_num, nf, section_expected_nf))

    return mismatches


def main() -> int:
    """Main entry point."""
    md_files = find_md_files()

    if not md_files:
        print("No Markdown files found.")
        return 0

    all_ok = True
    total_files = 0
    total_mismatches = 0

    for md_file in md_files:
        # Skip hidden directories (.git, .github, .cline, etc.)
        if any(part.startswith(".") for part in md_file.parts):
            continue

        mismatches = validate_file(md_file)
        total_files += 1

        if mismatches:
            all_ok = False
            total_mismatches += len(mismatches)
            print(f"\n❌ {md_file}")
            for line_num, actual_nf, expected_nf in mismatches:
                print(
                    f"   Line {line_num}: pipe count mismatch "
                    f"(actual={actual_nf}, expected={expected_nf})"
                )
        else:
            print(f"✅ {md_file}")

    print(f"\n{'=' * 50}")
    print(f"Files checked: {total_files}")
    if all_ok:
        print("Result: ALL PASS ✨")
        return 0
    else:
        print(f"Result: {total_mismatches} mismatch(es) found 🚨")
        print("\nFix: Ensure all table rows in the same section have the same number of | delimiters.")
        print("      Add missing '|  |  |  |' at the end of truncated rows.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
