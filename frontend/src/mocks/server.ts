// MSW サーバーインスタンスです。
// vitest.setup.ts からライフサイクルメソッドを通じて起動・停止します。

import { setupServer } from "msw/node";
import { handlers } from "./handlers";

/**
 * テスト環境で使用する MSW サーバーインスタンスです。
 */
export const server = setupServer(...handlers);
