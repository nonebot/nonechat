from typing import TYPE_CHECKING, cast

from textual.widget import Widget

from ..components.log import LogPanel
from ..components.log.toolbar import Toolbar

if TYPE_CHECKING:
    from ..app import Frontend


class LogView(Widget):
    DEFAULT_CSS = """
    LogView {
    }
    LogView > Toolbar {
        dock: top;
    }
    """

    def __init__(self):
        super().__init__()
        # setting = self.app.setting
        # if setting.bg_color:
        #     self.styles.background = setting.bg_color

    def compose(self):
        yield Toolbar(self.app.setting)
        yield LogPanel()

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)
