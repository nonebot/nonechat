from dataclasses import field, dataclass

from rich.text import Text
from textual.widget import Widget
from rich.console import RenderableType

from .model import StateChange

MAX_LOG_RECORDS = 500


@dataclass
class LogStorage:
    log_history: list[RenderableType] = field(default_factory=list)
    log_watchers: list[Widget] = field(default_factory=list)

    def write_log(self, *logs: RenderableType) -> None:
        self.log_history.extend(logs)
        if len(self.log_history) > MAX_LOG_RECORDS:
            self.log_history = self.log_history[-MAX_LOG_RECORDS:]
        self.emit_log_watcher(*logs)

    def add_log_watcher(self, watcher: Widget) -> None:
        self.log_watchers.append(watcher)

    def remove_log_watcher(self, watcher: Widget) -> None:
        self.log_watchers.remove(watcher)

    def emit_log_watcher(self, *logs: RenderableType) -> None:
        for watcher in self.log_watchers:
            watcher.post_message(StateChange(logs))


class FakeIO:
    def __init__(self, storage: LogStorage) -> None:
        self.storage = storage
        self._buffer: list[str] = []

    def isatty(self):
        return True

    def write(self, string: str) -> None:
        self._buffer.append(string)

        # By default, `print` adds a "\n" suffix which results in a buffer
        # flush. You can choose a different suffix with the `end` parameter.
        # If you modify the `end` parameter to something other than "\n",
        # then `print` will no longer flush automatically. However, if a
        # string you are printing contains a "\n", that will trigger
        # a flush after that string has been buffered, regardless of the value
        # of `end`.
        if "\n" in string:
            self.flush()

    def flush(self) -> None:
        self._write_to_storage()
        self._buffer.clear()

    def _write_to_storage(self) -> None:
        self.storage.write_log(Text.from_ansi("".join(self._buffer), end="", tab_size=4))

    def read(self) -> str:
        self.flush()  # 确保所有内容都被写入存储
        return "".join(self._buffer)
