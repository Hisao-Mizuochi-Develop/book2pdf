#!/usr/bin/env python3
"""
work_log.md のタスク番号を実施順に振り直す。
003005 → 003001, 003001 → 003002, 003002 → 003003, 003003 → 003004
"""

import re

filepath = "ocr-worker/docs/work_log.md"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 置換ルール（逆順で実行して衝突を回避）
# Step 1: 003003 → 003004（config.yml調整）
replacements_step1 = [
    (r"タスク003003：", "タスク003004："),
    (r"タスク 003003 で", "タスク 003004 で"),
    (r"003003 の sharpen_light_upscale_2x", "003004 の sharpen_light_upscale_2x"),
    (r"003003 と同一", "003004 と同一"),
    (r"003003 が完了", "003004 が完了"),
    (r"003003/>", "003004/>"),
    (r"ocr-results-003003", "ocr-results-tmp003004"),
    (r"preprocess-comparison-report-003003\.md", "preprocess-comparison-report-tmp003004.md"),
]

for pattern, repl in replacements_step1:
    content = re.sub(pattern, repl, content)

# Step 2: 003002 → 003003（前処理効果検証）
replacements_step2 = [
    (r"タスク003002：", "タスク003003："),
    (r"タスク 003002 で", "タスク 003003 で"),
    (r"003002 で特定した", "003003 で特定した"),
    (r"003002 の結果", "003003 の結果"),
    (r"003002 と同一条件", "003003 と同一条件"),
    (r"benchmark-ocr-003002-sharpen\.zip", "benchmark-ocr-003003-sharpen.zip"),
    (r"benchmark-ocr-003002-sharpen-upscale\.zip", "benchmark-ocr-003003-sharpen-upscale.zip"),
    (r"benchmark-ocr-003002-contrast-gamma\.zip", "benchmark-ocr-003003-contrast-gamma.zip"),
    (r"benchmark-ocr-003002-contrast-gamma-sharpen\.zip", "benchmark-ocr-003003-contrast-gamma-sharpen.zip"),
    (r"ocr-results-003002", "ocr-results-003003"),
    (r"ocr-accuracy-report-003002\.md", "ocr-accuracy-report-003003.md"),
    (r"preprocess-comparison-report\.md", "preprocess-comparison-report-003003.md"),
]

for pattern, repl in replacements_step2:
    content = re.sub(pattern, repl, content)

# Step 3: 003001 → 003002（精度再測定）
replacements_step3 = [
    (r"タスク003001：", "タスク003002："),
    (r"タスク 003001 で", "タスク 003002 で"),
    (r"benchmark-ocr-003001\.zip", "benchmark-ocr-003002.zip"),
    (r"ocr-results-003001", "ocr-results-003002"),
    (r"ocr-accuracy-report-003001\.md", "ocr-accuracy-report-003002.md"),
]

for pattern, repl in replacements_step3:
    content = re.sub(pattern, repl, content)

# Step 4: 003005 → 003001（500エラー修正）
replacements_step4 = [
    (r"タスク003005：", "タスク003001："),
    (r"タスク 003005 で", "タスク 003001 で"),
]

for pattern, repl in replacements_step4:
    content = re.sub(pattern, repl, content)

# Step 5: 一時置換を確定
replacements_step5 = [
    (r"ocr-results-tmp003004", "ocr-results-003004"),
    (r"preprocess-comparison-report-tmp003004\.md", "preprocess-comparison-report-003004.md"),
]

for pattern, repl in replacements_step5:
    content = re.sub(pattern, repl, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

# 確認出力
import re as re_mod
matches = re_mod.findall(r'タスク00300[1-4]：', content)
print("Updated task headers found:", sorted(set(matches)))
print("File updated successfully.")
