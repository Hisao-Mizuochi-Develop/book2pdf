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


def validate_task_completion(file_path: Path) -> List[Tuple[int, str]]:
    """
    Validate that completed tasks (completion date filled) have implementation results.
    Only applies to *-TASKS.md files.
    Returns list of (line_number, message) for issues.
    """
    if not file_path.name.endswith("TASKS.md"):
        return []

    issues = []
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if this is a table row
        if not line.startswith("|"):
            i += 1
            continue

        # Split by | and strip whitespace
        parts = [p.strip() for p in line.split("|")]
        # Remove empty first/last elements from leading/trailing |
        if len(parts) >= 2 and parts[0] == "":
            parts = parts[1:]
        if len(parts) >= 1 and parts[-1] == "":
            parts = parts[:-1]

        # Must have 5 columns to be a task row
        if len(parts) != 5:
            i += 1
            continue

        task_no = parts[0]
        completion_date = parts[3]

        # Task rows have non-empty task_no and are not header rows
        if not task_no or task_no in ("タスクNO", "---") or task_no.startswith("-"):
            i += 1
            continue

        # If completion date is filled, check for implementation results
        if completion_date:
            found_results = False
            results_empty = True

            # Scan following lines for 【実施結果】
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()

                # Stop at next task row (non-empty task_no in 5-col table)
                if next_line.startswith("|"):
                    next_parts = [p.strip() for p in next_line.split("|")]
                    if len(next_parts) >= 2 and next_parts[0] == "":
                        next_parts = next_parts[1:]
                    if len(next_parts) >= 1 and next_parts[-1] == "":
                        next_parts = next_parts[:-1]

                    if len(next_parts) == 5 and next_parts[0] and next_parts[0] not in ("タスクNO", "---"):
                        break

                # Check for 【実施結果】 in detail rows
                if "【実施結果】" in next_line:
                    found_results = True
                    # Check the next line after 【実施結果】
                    k = j + 1
                    if k < len(lines):
                        result_line = lines[k].strip()
                        if result_line.startswith("|"):
                            result_parts = [p.strip() for p in result_line.split("|")]
                            if len(result_parts) >= 2 and result_parts[0] == "":
                                result_parts = result_parts[1:]
                            if len(result_parts) >= 1 and result_parts[-1] == "":
                                result_parts = result_parts[:-1]

                            # If the line after 【実施結果】 is 【移行履歴】 or next task, results are empty
                            if len(result_parts) >= 2:
                                content_cell = result_parts[1] if len(result_parts) > 1 else ""
                                if "【移行履歴】" in content_cell:
                                    results_empty = True
                                elif len(result_parts) == 5 and result_parts[0] and result_parts[0] not in ("タスクNO", "---"):
                                    results_empty = True
                                else:
                                    results_empty = False
                    break

                # Stop at section boundary (H2/H3 heading)
                if next_line.startswith("## ") or next_line.startswith("### "):
                    break

                j += 1

            if found_results and results_empty:
                issues.append((i + 1, f"Task '{task_no}' has completion date but empty 【実施結果】"))

        i += 1

    return issues


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
        completion_issues = validate_task_completion(md_file)
        total_files += 1

        file_has_issues = False
        if mismatches:
            all_ok = False
            total_mismatches += len(mismatches)
            file_has_issues = True
            print(f"\n❌ {md_file}")
            for line_num, actual_nf, expected_nf in mismatches:
                print(
                    f"   Line {line_num}: pipe count mismatch "
                    f"(actual={actual_nf}, expected={expected_nf})"
                )

        if completion_issues:
            all_ok = False
            total_mismatches += len(completion_issues)
            if not file_has_issues:
                print(f"\n❌ {md_file}")
            for line_num, message in completion_issues:
                print(f"   Line {line_num}: {message}")

        if not file_has_issues and not completion_issues:
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
