from typing import TYPE_CHECKING, cast

from textual.events import Resize
from textual.widget import Widget
from textual.reactive import Reactive

from ..components.log import LogPanel
from ..components.chatroom import ChatRoom
from ..components.sidebar import Sidebar, SidebarUserChanged, SidebarChannelChanged

if TYPE_CHECKING:
    from ..app import Frontend

SHOW_LOG_BREAKPOINT = 120


class HorizontalView(Widget):
    DEFAULT_CSS = """
    HorizontalView {
        layout: horizontal;
        height: 100%;
        width: 100%;
    }

    HorizontalView > Sidebar {
        width: 25%;
        height: 100%;
        min-width: 20;
    }

    HorizontalView > ChatRoom {
        width: 75%;
        height: 100%;
    }

    HorizontalView > LogPanel {
        width: 25%;
        height: 100%;
        border-left: solid rgba(204, 204, 204, 0.7);
        display: none;
    }

    HorizontalView.-show-log > ChatRoom {
        width: 50%;
    }

    HorizontalView.-show-log > Sidebar {
        width: 25%;
    }

    HorizontalView.-show-log > LogPanel {
        width: 25%;
        display: block;
    }
    """

    can_show_log: Reactive[bool] = Reactive(False)
    show_log: Reactive[bool] = Reactive(True)

    def __init__(self):
        super().__init__()
        # setting = self.app.setting
        self.sidebar = Sidebar()
        self.chatroom = ChatRoom()
        self.log_panel = LogPanel()
        # if setting.bg_color:
        #     self.styles.background = setting.bg_color

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        yield self.sidebar
        yield self.chatroom
        yield self.log_panel

    def on_resize(self, event: Resize):
        self.responsive(event.size.width)

    async def on_sidebar_user_changed(self, event: SidebarUserChanged):
        """处理用户切换事件"""
        # 刷新聊天室显示
        await self.chatroom.history.refresh_history()

        if self.app.storage.is_direct:
            self.chatroom.toolbar.center_title.update(self.app.storage.current_user.nickname)

    async def on_sidebar_channel_changed(self, event: SidebarChannelChanged):
        """处理频道切换事件"""
        # 刷新聊天室显示
        await self.chatroom.history.refresh_history()

        # 更新工具栏标题
        if event.direct:
            self.chatroom.toolbar.center_title.update(self.app.storage.current_user.nickname)
        else:
            self.chatroom.toolbar.center_title.update(event.channel.name)

    def watch_can_show_log(self, can_show_log: bool):
        self._toggle_log_panel()

    def watch_show_log(self, show_log: bool):
        self._toggle_log_panel()

    def responsive(self, width: int) -> None:
        self.can_show_log = width > SHOW_LOG_BREAKPOINT  # type: ignore

    def action_toggle_log_panel(self):
        self.show_log = not self.show_log  # type: ignore

    def _toggle_log_panel(self):
        show = self.can_show_log and self.show_log
        self.log_panel.display = show
        self.set_class(show, "-show-log")
