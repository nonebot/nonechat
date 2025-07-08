from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.message import Message
from textual.widgets import TabPane, TabbedContent

from .user_selector import UserSelector, UserSelectorPressed
from .channel_selector import ChannelSelector, ChannelSelectorPressed

if TYPE_CHECKING:
    from ..app import Frontend


class SidebarUserChanged(Message):
    """侧边栏用户更改消息"""

    def __init__(self, user) -> None:
        super().__init__()
        self.user = user


class SidebarChannelChanged(Message):
    """侧边栏频道更改消息"""

    def __init__(self, channel) -> None:
        super().__init__()
        self.channel = channel
        self.direct = channel.id == "_direct"


class Sidebar(Widget):
    """侧边栏组件，包含用户和频道选择器"""

    DEFAULT_CSS = """
    Sidebar {
        width: 25%;
        height: 100%;
        border-right: solid rgba(170, 170, 170, 0.7);
    }

    TabPane {
        padding: 0;
    }

    UserSelector, ChannelSelector {
        margin: 1 0 0 0;
        border: none;
        max-height: 100%;
    }
    """

    def __init__(self):
        super().__init__()
        self.user_selector = UserSelector()
        self.channel_selector = ChannelSelector()

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        with TabbedContent():
            with TabPane("👥 用户列表", id="users"):
                yield self.user_selector
            with TabPane("📺 频道列表", id="channels"):
                yield self.channel_selector

    def on_user_selector_pressed(self, event: UserSelectorPressed):
        """处理用户选择事件"""
        # 更新当前用户
        self.app.storage.set_user(event.user)

        # 更新用���选择器显示
        # self.user_selector.update_user_list()

        # 向父组件发送消息
        self.post_message(SidebarUserChanged(event.user))

    def on_channel_selector_pressed(self, event: ChannelSelectorPressed):
        """处理频道选择事件"""
        # 更新当前频道
        self.app.storage.set_channel(event.channel)

        # 更新频道选择器显示
        # self.channel_selector.update_channel_list()

        # 向父组件发送消息
        self.post_message(SidebarChannelChanged(event.channel))

    async def update_displays(self):
        """更新显示"""
        await self.user_selector.update_user_list()
        await self.channel_selector.update_channel_list()
