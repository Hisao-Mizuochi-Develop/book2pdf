"use client";

/**
 * アップロードされた画像ファイル名一覧を表示するコンポーネントです。
 */

export interface ImageListProps {
  /** 表示する画像ファイル名の一覧です。 */
  files: string[];
}

/**
 * アップロードされた画像ファイル名をグリッド表示します。
 * 縦3行固定、横スクロールバーで表示します。
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
      <div className="mt-1 overflow-x-auto rounded-lg border border-border bg-background p-2">
        <div className="grid grid-flow-col grid-rows-3 gap-x-4 gap-y-1 min-w-max">
          {files.map((name) => (
            <span key={name} className="whitespace-nowrap text-sm text-foreground">
              {name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
