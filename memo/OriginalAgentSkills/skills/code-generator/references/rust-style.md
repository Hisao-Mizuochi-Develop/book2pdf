# rust-style

## 基本

- Tauri v2 / Rust 最新エディション
- 関数・構造体には doc comments を記述
- unsafe 使用時は特に理由を記述

## use コメント例

```rust
// tauri: デスクトップアプリケーションフレームワーク。IPC コマンドを提供
use tauri::command;

// serde: JSON シリアライズ・デシリアライズ
use serde::{Deserialize, Serialize};
```

## doc comment 例

```rust
/// 指定された画像ディレクトリから OCR 用 ZIP アーカイブを作成する。
/// 画像は昇順にソートされてから追加される。
pub fn create_image_zip(input_dir: &Path, output_path: &Path) -> Result<(), Box<dyn Error>> {
    ...
}
```
