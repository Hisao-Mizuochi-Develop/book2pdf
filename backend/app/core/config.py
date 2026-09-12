"""アプリケーション全体で使用する設定値を管理します。

pydantic-settings を使うと、環境変数から型安全に設定を読み込むことができます。
例えば、APP_HOST という環境変数が自動的に host フィールドに反映されます。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# 環境変数から型安全に設定を読み込むためのベースクラスです
# これを継承すると、APP_HOST などの環境変数が自動的にフィールドに反映されます
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定を表すクラスです。

    BaseSettings を継承することで、環境変数から自動的に値を読み込みます。
    値が設定されていない場合は、default= で指定したデフォルト値が使われます。
    """

    # Web サーバーが待ち受けるホスト名です
    # Docker コンテナ内では 0.0.0.0 を指定します
    host: str = "0.0.0.0"

    # Web サーバーが待ち受けるポート番号です
    port: int = 8000

    # デバッグ時に自動リロードを有効にするかどうか
    reload: bool = False

    # OCR 処理中にフロントエンドへ段階的進捗を届けるための、
    # ページマーカー書き込み間隔（秒）です。
    # 0 に設定すると書き込み間隔なし（従来と同じ挙動）になります。
    ocr_progress_step_delay: float = 0.5


# アプリケーション全体で使う設定インスタンスです
# この変数を他のモジュールからインポートして使います
settings = Settings()
