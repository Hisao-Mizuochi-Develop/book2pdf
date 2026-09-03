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

// UI セレクト（ドロップダウン）コンポーネント群を読み込み
// Select: ドロップダウン本体, SelectContent: 選択肢リスト,
// SelectItem: 個別選択肢, SelectTrigger: トリガー, SelectValue: 表示値
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
// プロファイル状態管理ストア（Zustand）を読み込み
// ビルトインプロファイル一覧・選択中プロファイルを取得するために使用する
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

  // 選択中のプロファイル名を取得
  // builtinProfiles が未読み込み（空配列）でも selectedProfileKey は "kindle" 等の初期値を持つため、
  // SelectValue に手動で表示テキストを渡して初期表示時にplaceholderにならないようにする。
  // builtinProfiles 読み込み後は .find() で name が解決される。
  const selectedProfile = builtinProfiles.find((p) => p.key === selectedProfileKey);
  const displayLabel = selectedProfile?.name ?? selectedProfileKey ?? "プロファイルを選択";

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-muted-foreground shrink-0">プロファイル</span>
      <Select
        value={selectedProfileKey ?? undefined}
        onValueChange={(key) => key && selectProfile(key)}
      >
        <SelectTrigger className="w-[240px]">
          <SelectValue placeholder="プロファイルを選択">{displayLabel}</SelectValue>
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
