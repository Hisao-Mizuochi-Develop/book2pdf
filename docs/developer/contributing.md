# コントリビューションガイド

## コーディング規約

`pyproject.toml` に `ruff` の設定があります。

```bash
book_env/bin/pip install ruff
book_env/bin/ruff check .
book_env/bin/ruff format .
```

- `target-version = "py311"`, `line-length = 100`
- 有効ルール: `E`, `F`, `W`, `I`（isort）, `UP`（pyupgrade）, `B`（bugbear）, `SIM`
- `book_env`, `ndlocr-lite`, `__pycache__` は対象外
- クオートはダブルクオート、インデントはスペース

このプロジェクト全体の方針として、コメントは「なぜそうしたか」を書き、
「何をしているか」は書かない（既存コードの docstring・インラインコメントが
この方針を徹底しているので、既存スタイルに合わせてください）。

## 新しいキャプチャプロファイルを追加する

GUIから「詳細設定」→「複製して保存」で追加するのが基本ですが、
ビルトインプロファイルとしてコードに追加する場合は
`core/capture_profiles.py` の `BUILTIN_PROFILES` に `CaptureProfile` を追加します。

```python
BUILTIN_PROFILES["my_app"] = CaptureProfile(
    name="My App",
    window_title_keyword="MyApp",
    page_wait=0.5,
    process_name="MyApp",  # macOSのオーナー名 (.exeサフィックスは自動除去される)
)
```

macOS実機でのオーナー名の調べ方は
[../user/custom-profiles.md](../user/custom-profiles.md) を参照してください。

## 新しい出力形式を追加する

1. `core/pdf_builder.py`（またはPDF以外なら新規モジュール）に生成関数を追加
   - シグネチャは既存の `images_to_pdf(folder, output_folder, filename, on_progress, chapters)`
     系に合わせると `ui/convert_tab.py` 側の実装が楽になります
2. `ui/convert_tab.py` の `formats` リストに `(value, 表示名)` を追加
3. `_run_convert()` の `thread()` 内に `elif fmt == "...":` 分岐を追加
4. 専用オプション（段落整形など）が必要なら `_on_format_changed()` の
   有効/無効切り替えロジックも更新

実装例として、`images_with_text_pdf()`（画像+テキストPDF、本移植で新規追加）が
参考になります。

## core/ の設計原則

- `core/` はUI非依存。`tkinter` / `customtkinter` を import しない
- 進捗通知は `on_progress(current, total, filename)` コールバック関数で統一
- 戻り値は原則 `(success: bool, message_or_data)` のタプル
- macOS固有のAPI呼び出しは `core/window_utils.py` に閉じ込め、他モジュールは
  そこから関数をimportするだけにする（Windows版との差分を最小化するため）

## 検証の仕方

GUIをただ起動するだけでなく、`core/` の関数を直接スクリプトから呼んで
実機（実際の電子書籍アプリ）に対して動作確認するのが効率的です。
[verification-log.md](verification-log.md) に実施例があります。

```bash
book_env/bin/python3 -c "
from core.capture_engine import CaptureEngine
from core.capture_profiles import BUILTIN_PROFILES
engine = CaptureEngine(BUILTIN_PROFILES['kindle'])
hwnd = engine.find_target_window()
print(hwnd)
"
```
