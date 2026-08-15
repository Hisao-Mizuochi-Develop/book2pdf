#!/bin/bash
# 003005 再検証スクリプト（前処理 ON 状態で score_thr パターン A/B/C を backend API 経由で実行）
set -euo pipefail

ZIP_FILE="benchmark-ocr-003002.zip"
PATTERNS=("0.2" "0.3" "0.4" "0.5")
PATTERN_NAMES=("score-thr-0.2" "score-thr-0.3" "score-thr-0.4" "score-thr-0.5")

for i in "${!PATTERNS[@]}"; do
    score_thr="${PATTERNS[$i]}"
    name="${PATTERN_NAMES[$i]}"

    echo "===== $name (score_thr=$score_thr) ====="

    # config.yml を変更
    docker compose exec ocr-worker sed -i "s/score_thr: .*/score_thr: $score_thr/" /opt/ocr-worker/config.yml
    docker compose exec ocr-worker grep "score_thr" /opt/ocr-worker/config.yml

    # ocr-worker を再起動（config.yml 再読み込みのため）
    docker compose restart ocr-worker
    echo "Waiting for ocr-worker to be ready..."
    for attempt in $(seq 1 30); do
        if curl -s http://localhost:8001/health | grep -q '"status":"ok"'; then
            echo "ocr-worker is ready"
            break
        fi
        sleep 2
    done

    # backend API 経由で OCR 実行
    JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
    echo "Job ID: $JOB_ID"

    curl -s -X POST -F "file=@$ZIP_FILE;type=application/zip" "http://localhost:8000/api/jobs/$JOB_ID/upload" | jq .
    curl -s --max-time 1800 -X POST "http://localhost:8000/api/jobs/$JOB_ID/ocr" | jq .

    # completed になるまでポーリング
    echo "Waiting for job completion..."
    for attempt in $(seq 1 180); do
        status=$(curl -s "http://localhost:8000/api/jobs/$JOB_ID" | jq -r '.status')
        if [ "$status" = "completed" ]; then
            echo "Job completed"
            break
        elif [ "$status" = "failed" ]; then
            echo "Job failed"
            curl -s "http://localhost:8000/api/jobs/$JOB_ID" | jq .
            exit 1
        fi
        echo "  status: $status (attempt $attempt)"
        sleep 10
    done

    # 成果物取得
    mkdir -p "ocr-results-003005/${name}-preprocess-on/pdfs"
    docker compose cp "backend:/data/pdfs/${JOB_ID}.pdf" "ocr-results-003005/${name}-preprocess-on/pdfs/"

    # backend の JobResponse に output_dir は含まれていないため、backend ログや実際のディレクトリから取得する
    # ndlocr_cli の mkdir_with_duplication_check により output_YYYYMMDDhhmmss ディレクトリが作成される
    echo "Searching actual output dir for job ${JOB_ID}..."
    OUTPUT_DIR=$(docker compose exec backend bash -c "find /data/extracted/${JOB_ID} -maxdepth 1 -type d -name 'output_*' | sort | tail -n 1" | tr -d '\r')
    if [ -z "$OUTPUT_DIR" ]; then
        # フォールバック: output ディレクトリをそのまま使用
        OUTPUT_DIR="/data/extracted/${JOB_ID}/output"
    fi
    echo "Output dir: $OUTPUT_DIR"
    mkdir -p "ocr-results-003005/${name}-preprocess-on/output"
    docker compose cp "backend:${OUTPUT_DIR}/" "ocr-results-003005/${name}-preprocess-on/output/"

    echo "$JOB_ID" > "ocr-results-003005/${name}-preprocess-on/job_id.txt"
    curl -s "http://localhost:8000/api/jobs/$JOB_ID" | jq . > "ocr-results-003005/${name}-preprocess-on/job_info.json"

    echo ""
done

echo "All patterns completed."
