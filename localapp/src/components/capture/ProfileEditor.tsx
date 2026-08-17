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

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProfileStore } from "@/store/profileStore";
import { invoke } from "@tauri-apps/api/core";
import { RotateCcw, Camera, ZoomIn, ZoomOut } from "lucide-react";
import { useState, useMemo } from "react";


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
            <Input
              type="number"
              min="0"
              step="1"
              className="max-w-[80px] text-center"
              value={String(profile.cropInsets?.top ?? 0)}
              onChange={(e) => {
                const num = parseInt(e.target.value, 10);
                updateCustomProfile(selectedProfileKey, {
                  cropInsets: {
                    ...(profile.cropInsets ?? { top: 0, right: 0, bottom: 0, left: 0 }),
                    top: isNaN(num) ? 0 : num,
                  },
                });
              }}
            />
          </div>
          <div />

          {/* Row 2: 左 | empty | 右 */}
          <div className="flex flex-col items-center space-y-1">
            <Label className="text-xs">左 (px)</Label>
            <Input
              type="number"
              min="0"
              step="1"
              className="max-w-[80px] text-center"
              value={String(profile.cropInsets?.left ?? 0)}
              onChange={(e) => {
                const num = parseInt(e.target.value, 10);
                updateCustomProfile(selectedProfileKey, {
                  cropInsets: {
                    ...(profile.cropInsets ?? { top: 0, right: 0, bottom: 0, left: 0 }),
                    left: isNaN(num) ? 0 : num,
                  },
                });
              }}
            />
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
            <Input
              type="number"
              min="0"
              step="1"
              className="max-w-[80px] text-center"
              value={String(profile.cropInsets?.right ?? 0)}
              onChange={(e) => {
                const num = parseInt(e.target.value, 10);
                updateCustomProfile(selectedProfileKey, {
                  cropInsets: {
                    ...(profile.cropInsets ?? { top: 0, right: 0, bottom: 0, left: 0 }),
                    right: isNaN(num) ? 0 : num,
                  },
                });
              }}
            />
          </div>

          {/* Row 3: empty | 下 | empty */}
          <div />
          <div className="flex flex-col items-center space-y-1">
            <Label className="text-xs">下 (px)</Label>
            <Input
              type="number"
              min="0"
              step="1"
              className="max-w-[80px] text-center"
              value={String(profile.cropInsets?.bottom ?? 0)}
              onChange={(e) => {
                const num = parseInt(e.target.value, 10);
                updateCustomProfile(selectedProfileKey, {
                  cropInsets: {
                    ...(profile.cropInsets ?? { top: 0, right: 0, bottom: 0, left: 0 }),
                    bottom: isNaN(num) ? 0 : num,
                  },
                });
              }}
            />
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
