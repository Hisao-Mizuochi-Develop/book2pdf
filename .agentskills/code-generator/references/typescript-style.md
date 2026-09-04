# typescript-style

## 基本

- Next.js 15 App Router
- TypeScript（strict 推奨）
- Tailwind CSS
- UI コンポーネントには variant/size/用途を含む JSDoc

## import コメント例

```typescript
// React: UI コンポーネントの状態管理と副作用処理
import { useState, useEffect } from "react";

// axios: バックエンド API 呼び出し
import axios from "axios";
```

## JSDoc 例

```typescript
/**
 * プライマリーボタン（大サイズ）。
 * メインフローの確定・送信アクションに使用する。
 */
export function PrimaryButton({ children, onClick }: PrimaryButtonProps) {
  ...
}
```
