export function PdfImportView() {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <h2 className="text-2xl font-semibold tracking-tight">PDF読込</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        外部 PDF を画像化してトリミングタブに引き継ぎます。
      </p>
    </div>
  );
}
