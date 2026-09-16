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
  | "failed"
  | "cancelled";

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
  /** 最新の進捗イベントです。未受信時は null です。 */
  latest: ProgressEvent | null;
  /** 表示するエラーメッセージです。空文字列または undefined の場合は表示しません。 */
  error?: string;
  /** キャンセルボタンを表示するかどうかです。 */
  showCancel?: boolean;
  /** キャンセルボタン押下時のコールバックです。 */
  onCancel?: () => void;
}

/** DownloadButton コンポーネントの props 型です。 */
export interface DownloadButtonProps {
  /** ダウンロード対象のジョブ ID。null の場合は何も描画しません。 */
  jobId: string | null;
  /** ボタン押下時のコールバックです。 */
  onDownload: () => void;
}

/** ZIP アップロードフォームの状態を表す文字列リテラル型です。 */
export type ZipUploadStatus =
  | "idle"
  | "creating"
  | "uploading"
  | "uploaded"
  | "error";

/** デバッグ表示エリアで使用する ZIP アップロード時間情報です。 */
export interface UploadTimingInfo {
  /** アップロード開始時刻（ISO 8601）です。 */
  uploadStart: string;
  /** アップロード完了時刻（ISO 8601）です。 */
  uploadEnd: string;
  /** 経過時間（ミリ秒）です。 */
  elapsedMs: number;
}

/** デバッグ表示エリアで使用する位相タイミング情報です。 */
export interface PhaseTiming {
  /** 開始時刻（ISO 8601）。未開始時は null です。 */
  start: string | null;
  /** 完了時刻（ISO 8601）。未完了時は null です。 */
  end: string | null;
  /** 経過時間（ミリ秒）。未確定時は null です。 */
  elapsedMs: number | null;
}

/** デバッグ表示エリアで使用する OCR ページ毎のタイミング情報です。 */
export interface PageOcrTiming {
  /** ページの 0-based インデックスです。 */
  pageIndex: number;
  /** 画像ファイル名です。 */
  fileName: string;
  /** OCR 開始時刻（ISO 8601）です。 */
  start: string | null;
  /** OCR 完了時刻（ISO 8601）です。 */
  end: string | null;
  /** OCR 処理にかかった時間（ミリ秒）です。 */
  elapsedMs: number | null;
}

/** デバッグ表示エリアで表示するタイミング情報の集約型です。 */
export interface TimingDebugInfo {
  /** ZIP アップロード（画像展開含む）のタイミングです。 */
  zipUpload: PhaseTiming;
  /** 1 枚目画像 OCR 開始から最終画像 OCR 処理完了までの OCR 処理総時間です。 */
  ocrTotal: PhaseTiming;
  /** 各ページの OCR 処理タイミングです。 */
  ocrPages: PageOcrTiming[];
  /** PDF 生成のタイミングです。 */
  pdfGeneration: PhaseTiming;
  /** アップロード開始から PDF 生成完了までの全体タイミングです。 */
  overall: PhaseTiming;
}

/** ランタイム設定ファイルの構造です。 */
export interface DebugConfig {
  /** デバッグ表示エリアを表示するかどうかです。 */
  showDebugTimingPanel: boolean;
}

/** ZipUploadForm コンポーネントの props 型です。 */
export interface ZipUploadFormProps {
  /** アップロード完了時に呼び出されるコールバックです。 */
  onUploaded: (jobId: string, files: string[], timing?: UploadTimingInfo) => void;
}
