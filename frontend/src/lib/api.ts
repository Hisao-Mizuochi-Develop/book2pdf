// FastAPI バックエンドとの通信を行うクライアント関数群です

import type {
  JobCreateResponse,
  JobUploadResponse,
} from "@/types";

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
  const data = (await response.json()) as JobCreateResponse;
  return data.job_id;
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
  const data = (await response.json()) as JobUploadResponse;
  return data.files ?? [];
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
 * File System Access API の型定義です
 * TypeScript の標準 lib に含まれていない可能性があるため、最小限の型を定義します
 */
interface FileSystemWritableFileStream extends WritableStream {
  write(data: Blob | BufferSource | string): Promise<void>;
  close(): Promise<void>;
}

interface SaveFilePickerOptions {
  suggestedName?: string;
  types?: Array<{
    description?: string;
    accept: Record<string, string[]>;
  }>;
}

export interface FileSystemFileHandle {
  createWritable(): Promise<FileSystemWritableFileStream>;
}

declare global {
  interface Window {
    showSaveFilePicker?: (options?: SaveFilePickerOptions) => Promise<FileSystemFileHandle>;
  }
}

/**
 * レスポンスボディを WritableStream に直接転送します
 * @param response 転送元の Response
 * @param writable 転送先の WritableStream
 */
async function streamToWritable(
  response: Response,
  writable: FileSystemWritableFileStream
): Promise<void> {
  if (response.body) {
    await response.body.pipeTo(writable);
  } else {
    await writable.write(await response.blob());
  }
}

/**
 * ブラウザ標準の「保存先を指定するダイアログ」を使用して PDF を保存します。
 * File System Access API に対応していないブラウザでは、従来の `<a download>` 方式にフォールバックします。
 *
 * showSaveFilePicker はユーザージェスチャ（クリック）の文脈内で同期的に呼ぶ必要があるため、
 * この関数内部で呼び出すと呼び出し元の async ラッパーによってジェスチャが失効する場合があります。
 * そのため本関数では fileHandle を受け取る方式を推奨し、showSaveFilePicker の呼び出しは
 * UI 層の同期 onClick ハンドラで行ってください。
 *
 * @param jobId ジョブ ID
 * @param filename 保存するファイル名（省略時は {jobId}.pdf）
 * @param fileHandle UI 層で事前に取得した FileSystemFileHandle（推奨）
 */
export async function downloadPdf(
  jobId: string,
  filename?: string,
  fileHandle?: FileSystemFileHandle
): Promise<void> {
  const suggestedName = filename || `${jobId}.pdf`;

  // fileHandle が提供されている場合は、ピッカーをスキップして直接ストリーミング書き込みします。
  // これによりクリックのユーザージェスチャ文脈を保持し、ダイアログが確実に表示されます。
  if (fileHandle) {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/jobs/${jobId}/pdf`);
    if (!response.ok) {
      throw new Error(`PDF のダウンロードに失敗しました: ${response.status} ${response.statusText}`);
    }

    const writable = await fileHandle.createWritable();
    try {
      await streamToWritable(response, writable);
    } finally {
      await writable.close();
    }
    return;
  }

  // File System Access API が利用可能な場合は、保存先ダイアログを表示してから書き込みます。
  // ただし、showSaveFilePicker を本関数内で呼ぶ場合は呼び出し元が同期イベントハンドラである必要があります。
  if (typeof window.showSaveFilePicker === "function") {
    let handle: FileSystemFileHandle;
    try {
      handle = await window.showSaveFilePicker({
        suggestedName,
        types: [
          {
            description: "PDF ファイル",
            accept: { "application/pdf": [".pdf"] },
          },
        ],
      });
    } catch (error) {
      // ユーザーがダイアログをキャンセルした場合は何もせず終了します
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      throw error;
    }

    const response = await fetchWithTimeout(`${API_BASE_URL}/api/jobs/${jobId}/pdf`);
    if (!response.ok) {
      throw new Error(`PDF のダウンロードに失敗しました: ${response.status} ${response.statusText}`);
    }

    const writable = await handle.createWritable();
    try {
      await streamToWritable(response, writable);
    } finally {
      await writable.close();
    }
    return;
  }

  // フォールバック: Blob URL + <a download> 方式
  // （File System Access API に対応していないブラウザ用）
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/jobs/${jobId}/pdf`);
  if (!response.ok) {
    throw new Error(`PDF のダウンロードに失敗しました: ${response.status} ${response.statusText}`);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = suggestedName;

  document.body.appendChild(link);
  link.click();

  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
