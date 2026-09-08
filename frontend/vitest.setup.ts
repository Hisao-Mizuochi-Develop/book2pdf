import "@testing-library/jest-dom/vitest";

// 結合テストで使用する MSW サーバーのセットアップです。
// 全テストファイル共通で server を起動し、テスト間でハンドラ状態をリセットします。

import { beforeAll, afterEach, afterAll } from "vitest";
import { server } from "@/mocks/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

