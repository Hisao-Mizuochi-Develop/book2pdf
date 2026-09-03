/**
 * プロファイル編集コンポーネント
 *
 * 【役割】
 * 選択中のプロファイルの詳細設定を表示・編集するパネル。
 * ページ送り待機時間、ウィンドウタイトル、プロセス名、トリミング設定などを
 * 入力フォームやトグルで編集できる。
 *
 * 【customProfiles との連携】
 * ビルトイン値とカスタム値を区別して表示する。
 * ユーザーが編集した値は customProfiles に保存され、
 * ビルトイン値との差分があるフィールドは視覚的に示す（将来的拡張）。
 *
 * 【編集項目】
 * - pageTurnKey: セレクト（right / left / space / arrow）
 * - pageWait: 数値入力（秒、0.1 刻み）
 * - cropInsets: コンテンツ領域トリミング（上/右/下/左 のピクセル入力）
 */

// UI ボタンコンポーネントを読み込み
// リセット・プレビュー等のアクションボタン
import { Button } from "@/components/ui/button";
// UI テキスト入力コンポーネントを読み込み
// 待機時間・トリミング値等の数値入力欄
import { Input } from "@/components/ui/input";
// UI ラベルコンポーネントを読み込み
// フォーム項目の見出しとして使用する
import { Label } from "@/components/ui/label";
// UI セレクト（ドロップダウン）コンポーネント群を読み込み
// pageTurnKey の選択肢（right/left/space/arrow）を表示する
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
// プロファイル状態管理ストア（Zustand）を読み込み
// 現在選択中のプロファイル・カスタム設定の読み書きに使用する
import { useProfileStore } from "@/store/profileStore";
// Tauri の Rust コマンド呼び出し関数を読み込み
// invoke("command_name") で Rust 側の #[tauri::command] 関数を実行する
import { invoke } from "@tauri-apps/api/core";
// アイコンライブラリ（lucide-react）からアイコンを読み込み
// RotateCcw（リセット）, Camera, ZoomIn, ZoomOut, Minus, Plus アイコン
import { RotateCcw, Camera, ZoomIn, ZoomOut, Minus, Plus } from "lucide-react";
// React のフック（状態管理・副作用処理・派生値計算）を読み込み
// useState: 編集中の値, useMemo: 派生値, useEffect: 初期化時のプロファイル読み込み
import { useState, useMemo, useEffect } from "react";


/**
 * プロファイル編集コンポーネント
 *
 * @returns プロファイル詳細設定編集フォーム
 */
