import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useDebugConfig } from "../useDebugConfig";

describe("useDebugConfig", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("showDebugTimingPanel が true の場合、true を返す", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ showDebugTimingPanel: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const { result } = renderHook(() => useDebugConfig());

    await waitFor(() => {
      expect(result.current.showDebugTimingPanel).toBe(true);
    });
    expect(result.current.loading).toBe(false);
    expect(fetchSpy).toHaveBeenCalledWith("/debug-config.json");
  });

  it("showDebugTimingPanel が false の場合、false を返す", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ showDebugTimingPanel: false }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const { result } = renderHook(() => useDebugConfig());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.showDebugTimingPanel).toBe(false);
  });

  it("fetch が失敗した場合、false を返す", async () => {
    fetchSpy.mockRejectedValueOnce(new Error("network error"));

    const { result } = renderHook(() => useDebugConfig());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.showDebugTimingPanel).toBe(false);
  });

  it("fetch が 404 を返した場合、false を返す", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response("not found", { status: 404 }),
    );

    const { result } = renderHook(() => useDebugConfig());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.showDebugTimingPanel).toBe(false);
  });
});
