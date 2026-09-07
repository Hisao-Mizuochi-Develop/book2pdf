"use client";

/**
 * アップロードされた画像ファイル名一覧を表示するコンポーネントです。
 */

export interface ImageListProps {
  /** 表示する画像ファイル名の一覧です。 */
  files: string[];
}

/**
 * アップロードされた画像ファイル名をリスト表示します。
 * ファイルが空の場合は何も描画しません。
 */
export function ImageList({ files }: ImageListProps) {
  if (files.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <h3 className="text-sm font-medium text-card-foreground">
        アップロードされた画像
      </h3>
      <ul className="mt-1 max-h-32 overflow-auto rounded-lg border border-border bg-background p-2 text-sm text-foreground">
        {files.map((name) => (
          <li key={name}>{name}</li>
        ))}
      </ul>
    </div>
  );
}
