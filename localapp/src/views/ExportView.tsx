export function ExportView() {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <h2 className="text-2xl font-semibold tracking-tight">ZIP出力</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        トリミング済み画像を ZIP アーカイブにまとめます。
      </p>
    </div>
  );
}
