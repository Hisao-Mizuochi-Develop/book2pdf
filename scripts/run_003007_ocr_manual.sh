#!/bin/zsh
# 003007: 追加前処理効果検証の OCR フルフロー手動実行用スクリプト
# 使い方: ./scripts/run_003007_ocr_manual.sh <pattern_name> <zip_file>
# 例: ./scripts/run_003007_ocr_manual.sh baseline_2x benchmark-ocr-003007-baseline-2x.zip

set -uo pipefail

cd /Users/hisao/Documents/work4/sakura/book2pdf

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <pattern_name> <zip_file>"
  exit 1
fi

pattern="$1"
zip_file="$2"
RESULTS_DIR="ocr-results-003007"
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
  exit 1
fi
echo "Job ID: $job_id"
echo "$job_id" > "$pattern_dir/job_id.txt"

# 2. ZIP アップロード
echo "Uploading..."
upload_response=$(curl -s -X POST \
  -F "file=@$zip_file;type=application/zip" \
  http://localhost:8000/api/jobs/$job_id/upload)
echo "$upload_response" | jq . > "$pattern_dir/job_info.json"

# 3. OCR 実行（タイムアウト長め）
echo "Running OCR..."
curl -s --max-time 3600 \
  -X POST http://localhost:8000/api/jobs/$job_id/ocr > "$pattern_dir/ocr_response.json"
echo "OCR request returned."

# 4. ジョブ状態を polling して完了確認
echo "Polling job status..."
for i in {1..360}; do
  job_status=$(curl -s http://localhost:8000/api/jobs/$job_id | jq -r '.status')
  echo "  status: $job_status"
  if [[ "$job_status" == "COMPLETED" ]]; then
    break
  fi
  if [[ "$job_status" == "FAILED" ]]; then
    echo "Job failed."
    exit 1
  fi
  sleep 10
done

# 5. PDF ダウンロード
echo "Downloading PDF..."
curl -s -o "$pattern_dir/pdfs/$job_id.pdf" \
  http://localhost:8000/api/jobs/$job_id/pdf

# 6. OCR 出力ディレクトリをコピー
echo "Copying OCR output..."
output_dir=$(docker compose exec backend sh -c "ls -d /data/extracted/$job_id/output_* 2>/dev/null" | head -n 1 | tr -d '\r')
if [[ -n "$output_dir" ]]; then
  output_basename=$(basename "$output_dir")
  docker compose cp "backend:$output_dir" "$pattern_dir/$output_basename"
else
  echo "WARN: Could not find output directory for job $job_id"
fi

echo "Pattern $pattern done."
