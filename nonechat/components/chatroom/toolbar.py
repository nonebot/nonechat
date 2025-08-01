from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.reactive import Reactive

from nonechat.router import RouteChange

from ..action import Action

if TYPE_CHECKING:
    from nonechat.app import Frontend
    from nonechat.views.horizontal import HorizontalView

    from .history import ChatHistory


class RoomTitle(Widget):
    title: Reactive[str] = Reactive("Chat")

    def render(self):
        return self.title


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

    Toolbar RoomTitle {
        width: 100%;
        content-align: center middle;
    }

    Toolbar Action {
        width: 3;
    }
    Toolbar Action.ml {
        margin-left: 4;
    }
    Toolbar Action.mr {
        margin-right: 4;
    }
    """
    title: Reactive[str] = Reactive("Chat")

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def __init__(self):
        super().__init__()
        setting = self.app.setting
        self.toggle_sidebar_button = Action(setting.toolbar_fold, id="toggle-sidebar", classes="left")
        self.exit_button = Action(setting.toolbar_exit, id="exit", classes="left ml")

        self.center_title = RoomTitle()
        # self.settings_button = Action(setting.toolbar_setting, id="settings", classes="right mr")
        self.clear_button = Action(setting.toolbar_clear, id="clear", classes="right mr")
        self.log_button = Action(setting.toolbar_log, id="log", classes="right")

    def compose(self):
        yield self.exit_button
        yield self.toggle_sidebar_button

        yield self.center_title.data_bind(Toolbar.title)

        # yield self.settings_button
        yield self.clear_button
        yield self.log_button

    async def on_action_pressed(self, event: Action.Pressed):
        event.stop()
        if event.action == self.exit_button:
            self.app.exit()
        elif event.action == self.clear_button:
            history: ChatHistory = cast("ChatHistory", self.app.query_one("ChatHistory"))
            await history.action_clear_history()
        elif event.action == self.toggle_sidebar_button:
            view: HorizontalView = cast("HorizontalView", self.app.query_one("HorizontalView"))
            view.action_toggle_sidebar()
            if view.show_sidebar:
                self.toggle_sidebar_button.update(self.app.setting.toolbar_fold)
            else:
                self.toggle_sidebar_button.update(self.app.setting.toolbar_expand)
        # elif event.action == self.settings_button:
        #     ...
        elif event.action == self.log_button:
            view: HorizontalView = cast("HorizontalView", self.app.query_one("HorizontalView"))
            if view.can_show_log:
                view.action_toggle_log_panel()
            else:
                self.post_message(RouteChange("log"))  # noqa
