# キャプチャ処理のシーケンス図

`ui/capture_tab.py` の「キャプチャ開始」ボタンから、`CaptureEngine`
（`core/capture_engine.py`）が1ページを撮影し終えるまでの流れです。

## 起動〜1ページ目撮影まで

```mermaid
sequenceDiagram
    participant UI as CaptureTab
    participant Engine as CaptureEngine
    participant Win as window_utils (Quartz/AppKit)
    participant App as 対象アプリ (例: Kindle)

    UI->>Engine: find_target_window()
    Engine->>Win: find_window(keyword, process_name)
    Win-->>Engine: CGWindowID または None
    UI->>Engine: set_target_window(hwnd)
    Engine->>Win: get_window_rect(hwnd)
    UI->>Engine: activate_target_window(hwnd)
    Engine->>Win: activate_window(hwnd)
    Win->>App: NSRunningApplication.activateWithOptions_
    Win->>Win: 最前面化を最大2秒リトライ確認
    UI->>Engine: start(save_folder, title)
    Note over Engine: 別スレッドで _capture_loop() 開始
    Engine->>Win: has_screen_recording_access()
    Engine->>Win: has_accessibility_access()
    Engine->>Win: is_window_frontmost(hwnd)
    Note over Engine: いずれか失敗ならエラー表示して停止
    Engine->>Engine: detect_boundaries() (既定は全幅)
    Engine->>Engine: _grab() で1ページ目を撮影・保存 (001.png)
```

## 2ページ目以降: ページめくり + エスカレーション

```mermaid
sequenceDiagram
    participant Engine as CaptureEngine
    participant OS as pyautogui / Quartz Event
    participant App as 対象アプリ

    loop 各ページ
        Engine->>Engine: is_window_frontmost() 確認
        Engine->>OS: _send_page_turn(現在の方式)
        OS->>App: キー送信 (right等) またはスクロール
        loop 変化待ち (timeout_seconds まで)
            Engine->>Engine: _grab() → _has_meaningful_change(old, new)
            alt 実質的な変化あり (差分比 > 0.5%)
                Engine->>Engine: 画像を保存 (NNN.png)、次ページへ
            else タイムアウト かつ 未試行の方式あり
                Engine->>Engine: 次の方式へエスカレーション<br/>(right→space→pagedown→down→scroll)
                Engine->>OS: _send_page_turn(次の方式)
            else 全方式で変化なし
                Engine->>Engine: 最終ページと判断し停止
            end
        end
    end
```

## 補足

- 一度エスカレーションで有効な方式が見つかると、`active_turn_idx` が
  更新され、以降のページも同じ方式が使われ続けます（毎回最初からやり直さない）
- `is_window_frontmost()` のチェックはループの先頭で毎回行われ、対象アプリが
  最前面でなくなった場合は即座に安全停止します（詳細は
  [../developer/architecture.md](../developer/architecture.md)）
