/**
 * アプリケーション設定の読み書きを行うユーティリティ
 *
 * Rust 側 `config.rs` で定義された `AppSettings` と対応する。
 * 設定ファイルは `~/.config/book2pdf/settings.json`（snake_case）で保存される。
 */
import { invoke } from "@tauri-apps/api/core";

/**
 * アプリケーション設定の型
 *
 * Rust 側 `AppSettings` とフィールド名を一致させるため snake_case を使用する。
 * これにより、ユーザーが `~/.config/book2pdf/settings.json` を直接編集しやすくなる。
 */
export interface AppSettings {
  /** backend API のベース URL（例: http://localhost:8000） */
  backend_url: string;
  /** ocr-worker のベース URL（例: http://localhost:8001） */
  ocr_worker_url: string;
  /** frontend の URL（例: http://localhost:3000） */
  frontend_url: string;
  /** 1ページあたりの OCR タイムアウト（秒） */
  page_timeout_sec: number;
  /** ジョブ状態ポーリング間隔（秒） */
  polling_interval_sec: number;
}

/**
 * 設定をファイルから読み込む
 *
 * @returns 現在保存されている設定。ファイルが存在しない場合はデフォルト値
 */
export async function loadSettings(): Promise<AppSettings> {
  return invoke<AppSettings>("load_settings");
}

/**
 * 設定をファイルに保存する
 *
 * @param settings - 保存する設定値
 */
export async function saveSettings(settings: AppSettings): Promise<void> {
  return invoke<void>("save_settings", { settings });
}
