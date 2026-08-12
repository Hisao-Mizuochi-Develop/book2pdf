#!/usr/bin/env bash
# book2pdf Web OCR/PDF システムの性能計測スクリプトです
#
# 性能テスト仕様:
#   - 入力: sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/001.png 〜 092.png
#   - 入力 ZIP: /tmp/book2pdf-benchmark/benchmark-input.zip
#   - 計測対象:
#       1. Docker Compose 起動時間
#       2. ジョブ作成時間
#       3. ZIP アップロード時間
#       4. OCR 全体時間
#       5. 1 ページごとの OCR 処理時間（ocr-worker DEBUG ログから抽出）
#       6. 1 ページあたり平均 OCR 処理時間
#       7. PDF 生成時間（backend DEBUG ログから抽出）
#       8. PDF ダウンロード時間
#       9. 合計処理時間
#   - ログ取得元:
#       - backend DEBUG ログ: ZIP 解凍時間、PDF 生成時間
#       - ocr-worker DEBUG ログ: 1 ページごとの OCR 処理時間
#   - 出力:
#       - /tmp/book2pdf-benchmark/results.csv
#       - /tmp/book2pdf-benchmark/results.txt
#   - クリーンアップ:
#       - 入力 ZIP、展開画像、OCR 出力を削除
#   - 特記事項:
#       - ZIP 内の画像ファイル数を自動検出し、1 ページ〜任意ページ数に対応します
set -euo pipefail

# 作業ディレクトリをプロジェクトルートに固定します
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

# 性能計測用の一時ディレクトリです
BENCH_DIR="/tmp/book2pdf-benchmark"
mkdir -p "${BENCH_DIR}"

# サンプル画像の配置ディレクトリです
SAMPLE_DIR="sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed"

# 入力 ZIP ファイルのパスです
INPUT_ZIP="${BENCH_DIR}/benchmark-input.zip"

# 結果ファイルのパスです
RESULT_TXT="${BENCH_DIR}/results.txt"
RESULT_CSV="${BENCH_DIR}/results.csv"

# OCR リクエストのタイムアウト（秒）です（環境変数 OCR_TIMEOUT で上書き可能）
# 10 ページ OCR には 15〜20 分かかるため、デフォルトを 1800 秒（30 分）に設定します
OCR_TIMEOUT=${OCR_TIMEOUT:-1800}

# ステータスポーリングの間隔（秒）です（環境変数 POLL_INTERVAL で上書き可能）
POLL_INTERVAL=${POLL_INTERVAL:-5}

# ステータスポーリングの最大回数です（環境変数 MAX_POLL で上書き可能）
MAX_POLL=${MAX_POLL:-120}

# jq が利用可能か確認します
if ! command -v jq >/dev/null 2>&1; then
  echo "エラー: jq がインストールされていません" >&2
  exit 1
fi

# ログ出力関数です
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${RESULT_TXT}"
}

# 現在時刻を秒単位で取得する関数です
# macOS / Linux 両対応のため python3 を使用します
now_seconds() {
  python3 -c "import time; print(time.time())"
}

# 経過時間を計算する関数です
# 引数: 開始時刻（秒）
# 戻り値: 経過秒数（小数点以下 3 桁）
elapsed() {
  local start=$1
  local end
  end=$(now_seconds)
  python3 -c "print(f'{${end} - ${start}:.3f}')"
}

# 結果ファイルを初期化します
> "${RESULT_TXT}"
> "${RESULT_CSV}"
echo "item,seconds" > "${RESULT_CSV}"

log "=== book2pdf OCR 性能計測開始 ==="
log "プロジェクトルート: ${PROJECT_ROOT}"
log "作業ディレクトリ: ${BENCH_DIR}"

# 1. 入力 ZIP ファイルを作成します
log "--- ZIP ファイル作成 ---"
if [ ! -f "${INPUT_ZIP}" ]; then
  file_list="${BENCH_DIR}/filelist.txt"
  > "${file_list}"
  # サンプル画像ディレクトリ内の画像ファイルをソートして取得します
  find "${PROJECT_ROOT}/${SAMPLE_DIR}" -maxdepth 1 -type f \
    \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.tif' -o -iname '*.tiff' -o -iname '*.jp2' -o -iname '*.bmp' \) |
    sort >> "${file_list}"
  # ZIP ファイルを作成します（-@ オプションでファイルリストから読み込みます）
  zip -q -j "${INPUT_ZIP}" -@ < "${file_list}"
  PAGE_COUNT=$(unzip -Z1 "${INPUT_ZIP}" 2>/dev/null | wc -l | tr -d ' ')
  log "作成: ${INPUT_ZIP} (${PAGE_COUNT} ページ)"
