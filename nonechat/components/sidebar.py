from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.message import Message
from textual.containers import Vertical
from textual.widgets import Button, TabPane, TabbedContent

from .user_selector import UserSelector, UserSelectorPressed
from .channel_selector import ChannelSelector, ChannelSelectorPressed

if TYPE_CHECKING:
    from ..app import Frontend, BotModeChanged


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
        layout: vertical;
    }

    TabbedContent {
        height: 100%;
    }

    TabPane {
        padding: 0;
        layout: vertical;
        height: 100%;
    }

    .selector-container {
        height: 1fr;
        layout: vertical;
    }

    .button-container {
        height: auto;
        layout: vertical;
        margin: 1 0;
        align-horizontal: center;
    }

    UserSelector, ChannelSelector {
        margin: 1 0 0 0;
        height: 1fr;
    }

    .add-button {
        background: darkgreen;
        color: white;
    }
    """

    def __init__(self):
        super().__init__()
        self.user_selector = UserSelector()
        self.channel_selector = ChannelSelector()
        self.is_bot_mode = self.app.is_bot_mode
        self.app.bot_mode_watchers.append(self)

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        with TabbedContent():
            with TabPane("👥 用户列表", id="users"):
                with Vertical(classes="selector-container"):
                    yield self.user_selector
                with Vertical(classes="button-container"):
                    yield Button("➕ 添加用户", id="add-user", classes="add-button")
            with TabPane("📺 频道列表", id="channels"):
                with Vertical(classes="selector-container"):
                    yield self.channel_selector
                with Vertical(classes="button-container"):
                    yield Button("➕ 添加频道", id="add-channel", classes="add-button")

    async def on_bot_mode_changed(self, event: "BotModeChanged"):
        """处理模式切换"""
        self.is_bot_mode = event.is_bot_mode

        add_user_btn = self.query_one("#add-user", Button)
        # 更新添加用户按钮状态
        if self.is_bot_mode:
            add_user_btn.label = "➕ 添加机器人"
        else:
            add_user_btn.label = "➕ 添加用户"

        # 更新添加频道按钮状态
        add_channel_btn = self.query_one("#add-channel", Button)
        if self.is_bot_mode:
            add_channel_btn.disabled = True
            add_channel_btn.label = "--"
        else:
            add_channel_btn.disabled = False
            add_channel_btn.label = "➕ 添加频道"

    async def on_button_pressed(self, event: Button.Pressed):
        """处理按钮点击事件"""
        if event.button.id == "add-user":
            await self.user_selector.add_new_user()
        elif event.button.id == "add-channel":
            await self.channel_selector.add_new_channel()

    def on_user_selector_pressed(self, event: UserSelectorPressed):
        """处理用户选择事件"""
        # 更新当前用户
        if self.is_bot_mode:
            self.app.backend.set_bot(event.user)  # type: ignore
        else:
            self.app.backend.set_user(event.user)

        # 更新用户选择器显示
        # self.user_selector.update_user_list()

        # 向父组件发送消息
        self.post_message(SidebarUserChanged(event.user))

    def on_channel_selector_pressed(self, event: ChannelSelectorPressed):
        """处理频道选择事件"""
        # 更新当前频道
        self.app.backend.set_channel(event.channel)
        if event.orig_user:
            self.app.backend.set_user(event.orig_user)

        # 更新频道选择器显示
        # self.channel_selector.update_channel_list()

        # 向父组件发送消息
        self.post_message(SidebarChannelChanged(event.channel))

    async def update_displays(self):
        """更新显示"""
        await self.user_selector.update_user_list()
        await self.channel_selector.update_channel_list()
