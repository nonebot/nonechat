from textual.widget import Widget
from textual.widgets import Static

from nonechat.router import RouteChange
from nonechat.setting import ConsoleSetting

from ..action import Action


class Toolbar(Widget):
    DEFAULT_CSS = """
    $toolbar-border-type: round;
    $toolbar-border-color: rgba(170, 170, 170, 0.7);
    $toolbar-border: $toolbar-border-type $toolbar-border-color;

    Toolbar {
        layout: horizontal;
        height: 3;
        width: 100%;
        border: $toolbar-border;
        padding: 0 1;
    }

    Toolbar Static {
        width: 100%;
        content-align: center middle;
    }

    Toolbar Action {
        width: 3;
    }
    Toolbar Action.ml {
        margin-left: 4;
    }
    """

    def __init__(self, settings: ConsoleSetting):
        super().__init__()
        self.exit_button = Action(settings.toolbar_exit, id="exit", classes="left ml")
        self.back_button = Action(settings.toolbar_expand, id="back", classes="left")
        # self.settings_button = Action(settings.toolbar_setting, id="settings", classes="right")

    def compose(self):
        yield self.exit_button
        yield self.back_button
        yield Static("Log", classes="center")
        # yield self.settings_button

    async def on_action_pressed(self, event: Action.Pressed):
        event.stop()
        if event.action == self.exit_button:
            self.app.exit()
        if event.action == self.back_button:
            self.post_message(RouteChange("main"))
        # elif event.action == self.settings_button:
        #     ...
