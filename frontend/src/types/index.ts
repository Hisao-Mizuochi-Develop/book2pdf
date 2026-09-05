/**
 * book2pdf フロントエンドで使用する共通型定義です。
 *
 * 主に以下の型を提供します:
 * - バックエンド API のレスポンス型
 * - Server-Sent Events による進捗通知のイベント型
 * - コンポーネント間で受け渡しする props 型
 */

/** OCR ジョブの状態を表す文字列リテラル型です。 */
export type JobStatus =
  | "pending"
  | "uploaded"
  | "processing"
  | "completed"
  | "failed";

/** `POST /api/jobs/` のレスポンス型です。 */
export interface JobCreateResponse {
  job_id: string;
  status: JobStatus;
}

/** `GET /api/jobs/{job_id}/` のレスポンス型です。 */
export interface JobResponse {
  job_id: string;
  status: JobStatus;
  message?: string;
  files?: string[];
  text?: string;
}

/** `POST /api/jobs/{job_id}/upload/` のレスポンス型です。 */
export interface JobUploadResponse {
  job_id: string;
  status: JobStatus;
  files?: string[];
}

/** `POST /api/jobs/{job_id}/ocr/` のレスポンス型です。 */
export interface JobOcrResponse {
  job_id: string;
  status: JobStatus;
  text?: string;
  message?: string;
}

/** `GET /api/jobs/{job_id}/events/` の SSE 進捙イベント型です。 */
export interface ProgressEvent {
  job_id: string;
  status: JobStatus;
  progress: number;
  current_page: number;
  total_pages: number;
  message?: string;
  timestamp?: string;
}

/** UploadForm コンポーネントの props 型です。 */
export interface UploadFormProps {
  /** 現在選択されているファイル。未選択時は null です。 */
  file: File | null;
  /** 処理中フラグ。true の間は入力・ボタンを無効化します。 */
  isLoading: boolean;
  /** ファイル選択時のコールバックです。 */
  onFileChange: (file: File | null) => void;
  /** アップロード実行時のコールバックです。 */
  onSubmit: () => void;
  /** 表示するエラーメッセージ。空文字列の場合は表示しません。 */
  error: string;
}

/** JobInfoPanel コンポーネントの props 型です。 */
export interface JobInfoPanelProps {
  /** 表示対象のジョブ ID。null の場合は何も描画しません。 */
  jobId: string | null;
  /** アップロードされた画像ファイル名の一覧です。 */
  files: string[];
}

/** ProgressPanel コンポーネントの props 型です。 */
export interface ProgressPanelProps {
  /** 最新の進捗イベントです。 */
  latest: ProgressEvent | null;
  /** 時系列順の進捗メッセージログです。 */
  log: string[];
}

/** ResultPanel コンポーネントの props 型です。 */
export interface ResultPanelProps {
  /** 表示する OCR 結果文字列。空文字列の場合は何も描画しません。 */
  result: string;
}

/** DownloadButton コンポーネントの props 型です。 */
export interface DownloadButtonProps {
  /** ダウンロード対象のジョブ ID。null の場合は何も描画しません。 */
  jobId: string | null;
  /** ボタン押下時のコールバックです。 */
  onDownload: () => void;
}