export function ProfileEditor() {
  // Zustand ストアから必要な状態・アクションを取得
  const selectedProfileKey = useProfileStore((state) => state.selectedProfileKey);
  const updateCustomProfile = useProfileStore((state) => state.updateCustomProfile);
  const resetProfile = useProfileStore((state) => state.resetProfile);
  const builtinProfiles = useProfileStore((state) => state.builtinProfiles);
  const customProfiles = useProfileStore((state) => state.customProfiles);

  // 現在選択中の実効プロファイル（ビルトイン + カスタム上書きマージ済み）
  // useMemo で派生計算することで、参照の安定性を保ち、
  // React の無限再レンダーを防止する。
  const profile = useMemo(() => {
    const key = selectedProfileKey;
    if (!key) return null;
    const builtin = builtinProfiles.find((p) => p.key === key);
    if (!builtin) return null;
    const custom = customProfiles[key];
    return custom ? { ...builtin, ...custom } : builtin;
  }, [builtinProfiles, customProfiles, selectedProfileKey]);

  // カスタム値が適用されているかどうか
  const hasCustom = selectedProfileKey ? selectedProfileKey in customProfiles : false;

  // キャプチャテスト用の state
  const [testImage, setTestImage] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  // ズーム機能（0.5x〜2.0x、0.1 刻み）
  const [zoom, setZoom] = useState(1.0);
  const MIN_ZOOM = 0.5;
  const MAX_ZOOM = 2.0;
  const ZOOM_STEP = 0.1;

  function handleZoomOut() {
    setZoom((prev) => Math.max(MIN_ZOOM, Math.round((prev - ZOOM_STEP) * 10) / 10));
  }

  function handleZoomIn() {
    setZoom((prev) => Math.min(MAX_ZOOM, Math.round((prev + ZOOM_STEP) * 10) / 10));
  }

  // ── トリミング入力用ローカル state ─────────────────────────
  /** ローカル入力値（文字列）— 入力中の一時的な値を保持 */
  const [cropInputs, setCropInputs] = useState({
    top: String(profile?.cropInsets?.top ?? 0),
    right: String(profile?.cropInsets?.right ?? 0),
    bottom: String(profile?.cropInsets?.bottom ?? 0),
    left: String(profile?.cropInsets?.left ?? 0),
  });

  /**
   * profile.cropInsets が外部から変更された場合、ローカル入力値も同期する。
   *（リセットボタン等でストア値が変わった時の反映用）
   */
  useEffect(() => {
    if (!profile) return;
    setCropInputs({
      top: String(profile.cropInsets?.top ?? 0),
      right: String(profile.cropInsets?.right ?? 0),
      bottom: String(profile.cropInsets?.bottom ?? 0),
      left: String(profile.cropInsets?.left ?? 0),
    });
  }, [profile?.cropInsets?.top, profile?.cropInsets?.right, profile?.cropInsets?.bottom, profile?.cropInsets?.left]);

  /**
   * トリミング値の入力変更ハンドラ
   *
   * 入力中はローカルの文字列として保持し、onBlur で確定する。
   *
   * @param side - 変更する辺
   * @param value - 入力文字列
   */
  function handleCropInputChange(
    side: "top" | "right" | "bottom" | "left",
    value: string
  ) {
    setCropInputs((prev) => ({ ...prev, [side]: value }));
  }

  /**
   * トリミング値の入力確定ハンドラ
   *
   * 入力値を数値に変換し、空文字や負数の場合は 0 に戻す。
   * 確定時に Zustand ストアを更新する。
   *
   * @param side - 確定する辺
   */
  function handleCropInputBlur(
    side: "top" | "right" | "bottom" | "left"
  ) {
    if (!profile || !selectedProfileKey) return;
    const value = cropInputs[side];
    const num = parseInt(value, 10);
    updateCustomProfile(selectedProfileKey, {
      cropInsets: {
        ...(profile.cropInsets ?? { top: 0, right: 0, bottom: 0, left: 0 }),
        [side]: isNaN(num) || num < 0 ? 0 : num,
      },
    });
  }

  /**
   * トリミング値を増減する
   *
   * +/- ボタンから呼び出され、現在のストア値に delta を加算/減算する。
   * 結果が負数にならないようにクランプする。
   *
   * @param side - 変更する辺
   * @param delta - 増減値（+1 または -1）
   */
  function handleCropAdjust(
    side: "top" | "right" | "bottom" | "left",
    delta: number
  ) {
    if (!profile || !selectedProfileKey) return;
    const current = profile.cropInsets?.[side] ?? 0;
    const newValue = Math.max(0, current + delta);
    updateCustomProfile(selectedProfileKey, {
      cropInsets: {
        ...(profile.cropInsets ?? { top: 0, right: 0, bottom: 0, left: 0 }),
        [side]: newValue,
      },
    });
  }

  // プロファイル未ロード時は何も表示しない（デフォルトは kindle であり未選択状態は起こらない）
  if (!profile || !selectedProfileKey) {
    return null;
  }

  /**
   * キャプチャテストを実行する
   *
   * 選択中のプロファイル設定で1枚キャプチャし、トリミング適用後の
   * 画像をプレビュー表示する。利用する Rust コマンドは `capture_screen`。
   */
  async function handleTestCapture() {
    if (!profile) return;
    setIsTesting(true);
    setTestImage(null);
    try {
      const result = await invoke<{ base64: string; width: number; height: number }>(
        "capture_screen",
        { profile }
      );
      setTestImage(`data:image/png;base64,${result.base64}`);
    } catch (err) {
      console.error("キャプチャテストエラー:", err);
      // エラー時はプレビューをクリア（将来的にはトースト通知等を検討）
      setTestImage(null);
    } finally {
      setIsTesting(false);
    }
  }

  return (
    <div className="space-y-5">
      {/* ヘッダー: プロファイル名 + リセットボタン */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">{profile.name}</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            {hasCustom
              ? "カスタム設定が適用されています"
              : "ビルトイン既定値が使用されています"}
          </p>
        </div>
        {hasCustom && (
          <Button
            variant="outline"
            size="sm"
            className="gap-1 h-8"
            onClick={() => selectedProfileKey && resetProfile(selectedProfileKey)}
          >
            <RotateCcw className="h-3.5 w-3.5" />
            デフォルトに戻す
          </Button>
        )}
      </div>

      {/* ページ送り設定 */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-4 items-end">
        {/* ページ送りキー */}
        <div className="space-y-1.5">
          <Label className="text-xs">ページ送りキー</Label>
          <Select
            value={profile.pageTurnKey}
            onValueChange={(value) =>
              value && updateCustomProfile(selectedProfileKey, { pageTurnKey: value })
            }
          >
            <SelectTrigger>
              <SelectValue>
                {(value: string | null) => {
                  const labelMap: Record<string, string> = {
                    right: "右矢印（→）",
                    left: "左矢印（←）",
                  };
                  return <span>{value ? labelMap[value] ?? value : ""}</span>;
                }}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="right">右矢印（→）</SelectItem>
              <SelectItem value="left">左矢印（←）</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 待機時間 */}
        <div className="space-y-1.5">
          <Label className="text-xs">ページ送り待機時間（秒）</Label>
          <Select
            value={String(profile.pageWait)}
            onValueChange={(value) =>
              value && updateCustomProfile(selectedProfileKey, { pageWait: parseFloat(value) })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="0.05">0.05</SelectItem>
              <SelectItem value="0.10">0.10</SelectItem>
              <SelectItem value="0.15">0.15</SelectItem>
              <SelectItem value="0.20">0.20</SelectItem>
              <SelectItem value="0.25">0.25</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* トリミング設定 */}
      <div className="space-y-3">
        {/* トリミング見出し */}
        <h4 className="text-sm font-semibold">取り込み画像トリミング</h4>

        {/* 十字レイアウトリミング入力 */}
        <div className="grid grid-cols-3 gap-x-4 gap-y-2 justify-items-center">
          {/* Row 1: empty | 上 | empty */}
          <div />
          <div className="flex flex-col items-center space-y-1">
            <Label className="text-xs">上 (px)</Label>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => handleCropAdjust("top", -1)}
                disabled={(profile.cropInsets?.top ?? 0) <= 0}
              >
                <Minus className="h-3 w-3" />
              </Button>
              <Input
                type="text"
                inputMode="numeric"
                className="max-w-[56px] text-center"
                value={cropInputs.top}
                onChange={(e) => handleCropInputChange("top", e.target.value)}
                onBlur={() => handleCropInputBlur("top")}
              />
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => handleCropAdjust("top", +1)}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>
          </div>
          <div />

          {/* Row 2: 左 | empty | 右 */}
          <div className="flex flex-col items-center space-y-1">
            <Label className="text-xs">左 (px)</Label>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => handleCropAdjust("left", -1)}
                disabled={(profile.cropInsets?.left ?? 0) <= 0}
              >
                <Minus className="h-3 w-3" />
              </Button>
              <Input
                type="text"
                inputMode="numeric"
                className="max-w-[56px] text-center"
                value={cropInputs.left}
                onChange={(e) => handleCropInputChange("left", e.target.value)}
                onBlur={() => handleCropInputBlur("left")}
              />
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => handleCropAdjust("left", +1)}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>
          </div>
          <div className="flex flex-col items-center justify-center space-y-1.5 w-full h-full">
            <Button
              variant="outline"
              size="sm"
              className="gap-1"
              onClick={handleTestCapture}
              disabled={isTesting}
            >
              <Camera className="h-3.5 w-3.5" />
              キャプチャテスト
            </Button>
            {testImage ? (
              <div className="overflow-auto max-w-[480px] max-h-[320px] rounded border">
                <img
                  src={testImage}
                  alt="キャプチャ結果"
                  className="object-contain origin-top-left"
                  style={{ transform: `scale(${zoom})` }}
                />
              </div>
            ) : (
              <span className="text-[10px] text-muted-foreground">
                {isTesting ? "キャプチャ中..." : "キャプチャ結果"}
              </span>
            )}
            {testImage && (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  onClick={handleZoomOut}
                  disabled={zoom <= MIN_ZOOM}
                >
                  <ZoomOut className="h-3.5 w-3.5" />
                </Button>
                <span className="text-xs text-muted-foreground min-w-[40px] text-center">
                  {Math.round(zoom * 100)}%
                </span>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  onClick={handleZoomIn}
                  disabled={zoom >= MAX_ZOOM}
                >
                  <ZoomIn className="h-3.5 w-3.5" />
                </Button>
              </div>
            )}
          </div>
          <div className="flex flex-col items-center space-y-1">
            <Label className="text-xs">右 (px)</Label>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => handleCropAdjust("right", -1)}
                disabled={(profile.cropInsets?.right ?? 0) <= 0}
              >
                <Minus className="h-3 w-3" />
              </Button>
              <Input
                type="text"
                inputMode="numeric"
                className="max-w-[56px] text-center"
                value={cropInputs.right}
                onChange={(e) => handleCropInputChange("right", e.target.value)}
                onBlur={() => handleCropInputBlur("right")}
              />
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => handleCropAdjust("right", +1)}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>
          </div>

          {/* Row 3: empty | 下 | empty */}
          <div />
          <div className="flex flex-col items-center space-y-1">
            <Label className="text-xs">下 (px)</Label>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => handleCropAdjust("bottom", -1)}
                disabled={(profile.cropInsets?.bottom ?? 0) <= 0}
              >
                <Minus className="h-3 w-3" />
              </Button>
              <Input
                type="text"
                inputMode="numeric"
                className="max-w-[56px] text-center"
                value={cropInputs.bottom}
                onChange={(e) => handleCropInputChange("bottom", e.target.value)}
                onBlur={() => handleCropInputBlur("bottom")}
              />
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => handleCropAdjust("bottom", +1)}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>
          </div>
          <div />
        </div>

        {/* プレビュー反映ボタン */}
        <div className="flex justify-center pt-1">
          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={handleTestCapture}
            disabled={isTesting}
          >
            <Camera className="h-3.5 w-3.5" />
            プレビューに反映
          </Button>
        </div>

        {/* トリミング説明文 */}
        <p className="text-xs text-muted-foreground text-center">
          外枠・タイトルバーを除外して書籍コンテンツ部分だけを切り出します（ピクセル単位）
        </p>
      </div>
    </div>
  );
}
