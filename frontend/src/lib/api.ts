// FastAPI バックエンドとの通信を行うクライアント関数群です

// ブラウザからアクセスする backend API のベース URL です
// コンテナ外の開発時は環境変数が未定義の場合 localhost:8000 を使用します
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// API 呼び出しのデフォルトタイムアウト（ミリ秒）です
const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * fetch にタイムアウトを付与して実行します
 * @param input リクエスト URL
 * @param init fetch オプション
 * @returns Response
 */
async function fetchWithTimeout(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * 新しい OCR ジョブを作成します
 * @returns 作成されたジョブの ID
 */
export async function createJob(): Promise<string> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/jobs/`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`ジョブの作成に失敗しました: ${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  return data.job_id as string;
}

/**
 * ZIP ファイルを指定したジョブにアップロードします
 * @param jobId ジョブ ID
 * @param file アップロードする ZIP ファイル
 * @returns 画像ファイル名の一覧
 */
export async function uploadZip(jobId: string, file: File): Promise<string[]> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetchWithTimeout(`${API_BASE_URL}/api/jobs/${jobId}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`ZIP アップロードに失敗しました: ${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  return data.files as string[];
}

/**
 * 指定したジョブの OCR 処理を開始します
 * @param jobId ジョブ ID
 * @returns OCR 結果
 */
export async function runOcr(jobId: string): Promise<unknown> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/jobs/${jobId}/ocr`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`OCR 実行に失敗しました: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

/**
 * 指定したジョブの進捗を SSE で購読します
 * @param jobId ジョブ ID
 * @param onMessage 進捗メッセージを受け取るコールバック
 * @param onError エラー発生時のコールバック
 * @param onComplete 完了時のコールバック
 * @returns EventSource インスタンス
 */
export function subscribeJobProgress(
  jobId: string,
  onMessage: (message: string) => void,
  onError: (error: Event) => void,
  onComplete: () => void
): EventSource {
  const eventSource = new EventSource(`${API_BASE_URL}/api/jobs/${jobId}/events`);

  eventSource.onmessage = (event) => {
    const data = event.data;
    if (data === "[DONE]") {
      onComplete();
      eventSource.close();
      return;
    }
    onMessage(data);
  };

  eventSource.onerror = (error) => {
    onError(error);
    eventSource.close();
  };

  return eventSource;
}

/**
 * 指定したジョブの生成済み PDF をダウンロードします
 * @param jobId ジョブ ID
 * @returns ブラウザで PDF を開くための URL
 */
export function getPdfDownloadUrl(jobId: string): string {
  return `${API_BASE_URL}/api/jobs/${jobId}/pdf`;
}

/**
 * 指定したジョブの生成済み PDF をファイルとしてダウンロードします
 * @param jobId ジョブ ID
 * @param filename 保存するファイル名（省略時は {jobId}.pdf）
 */
export async function downloadPdf(jobId: string, filename?: string): Promise<void> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/jobs/${jobId}/pdf`);
  if (!response.ok) {
    throw new Error(`PDF のダウンロードに失敗しました: ${response.status} ${response.statusText}`);
  }

  // レスポンスを Blob として取得します
  const blob = await response.blob();

  // Blob から一時的なオブジェクト URL を作成します
  const url = window.URL.createObjectURL(blob);

  // ダウンロード用のリンク要素を作成します
  const link = document.createElement("a");
  link.href = url;
  link.download = filename || `${jobId}.pdf`;

  // リンクをクリックしてダウンロードを開始します
  document.body.appendChild(link);
  link.click();

  // リンク要素とオブジェクト URL を解放します
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
