"use client";

import { useEffect, useState } from "react";
import type { DebugConfig } from "@/types";

/**
 * ランタイム設定ファイル (/debug-config.json) を読み込み、
 * デバッグ表示エリアの表示制御に使用するカスタムフックです。
 *
 * コンテナリビルドなしで表示切り替えできるよう、ビルド時ではなく
 * ブラウザ上で JSON を fetch します。
 */
export function useDebugConfig(): {
  showDebugTimingPanel: boolean;
  loading: boolean;
} {
  const [config, setConfig] = useState<DebugConfig>({
    showDebugTimingPanel: false,
  });
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let cancelled = false;

    fetch("/debug-config.json")
      .then((res) => (res.ok ? res.json() : { showDebugTimingPanel: false }))
      .then((data: DebugConfig) => {
        if (!cancelled) {
          setConfig(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setConfig({ showDebugTimingPanel: false });
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { showDebugTimingPanel: config.showDebugTimingPanel, loading };
}
