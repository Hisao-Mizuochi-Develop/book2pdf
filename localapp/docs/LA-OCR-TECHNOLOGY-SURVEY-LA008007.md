# localapp 単体 OCR→PDF 技術調査レポート（タスク LA008007）

**実施日**: 2026-09-04  
**調査者**: Cline (AI アシスタント)  
**目的**: localapp 内で画像→OCR→検索可能 PDF を単体完結させるための技術選定と POC 検証

---

## 1. PDF 生成 Crate 選定

### 1.1 候補と評価

| Crate | バージョン | 評価 | 採用判断 |
|---|---|---|---|
| `printpdf` | 0.7.0 | シンプルな高レベル API。画像埋め込みに対応。MIT ライセンス。 | **採用** |
| `pdf-writer` | 0.12 | 低レベルで細かい制御が可能だが、学習コストが高い。 | 非採用 |
| `genpdf` | 0.2 | テキスト中心。画像レイアウトが複雑。 | 非採用 |

### 1.2 POC 結果（`printpdf` 0.7.0）

- **画像→PDF 埋め込みに成功**。出力ファイル `/tmp/poc_printpdf_output.pdf` を生成。
- **正しい API パターン**:
  ```rust
  let decoder = image_crate::codecs::jpeg::JpegDecoder::new(...)?;
  let image = Image::try_from(decoder)?;
  let transform = ImageTransform {
      translate_x: Some(x_mm),
      translate_y: Some(y_mm),
      scale_x: Some(scale),
      scale_y: Some(scale),
      rotate: None,
      dpi: Some(300.0),
  };
  image.add_to_layer(layer, transform)?;
  ```
- **画像 crate の namespace shadowing**を解決。`printpdf` は `pub mod image` をエクスポートするため、外部の `image` crate と衝突。`image_crate = { package = "image", version = "0.24" }` で alias 化。
- **A4 フィットロジックを確立**:
  - ページ: 210mm × 297mm（A4）
  - マージン: 10mm（四辺）
  - 300 DPI の px→mm 変換: `mm = px / 300.0 * 25.4`
  - `ImageTransform` でセンタリング + アスペクト比維持スケーリング
- **PDF 出力検証**: PyMuPDF + pikepdf で A4 サイズ（595.28×841.89 pt）と画像埋め込みを確認。

### 1.3 注意事項

- `printpdf` 0.7.0 は内部で `image` 0.24.3 に依存。localapp では `image` 0.25.10 を使用しており、**デュアルバージョンのリスク**あり。
  - 対応策 A: `image` 0.24.x を別名でインポート（現在の POC 方式）
  - 対応策 B: localapp 全体を `image` 0.24.x にダウングレード（影響調査が必要）
- `printpdf` 0.7.0 の `Image::try_from(decoder)` は `_EXPECTS_IMAGE_0_24_` フラグ付きビルド時のみ有効。API の unstable 性に注意。

---

## 2. OCR エンジン選定

### 2.1 候補と評価

| Crate | バージョン | 裏側エンジン | 評価 | 採用判断 |
|---|---|---|---|---|
| `tesseract` | 0.15.2 | Tesseract 5.x | Rust FFI ラッパー。`SetImage` → `GetUTF8Text` の手続き型 API。 | 非採用 |
| `leptess` | 0.14.0 | Tesseract 5.x + Leptonica | `get_component_boxes()` で word/line 単位の bbox を直接取得可能。Leptonica の安全なラッパー。 | **採用** |
| PaddleOCR / EasyOCR | — | 深層学習 | Rust バインディングがない、または CLI 呼び出しのみ。 | 非採用 |

### 2.2 選定理由（`leptess`）

1. **`get_component_boxes()` の存在**: `RIL_WORD` / `RIL_TEXTLINE` レベルで `(x, y, w, h, text)` を直接取得でき、手動の hOCR / TSV / XML パースが不要。
2. **Leptonica の抽象化**: `Pix` 構造体のメモリ管理が safe wrapper で行われ、生ポインタ操作が減る。
3. **`tesseract` crate との差**: `tesseract` crate は文字列テキストしか取れず、bbox 情報を得るには hOCR 出力を自前でパースする必要がある。

