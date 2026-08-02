"""タブ間共有状態"""


class AppState:
    """タブ間で共有されるアプリケーション状態"""

    def __init__(self):
        self.last_capture_folder = ""
        self.last_trim_output_folder = ""
        self._listeners = []

    def add_listener(self, callback):
        self._listeners.append(callback)

    def notify(self, event, data=None):
        for listener in self._listeners:
            listener(event, data)
