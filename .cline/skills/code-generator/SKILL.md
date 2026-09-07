---
name: code-generator
description: |
  Generate code following project conventions for Python, TypeScript, and Rust.
  Activate when writing or reviewing source code in backend/, frontend/, localapp/, or ocr-worker/.
compatibility: VS Code + Cline
metadata:
  author: book2pdf-team
  version: "1.0"
---

# code-generator

## 概要
本スキルは、book2pdf プロジェクトの言語別コーディング規約と、API/関数呼び出しの整合性確認手順を定めます。

## 手順

1. **技術スタックの確認**
   - Web backend: FastAPI + Python
   - Web frontend: Next.js 15 + TypeScript + Tailwind CSS
   - Local app: Tauri v2 + Rust + React + Vite
   - OCR: ndlocr_cli
   - PDF: PyMuPDF
   - 基盤: Docker + Docker Compose
   - アーキテクチャ: FastAPI と ndlocr_cli は別コンテナとして分離

2. **コメント必須**
   - 各関数・クラス・複雑なロジックに JSDoc / docstring / Rust doc comments を付ける
   - 「何をするか」だけでなく「なぜそのように実装したか」の理由も記載
   - UI コンポーネントには variant/size/用途を含む詳細な JSDoc
   - CSS 変数には「用途＋デザイン意図」のコメント

3. **外部依存の宣言文に必ずコメントを付ける**
   - Rust: `use crate::module;` / `use external_crate::Type;` / `mod submodule;`
   - TypeScript: `import { ... } from "module"`
   - Python: `import module`
   - 各識別子の役割も説明する

4. **API・関数呼び出しの整合性確認**（双方向チェック）
   - 呼び出し元と受け側の両ファイルを同時に開く
   - 引数名・キー名・型の整合性を横並びで確認
   - フレームワークの自動変換挙動（camelCase ↔ snake_case など）を確認

## よくある境界ケース
- 規約に反する実装が必要な場合は、コメントで理由を明示
