// FastAPI バックエンドとの通信を行うクライアント関数群です

import type {
  JobCreateResponse,
  JobUploadResponse,
  JobResponse,
} from "@/types";

// ブラウザからアクセスする backend API のベース URL です
// コンテナ外の開発時は環境変数が未定義の場合 localhost:8000 を使用します
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// API 呼び出しのデフォルトタイムアウト（ミリ秒）です
const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * 通信デバッグログを有効にするかどうかです。
 * 本番ビルドでは不要なログを抑制するため、NEXT_PUBLIC_DEBUG_API が truthy な場合のみ詳細ログを出力します。
 * ただし SSE のエラーや接続状態は常に出力し、トラブルシューティングを支援します。
 */
const _DEBUG_API = Boolean(process.env.NEXT_PUBLIC_DEBUG_API);

/**
 * リクエスト/レスポンスのデバッグログを出力します
 * @param label ログラベル
 * @param detail ログ内容
 */
function _logApi(label: string, detail: unknown): void {
  console.log(`[API-DEBUG] ${label}`, detail);
}

/**
 * fetch にタイムアウトを付与して実行します
 * @param input リクエスト URL
 * @param init fetch オプション
 * @param timeoutMs タイムアウト（ミリ秒）。0 以下を指定するとタイムアウトしません。
 * @returns Response
 */
async function fetchWithTimeout(
  input: RequestInfo | URL,
  init?: RequestInit,
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<Response> {
  const url = typeof input === "string" ? input : input.toString();
  if (_DEBUG_API) {
    _logApi("REQ", {
      url,
      method: init?.method ?? "GET",
      // FormData などは直接ログに出さず、型のみ表示します
      bodyType: init?.body ? (init.body instanceof FormData ? "FormData" : typeof init.body) : undefined,
    });
  }

  const controller = new AbortController();
  const timeoutId =
    timeoutMs > 0
      ? setTimeout(() => controller.abort(), timeoutMs)
      : undefined;
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    if (_DEBUG_API) {
      _logApi("RES", {
        url,
        status: response.status,
        statusText: response.statusText,
        contentType: response.headers.get("content-type"),
      });
    }
    return response;
  } finally {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId);
    }
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
 * 指定したジョブの OCR 処理を非同期で開始します。
 * バックエンドは 202 Accepted を返し、OCR はバックグラウンドで実行されます。
 * @param jobId ジョブ ID
 */
export async function runOcr(jobId: string): Promise<void> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/jobs/${jobId}/ocr`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`OCR 実行に失敗しました: ${response.status} ${response.statusText}`);
  }
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

  // [DONE] を受信済みかどうかを追跡します。
  // サーバーが正常にストリームを終了すると、ブラウザ側で onerror が発火する場合がありますが、
  // 既に [DONE] を受信済みの場合はエラーとして扱いません。
  let doneReceived = false;

  eventSource.onopen = () => {
    console.log(`[SSE-DEBUG] OPEN job_id=${jobId}`);
  };

  eventSource.onmessage = (event) => {
    const data = event.data;
    console.log(`[SSE-DEBUG] MSG job_id=${jobId} data=`, data);
    if (data === "[DONE]") {
      doneReceived = true;
      onComplete();
      eventSource.close();
      return;
    }
    onMessage(data);
  };

  eventSource.onerror = (error) => {
    console.log(`[SSE-DEBUG] ERROR job_id=${jobId}`, error);
    // [DONE] 受信後の切断は正常終了として扱います
    if (!doneReceived) {
      onError(error);
    }
    eventSource.close();
  };

  return eventSource;
}

/**
 * ポーリング間隔（ミリ秒）です。
 * Next.js の公開環境変数 `NEXT_PUBLIC_POLL_INTERVAL_MS` から取得します。
 * 未設定または無効な値の場合は 1000ms をデフォルトとします。
 */
const POLL_INTERVAL_MS = (() => {
  const envValue = process.env.NEXT_PUBLIC_POLL_INTERVAL_MS;
  if (!envValue) {
    return 1_000;
  }
  const parsed = Number.parseInt(envValue, 10);
  return Number.isNaN(parsed) || parsed <= 0 ? 1_000 : parsed;
})();

/**
 * 指定したジョブの進捗をポーリングで監視します。
 * SSE が利用できない環境（プロキシ環境など）でのフォールバックとして使用します。
 * @param jobId ジョブ ID
 * @param onMessage 進捗メッセージを受け取るコールバック
 * @param onError エラー発生時のコールバック
 * @param onComplete 完了時のコールバック
 * @returns ポーリングを停止するための関数
 */
export interface PollJobProgressOptions {
  /** ポーリング間隔（ミリ秒）。デフォルトは 1000ms です。 */
  interval?: number;
}

export function pollJobProgress(
  jobId: string,
  onMessage: (message: string) => void,
  onError: (error: Error) => void,
  onComplete: () => void,
  options?: PollJobProgressOptions
): () => void {
  const interval = options?.interval ?? POLL_INTERVAL_MS;
  let active = true;

  const tick = async () => {
    if (!active) return;

    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/api/jobs/${jobId}`);
      if (!response.ok) {
        throw new Error(`進捗の取得に失敗しました: ${response.status} ${response.statusText}`);
      }

      const data = (await response.json()) as JobResponse;

      // backend/frontend/ocr-worker 間で UTC の秒精度 ISO 8601 を統一します (SY002003)
      const fallbackTimestamp = new Date().toISOString().split(".")[0] + "Z";

      // 進捗情報を SSE と同じ形式（JSON）に変換してコールバックに渡します
      const progressEvent = {
        job_id: jobId,
        status: data.status,
        progress: data.progress ?? 0,
        current_page: data.current_page ?? 0,
        total_pages: data.total_pages ?? 0,
        message: data.message ?? "",
        timestamp: data.timestamp ?? fallbackTimestamp,
        ocrPages: data.ocrPages ?? [],
      };
      onMessage(JSON.stringify(progressEvent));

      // ジョブが完了または失敗した場合はポーリングを停止します
      if (data.status === "completed" || data.status === "failed") {
        active = false;
        onComplete();
        return;
      }
    } catch (err) {
      if (!active) return;
      onError(err instanceof Error ? err : new Error(String(err)));
    }

    // 次のポーリングをスケジュールします
    if (active) {
      setTimeout(tick, interval);
    }
  };

  // 初回のポーリングを開始します
  tick();

  return () => {
    active = false;
  };
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
 * 指定したジョブの OCR 処理をキャンセルし、関連リソースをクリーンアップします
 * SY002002: ユーザーが進行中のジョブをキャンセルするために使用します。
 * @param jobId ジョブ ID
 */
export async function cancelJob(jobId: string): Promise<void> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/jobs/${jobId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`ジョブのキャンセルに失敗しました: ${response.status} ${response.statusText}`);
  }
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
    await response.body.pipeTo(writable, { preventClose: true });
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
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/jobs/${jobId}/pdf`,
      undefined,
      0
    );
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

    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/jobs/${jobId}/pdf`,
      undefined,
      0
    );
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
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/jobs/${jobId}/pdf`,
    undefined,
    0
  );
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
