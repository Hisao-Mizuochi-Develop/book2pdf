#!/bin/zsh
# 003007: 追加前処理効果検証の OCR フルフロー自動実行スクリプト（未実行分）
# 各パターンの ZIP を backend API にアップロードし、OCR・PDF 生成まで実行する

set -uo pipefail

cd /Users/hisao/Documents/work4/sakura/book2pdf

RESULTS_DIR="ocr-results-003007"
mkdir -p "$RESULTS_DIR"

# 比較パターン定義（パターン名=ZIPファイル名）
declare -A PATTERN_ZIPS=(
  [baseline_2x]="benchmark-ocr-003007-baseline-2x.zip"
  [4x_upscale]="benchmark-ocr-003007-4x-upscale.zip"
  [4x_upscale_sharpen]="benchmark-ocr-003007-4x-upscale-sharpen.zip"
  [local_binarization]="benchmark-ocr-003007-local-binarization.zip"
  [local_binarization_sharpen]="benchmark-ocr-003007-local-binarization-sharpen.zip"
  [contrast_strong_4x]="benchmark-ocr-003007-contrast-strong-4x.zip"
)

for pattern in "${(@k)PATTERN_ZIPS}"; do
  zip_file="${PATTERN_ZIPS[$pattern]}"
  pattern_dir="$RESULTS_DIR/$pattern"
  mkdir -p "$pattern_dir/pdfs"

  echo "========================================"
  echo "Pattern: $pattern"
  echo "ZIP: $zip_file"
  echo "========================================"

  # 1. ジョブ作成
  job_response=$(curl -s -X POST http://localhost:8000/api/jobs/)
  job_id=$(echo "$job_response" | jq -r '.job_id')
  if [[ -z "$job_id" || "$job_id" == "null" ]]; then
    echo "ERROR: Failed to create job. response: $job_response"
    continue
  fi
  echo "Job ID: $job_id"
  echo "$job_id" > "$pattern_dir/job_id.txt"

  # 2. ZIP アップロード
  echo "Uploading..."
  upload_response=$(curl -s -X POST \
    -F "file=@$zip_file;type=application/zip" \
    http://localhost:8000/api/jobs/$job_id/upload)
  echo "$upload_response" | jq . > "$pattern_dir/job_info.json"

  # 3. OCR 実行（タイムアウト長め）。レスポンスはそのまま保存
  echo "Running OCR..."
  ocr_response=$(curl -s --max-time 3600 \
    -X POST http://localhost:8000/api/jobs/$job_id/ocr)
  echo "$ocr_response" | jq . > "$pattern_dir/ocr_response.json" || true

  # 4. ジョブ状態を polling して完了確認
  echo "Polling job status..."
  for i in {1..360}; do
    job_status=$(curl -s http://localhost:8000/api/jobs/$job_id | jq -r '.status')
    echo "  status: $job_status"
    if [[ "$job_status" == "COMPLETED" || "$job_status" == "FAILED" ]]; then
      break
    fi
    sleep 10
  done

  # 5. PDF ダウンロード
  echo "Downloading PDF..."
  curl -s -o "$pattern_dir/pdfs/$job_id.pdf" \
    http://localhost:8000/api/jobs/$job_id/pdf

  # 6. OCR 出力ディレクトリをコピー（extracted ボリューム内の output_YYYYMMDDhhmmss ディレクトリ）
  echo "Copying OCR output..."
  output_dir=$(docker compose exec backend ls -d /data/extracted/$job_id/output_* 2>/dev/null | head -n 1 | tr -d '\r')
  if [[ -n "$output_dir" && "$output_dir" == /data/extracted/$job_id/output_* ]]; then
    output_basename=$(basename "$output_dir")
    docker compose cp "backend:$output_dir" "$pattern_dir/output_$output_basename"
  else
    echo "WARN: Could not find output directory for job $job_id"
  fi

  echo "Pattern $pattern done."
  echo
done

echo "All patterns completed."
