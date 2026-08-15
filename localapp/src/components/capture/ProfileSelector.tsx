/**
 * プロファイル選択コンポーネント
 *
 * 【役割】
 * shadcn/ui の Select を使用し、取得したビルトインプロファイル一覧から
 * 現在のプロファイルを選択・切り替える UI を提供する。
 *
 * 【状態管理】
 * `useProfileStore` を subscribe して `builtinProfiles` と `selectedProfileKey` を取得。
 * 選択が変更されると `selectProfile()` で Zustand ストアを更新する。
 */

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProfileStore } from "@/store/profileStore";

/**
 * プロファイル選択コンポーネント
 *
 * @returns ドロップダウン形式のプロファイルセレクタ
 */
export function ProfileSelector() {
  const builtinProfiles = useProfileStore((state) => state.builtinProfiles);
  const selectedProfileKey = useProfileStore((state) => state.selectedProfileKey);
  const selectProfile = useProfileStore((state) => state.selectProfile);

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-muted-foreground shrink-0">プロファイル</span>
      <Select
        value={selectedProfileKey ?? undefined}
        onValueChange={(key) => key && selectProfile(key)}
      >
        <SelectTrigger className="w-[240px]">
          <SelectValue placeholder="プロファイルを選択" />
        </SelectTrigger>
        <SelectContent>
          {builtinProfiles.map((profile) => (
            <SelectItem key={profile.key} value={profile.key}>
              {profile.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
