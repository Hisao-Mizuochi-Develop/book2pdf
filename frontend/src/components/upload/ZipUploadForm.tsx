"use client";

import { useState, useCallback } from "react";
import { createJob, uploadZip } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ImageList } from "./ImageList";
import type { ZipUploadFormProps, ZipUploadStatus } from "@/types";

/**
 * ZIP ファイルをアップロードするフォームコンポーネントです。
 *
 * ジョブ作成 → ZIP アップロード → 画像一覧取得の一連を行い、
 * 完了後に `onUploaded` コールバックを呼び出します。
 */
export function ZipUploadForm({ onUploaded }: ZipUploadFormProps) {
  const [status, setStatus] = useState<ZipUploadStatus>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  const isBusy = status === "creating" || status === "uploading";

  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const selected = event.target.files?.[0] ?? null;
      setFile(selected);
      setError(null);
      if (selected) {
        setStatus("idle");
      }
    },
    [],
  );

  const handleSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();

      if (!file) {
        setError("ZIP ファイルを選択してください。");
        setStatus("error");
        return;
      }

      setError(null);
      setStatus("creating");

      let jobId: string;
      try {
        jobId = await createJob();
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "ジョブの作成に失敗しました。";
        setError(message);
        setStatus("error");
        return;
      }

      setStatus("uploading");

      let files: string[];
      try {
        files = await uploadZip(jobId, file);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "ZIP ファイルのアップロードに失敗しました。";
        setError(message);
        setStatus("error");
        return;
      }

      setUploadedFiles(files);
      setStatus("uploaded");
      onUploaded(jobId, files);
    },
    [file, onUploaded],
  );

  const statusMessage: Record<Exclude<ZipUploadStatus, "error">, string> = {
    idle: "ZIP ファイルを選択してアップロードしてください。",
    creating: "ジョブを作成中です...",
    uploading: "ZIP ファイルをアップロード中です...",
    uploaded: "アップロードが完了しました。",
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="zip-file">ZIP ファイル</Label>
        <Input
          id="zip-file"
          type="file"
          accept=".zip,application/zip,application/x-zip-compressed"
          onChange={handleFileChange}
          disabled={isBusy}
          data-testid="zip-file-input"
        />
      </div>

      <Button
        type="submit"
        disabled={!file || isBusy}
        data-testid="upload-button"
      >
        {status === "uploading" ? "アップロード中..." : "アップロード"}
      </Button>

      <p
        className={`text-sm ${
          status === "uploaded" ? "text-green-600" : "text-muted-foreground"
        }`}
        data-testid="status-message"
      >
        {status === "error" ? error : statusMessage[status]}
      </p>

      {status === "uploaded" && <ImageList files={uploadedFiles} />}
    </form>
  );
}