else
  PAGE_COUNT=$(unzip -Z1 "${INPUT_ZIP}" 2>/dev/null | wc -l | tr -d ' ')
  log "既存: ${INPUT_ZIP} (${PAGE_COUNT} ページ)"
fi

if [ "${PAGE_COUNT}" -eq 0 ]; then
  echo "エラー: 入力 ZIP に画像ファイルが含まれていません" >&2
  exit 1
fi

# 2. Docker Compose の起動時間を計測します
log "--- Docker Compose 起動 ---"
log "backend / ocr-worker の起動状態を確認します"

compose_start=$(now_seconds)
compose_already_running=false
backend_ok=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
ocr_ok=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "000")
if [ "${backend_ok}" = "200" ] && [ "${ocr_ok}" = "200" ]; then
  compose_already_running=true
  log "既存コンテナが実行中です"
else
  log "既存コンテナを停止・削除します"
  docker compose down >/dev/null 2>&1 || true
  log "Docker Compose 起動開始"
  docker compose up -d backend ocr-worker
fi

# backend / ocr-worker のヘルスチェックが通るまで待機します
log "backend / ocr-worker のヘルスチェック待機中..."
while true; do
  backend_ok=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
  ocr_ok=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "000")
  if [ "${backend_ok}" = "200" ] && [ "${ocr_ok}" = "200" ]; then
    break
  fi
  sleep 1
done
compose_elapsed=$(elapsed "${compose_start}")
log "Docker Compose 起動完了: ${compose_elapsed} 秒"

