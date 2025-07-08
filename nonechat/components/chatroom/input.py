from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.widgets import Input
from textual.binding import Binding

if TYPE_CHECKING:
    from nonechat.app import Frontend


class InputBox(Widget):
    DEFAULT_CSS = """
    $input-background: rgba(0, 0, 0, 0);
    $input-border-type: round;
    $input-border-color: rgba(170, 170, 170, 0.7);
    $input-border-active-color: $accent;
    $input-border: $input-border-type $input-border-color;
    $input-border-active: $input-border-type $input-border-active-color;

    InputBox {
        layout: horizontal;
        height: auto;
        width: 100%;
    }

    InputBox > Input {
        padding: 0 1;
        background: $input-background;
        border: $input-border !important;
    }
    InputBox > Input:focus {
        border: $input-border-active !important;
    }
    """

    BINDINGS = [
        Binding("escape", "blur", "Reset focus", show=False),
        Binding("up", "set_previous_input", "Set Previous Input"),
        Binding("down", "set_next_input", "Set Next Input"),
    ]

    def __init__(self):
        super().__init__()
        self.input = Input(placeholder="Send Message")
        self.input_history = []
        self.history_index = 0

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        yield self.input

    async def on_input_submitted(self, event: Input.Submitted):
        event.stop()
        if event.value == "":
            return
        if not self.input_history:
            self.input_history.append(event.value)
        elif self.input_history[-1] != event.value:
            self.input_history.append(event.value)
        self.history_index = len(self.input_history)
        self.input.value = ""
        await self.app.action_post_message(event.value)

    def action_blur(self):
        self.input.blur()

    async def action_set_previous_input(self):
        if not self.input_history:
            return
        self.history_index -= 1
        if self.history_index < 0:
            self.history_index = 0
        self.input.value = self.input_history[self.history_index]

    async def action_set_next_input(self):
        if not self.input_history:
            return
        self.history_index += 1
        if self.history_index >= len(self.input_history):
            self.input.value = ""
            self.history_index = len(self.input_history) - 1
            return
        self.input.value = self.input_history[self.history_index]
