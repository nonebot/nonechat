from collections.abc import Iterable
from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.events import Unmount
from textual.widgets import RichLog
from rich.console import RenderableType

if TYPE_CHECKING:
    from ...app import Frontend
    from ...setting import ConsoleSetting
    from ...storage import Storage, StateChange


MAX_LINES = 1000


class LogPanel(Widget):
    DEFAULT_CSS = """
    LogPanel {
        layout: vertical;
    }
    LogPanel > TextLog {
        padding: 0 1;
        min-width: 60 !important;
        scrollbar-size-vertical: 1;
    }
    """

    def __init__(self, setting: "ConsoleSetting") -> None:
        super().__init__()

        self.output = RichLog(max_lines=MAX_LINES, min_width=60, wrap=True, markup=True)
        if setting.bg_color:
            self.styles.background = setting.bg_color
            self.output.styles.background = setting.bg_color

    @property
    def storage(self) -> "Storage":
        return cast("Frontend", self.app).storage

    def compose(self):
        yield self.output

    def on_mount(self):
        self.on_log(self.storage.log_history)
        self.storage.add_log_watcher(self)

    def on_unmount(self, event: Unmount):
        self.storage.remove_log_watcher(self)

    def on_state_change(self, event: "StateChange[tuple[RenderableType, ...]]") -> None:
        self.on_log(event.data)

    def on_log(self, logs: Iterable[RenderableType]) -> None:
        for log in logs:
            self.output.write(log)