# 3. ジョブ作成時間を計測します
log "--- ジョブ作成 ---"
job_create_start=$(now_seconds)
job_response=$(curl -s -X POST http://localhost:8000/api/jobs/)
job_id=$(echo "${job_response}" | jq -r '.job_id')
job_create_elapsed=$(elapsed "${job_create_start}")
log "job_id=${job_id}"
log "ジョブ作成完了: ${job_create_elapsed} 秒"

# 4. ZIP アップロード時間を計測します
log "--- ZIP アップロード ---"
upload_start=$(now_seconds)
upload_response=$(curl -s -X POST \
  -F "file=@${INPUT_ZIP};type=application/zip" \
  "http://localhost:8000/api/jobs/${job_id}/upload")
upload_elapsed=$(elapsed "${upload_start}")
log "ZIP アップロード完了: ${upload_elapsed} 秒"

# 5. OCR 実行時間を計測します
log "--- OCR 実行 ---"
ocr_start=$(now_seconds)
ocr_response=$(curl -s --max-time "${OCR_TIMEOUT}" -X POST \
  "http://localhost:8000/api/jobs/${job_id}/ocr")
ocr_endpoint_elapsed=$(elapsed "${ocr_start}")
log "OCR エンドポイント応答完了: ${ocr_endpoint_elapsed} 秒"

# ジョブが completed または failed になるまでポーリングします
status=$(echo "${ocr_response}" | jq -r '.status')
if [ "${status}" != "completed" ] && [ "${status}" != "failed" ]; then
  poll_count=0
  while [ ${poll_count} -lt ${MAX_POLL} ]; do
    sleep ${POLL_INTERVAL}
    status=$(curl -s "http://localhost:8000/api/jobs/${job_id}" | jq -r '.status')
    if [ "${status}" = "completed" ] || [ "${status}" = "failed" ]; then
      break
    fi
    poll_count=$((poll_count + 1))
  done
fi
ocr_total_elapsed=$(python3 -c "print(f'{$(now_seconds) - ${ocr_start}:.3f}')")
log "OCR 処理完了（ジョブ状態: ${status}）: ${ocr_total_elapsed} 秒"

# 6. PDF ダウンロード時間を計測します
log "--- PDF ダウンロード ---"
pdf_download_start=$(now_seconds)
pdf_status=$(curl -s -o "${BENCH_DIR}/downloaded-${job_id}.pdf" -w "%{http_code}" \
  "http://localhost:8000/api/jobs/${job_id}/pdf" || echo "000")
pdf_download_elapsed=$(elapsed "${pdf_download_start}")
log "PDF ダウンロード HTTP ステータス: ${pdf_status}"
log "PDF ダウンロード完了: ${pdf_download_elapsed} 秒"

# 7. ログから各工程時間を取得します
log "--- ログから工程時間を抽出 ---"

# backend ログから ZIP 解凍時間と PDF 生成時間を抽出します
backend_logs=$(docker compose logs --no-log-prefix backend 2>/dev/null || true)
zip_extract_seconds=$(echo "${backend_logs}" | grep "ZIP 解凍が完了しました: job_id=${job_id}" | grep -oE 'elapsed=[0-9]+\.[0-9]+s' | tail -1 | sed 's/elapsed=//;s/s//' || echo "")
pdf_generate_seconds=$(echo "${backend_logs}" | grep "PDF 生成が完了しました: job_id=${job_id}" | grep -oE 'elapsed=[0-9]+\.[0-9]+s' | tail -1 | sed 's/elapsed=//;s/s//' || echo "")
log "ZIP 解凍時間（ログ）: ${zip_extract_seconds:-N/A} 秒"
log "PDF 生成時間（ログ）: ${pdf_generate_seconds:-N/A} 秒"

# ocr-worker ログから 1 ページごとの OCR 処理時間を抽出します
# OCR 処理開始時刻以降のログのみを対象とし、過去の実行分を含めないようにします
ocr_start_iso=$(python3 -c "import datetime; print(datetime.datetime.fromtimestamp(${ocr_start}).astimezone().isoformat())")
ocr_worker_logs=$(docker compose logs --no-log-prefix --since "${ocr_start_iso}" ocr-worker 2>/dev/null || true)
page_times=$(echo "${ocr_worker_logs}" | grep -oE '\[ndlocr_cli\] ページ処理完了: page=[0-9]+, img_path=.*, elapsed=[0-9]+\.[0-9]+s' | grep -oE 'elapsed=[0-9]+\.[0-9]+' | sed 's/elapsed=//')
page_count=0
page_total=0
while IFS= read -r pt; do
  if [ -n "${pt}" ]; then
    page_count=$((page_count + 1))
    page_total=$(python3 -c "print(${page_total} + ${pt})")
    log "ページ ${page_count} OCR 処理時間: ${pt} 秒"
  fi
done <<< "${page_times}"
if [ ${page_count} -gt 0 ]; then
  page_average=$(python3 -c "print(f'{${page_total} / ${page_count}:.3f}')")
else
  page_average=""
fi
log "1 ページあたり平均 OCR 処理時間: ${page_average:-N/A} 秒"

# 8. 結果を CSV とテキストに出力します
log "--- 結果出力 ---"
echo "Docker Compose 起動時間,${compose_elapsed}" >> "${RESULT_CSV}"
echo "ジョブ作成時間,${job_create_elapsed}" >> "${RESULT_CSV}"
echo "ZIP アップロード時間,${upload_elapsed}" >> "${RESULT_CSV}"
echo "OCR 全体時間,${ocr_total_elapsed}" >> "${RESULT_CSV}"
if [ -n "${page_average}" ]; then
  echo "1 ページあたり平均 OCR 処理時間,${page_average}" >> "${RESULT_CSV}"
fi
if [ -n "${zip_extract_seconds}" ]; then
  echo "ZIP 解凍時間（ログ）,${zip_extract_seconds}" >> "${RESULT_CSV}"
fi
if [ -n "${pdf_generate_seconds}" ]; then
  echo "PDF 生成時間（ログ）,${pdf_generate_seconds}" >> "${RESULT_CSV}"
fi
echo "PDF ダウンロード時間,${pdf_download_elapsed}" >> "${RESULT_CSV}"
total_all=$(python3 -c "print(f'{${compose_elapsed} + ${job_create_elapsed} + ${upload_elapsed} + ${ocr_total_elapsed} + ${pdf_download_elapsed}:.3f}')")
echo "合計処理時間,${total_all}" >> "${RESULT_CSV}"

# 9. クリーンアップします
log "--- クリーンアップ ---"
rm -f "${INPUT_ZIP}"
rm -f "${BENCH_DIR}/filelist.txt"
rm -f "${BENCH_DIR}/downloaded-${job_id}.pdf"
# コンテナ内の展開画像と OCR 出力を削除します
docker compose exec -T backend rm -rf "/data/extracted/${job_id}" "/data/ocr_output/${job_id}" 2>/dev/null || true
log "クリーンアップ完了"

# 10. 結果サマリーを出力します
log "=== 計測結果サマリー ==="
cat "${RESULT_CSV}" | tee -a "${RESULT_TXT}"

log "=== book2pdf OCR 性能計測終了 ==="
log "結果テキスト: ${RESULT_TXT}"
log "結果 CSV: ${RESULT_CSV}"
