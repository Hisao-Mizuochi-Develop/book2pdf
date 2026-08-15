/**
 * プロファイル編集コンポーネント
 *
 * 【役割】
 * 選択中のプロファイルの詳細設定を表示・編集するパネル。
 * ページ送り待機時間、ウィンドウタイトル、プロセス名などを
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
 * - windowTitleKeyword: テキスト入力
 * - processName: テキスト入力
 * - clickPosition: セレクト（center / top_left）
 * - useBringToTop: トグル（Switch）
 */

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProfileStore } from "@/store/profileStore";
import { RotateCcw } from "lucide-react";

/**
 * プロファイル編集コンポーネント
 *
 * @returns プロファイル詳細設定編集フォーム
 */
export function ProfileEditor() {
  // Zustand ストアから必要な状態・アクションを取得
  const selectedProfileKey = useProfileStore((state) => state.selectedProfileKey);
  const getEffectiveProfile = useProfileStore((state) => state.getEffectiveProfile);
  const updateCustomProfile = useProfileStore((state) => state.updateCustomProfile);
  const resetProfile = useProfileStore((state) => state.resetProfile);
  const hasCustom = useProfileStore((state) =>
    selectedProfileKey ? selectedProfileKey in state.customProfiles : false
  );

  // 現在選択中の実効プロファイル（ビルトイン + カスタム上書きマージ済み）
  const profile = selectedProfileKey ? getEffectiveProfile(selectedProfileKey) : null;

  // ローカル編集状態（フィールドが変更されるまで確定しない）
  const [localPageWait, setLocalPageWait] = useState<string>("");

  // プロファイル切り替え時にローカル状態をリセット
  useEffect(() => {
    if (profile) {
      setLocalPageWait(String(profile.pageWait));
    }
  }, [profile?.key]);

  // プロファイル未選択時の表示
  if (!profile || !selectedProfileKey) {
    return (
      <div className="text-sm text-muted-foreground">
        プロファイルを選択して設定を編集できます。
      </div>
    );
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

      {/* 編集フォーム: 2カラムグリッド */}
      <div className="grid grid-cols-2 gap-x-8 gap-y-4">
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
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="right">右矢印（→）</SelectItem>
              <SelectItem value="left">左矢印（←）</SelectItem>
              <SelectItem value="space">スペース</SelectItem>
              <SelectItem value="arrow">矢印キー（左右）</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 待機時間 */}
        <div className="space-y-1.5">
          <Label className="text-xs">ページ送り待機時間（秒）</Label>
          <Input
            type="number"
            step="0.1"
            min="0"
            value={localPageWait}
            onChange={(e) => {
              setLocalPageWait(e.target.value);
              const num = parseFloat(e.target.value);
              if (!isNaN(num)) {
                updateCustomProfile(selectedProfileKey, { pageWait: num });
              }
            }}
          />
        </div>

        {/* ウィンドウタイトルキーワード */}
        <div className="space-y-1.5">
          <Label className="text-xs">ウィンドウタイトルキーワード</Label>
          <Input
            value={profile.windowTitleKeyword}
            onChange={(e) =>
              updateCustomProfile(selectedProfileKey, {
                windowTitleKeyword: e.target.value,
              })
            }
          />
        </div>

        {/* プロセス名 */}
        <div className="space-y-1.5">
          <Label className="text-xs">プロセス名</Label>
          <Input
            value={profile.processName}
            placeholder="例: Kindle.exe"
            onChange={(e) =>
              updateCustomProfile(selectedProfileKey, {
                processName: e.target.value,
              })
            }
          />
        </div>

        {/* クリック位置 */}
        <div className="space-y-1.5">
          <Label className="text-xs">クリック位置</Label>
          <Select
            value={profile.clickPosition}
            onValueChange={(value) =>
              value && updateCustomProfile(selectedProfileKey, { clickPosition: value })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="center">中央</SelectItem>
              <SelectItem value="top_left">左上</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 最前面化 */}
        <div className="flex items-center gap-3 pt-5">
          <Switch
            id="bring-to-top"
            checked={profile.useBringToTop}
            onCheckedChange={(checked) =>
              updateCustomProfile(selectedProfileKey, {
                useBringToTop: checked,
              })
            }
          />
          <Label htmlFor="bring-to-top" className="text-xs">
            キャプチャ前に最前面へ持ってくる
          </Label>
        </div>
      </div>
    </div>
  );
}
