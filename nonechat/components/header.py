from typing import TYPE_CHECKING, cast

from textual.widgets import Header as TextualHeader
from textual.widgets._header import HeaderIcon, HeaderClock, HeaderTitle

from ..setting import ConsoleSetting

if TYPE_CHECKING:
    from ..app import Frontend


class _Icon(HeaderIcon):
    def __init__(self, setting: ConsoleSetting):
        super().__init__()
        if setting.icon:
            self.icon = setting.icon
        if setting.icon_color:
            self.styles.color = setting.icon_color


class _Title(HeaderTitle):
    def __init__(self, setting: ConsoleSetting):
        super().__init__()
        if setting.title_color:
            self.styles.color = setting.title_color


class Header(TextualHeader):
    DEFAULT_CSS = """
    Header {
    }
    """

    def __init__(self):
        super().__init__(show_clock=True)
        setting = self.app.setting
        if setting.header_color:
            self.styles.background = setting.header_color

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        yield _Icon(self.app.setting)
        yield _Title(self.app.setting)
        yield HeaderClock()
