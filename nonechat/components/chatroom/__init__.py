from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.binding import Binding

from .input import InputBox
from .toolbar import Toolbar
from .history import ChatHistory

if TYPE_CHECKING:
    from ...app import Frontend


class ChatRoom(Widget):
    DEFAULT_CSS = """
    ChatRoom {
        layout: vertical;
    }
    ChatRoom > Toolbar {
        dock: top;
    }
    ChatRoom > InputBox {
        dock: bottom;
    }
    """

    BINDINGS = [Binding("ctrl+l", "clear_history", "Clear chat history")]

    def __init__(self):
        super().__init__()
        self.history = ChatHistory()

    def compose(self):
        yield Toolbar(self.app.setting)
        yield self.history
        yield InputBox()

    def action_clear_history(self):
        self.history.action_clear_history()

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)