### 2.3 コード例（予想）

```rust
use leptess::{LepTess, Variable};

let mut lt = LepTess::new(None, "jpn")?;
lt.set_image(&pix)?;
lt.set_variable(Variable::TesseditPagesegMode, "6")?; // PSM_AUTO

// word 単位の bbox を取得
let boxes = lt.get_component_boxes(leptess::capi::TessPageIteratorLevel::RIL_WORD)?;
for (i, box) in boxes.iter().enumerate() {
    println!("word {}: '{}' at ({},{},{},{})", 
        i, box.text, box.x1, box.y1, box.x2 - box.x1, box.y2 - box.y1);
}
```

---

## 3. 画像サイズ扱いの方針

| 項目 | 方針 |
|---|---|
| ページサイズ | 固定 A4（210mm × 297mm / 595.28pt × 841.89pt） |
| 画像配置 | アスペクト比維持で A4 描画領域に fit、余白は白背景 |
| マージン | 10mm（四辺） |
| 解像度 | 300 DPI を基準とした px→mm 変換 |
| 将来的拡張 | 「元画像サイズ維持」オプションを追加可能な設計とする |

---

## 4. backend + ocr-worker 実装との差異

localapp 単体パイプラインと、既存の backend + ocr-worker 実装には根本的な差異があります。**両者は「オフライン・軽量」対「ネットワーク・高精度」という位置づけで並存**します。

| 項目 | backend + ocr-worker | localapp 単体（予定） |
|---|---|---|
| **OCR エンジン** | ndlocr_cli（深層学習、国立国会図書館） | Tesseract（`leptess` Rust バインディング） |
| **PDF 生成** | PyMuPDF（fitz） | `printpdf` 0.7.0 |
| **ページサイズ** | 元画像サイズを維持 | A4 固定、アスペクト比維持 fit |
| **OCR 出力形式** | XML（.sorted.xml）+ .txt | 構造体 `(text, bbox)[]` 直接（中間ファイルなし） |
| **アーキテクチャ** | 分散型（コンテナ間 HTTP） | スタンドアロン（同一プロセス） |
| **進捗通知** | SSE（Server-Sent Events） | Zustand ストア（ローカル） |
| **ネットワーク** | 必須 | 不要（オフライン動作可能） |
| **精度** | 高精度（深層学習） | 標準（古典的 OCR） |

### 4.1 座標系変換の違い

- **backend**: XML 左上原点 → PyMuPDF 左下原点（`pdf_y = pdf_height - (xml_y + xml_height)`）
- **localapp**: Tesseract 左上原点 → `printpdf` 左下原点。A4 へのスケーリング係数を px→mm で計算する必要がある。

### 4.2 PDF テキストレイヤーの違い

- **backend**: PyMuPDF の `insert_text()` でフォントサイズ自動縮小、濃い緑色の透明テキスト
- **localapp**: `printpdf` でテキスト描画。フォント埋め込みと透明色指定の方法が異なる。LA008009 で詳細調査が必要。

---

## 5. 残課題・次のステップ

| 課題 | 次のタスク | 内容 |
|---|---|---|
| `image` crate デュアルバージョン | LA008008 | compile-size 影響を測定し、ダウングレードか別名維持を決定 |
| `leptess` 統合 POC | LA008009 | テスト PNG から OCR → `(text, bbox)[]` → PDF テキストレイヤー配置の一気通貫 |
| `printpdf` テキスト描画 | LA008009 | 日本語フォント埋め込み、透明テキスト、座標変換の詳細調査 |
| ndlocr_cli との精度比較 | LA008010 以降 | 同一画像セットで Tesseract vs ndlocr_cli の認識精度を比較評価 |

---

## 6. 結論

- **PDF 生成**: `printpdf` 0.7.0 を採用。画像→A4 PDF 埋め込みは POC で実証済み。
- **OCR エンジン**: `leptess` 0.14.0 を採用。`get_component_boxes()` で bbox 付きテキストを直接取得可能。
- **方針**: A4 固定ページ、アスペクト比維持 fit、10mm マージン。
- **リスク**: `image` crate のデュアルバージョン。LA008008 で対応方針を確定する。
