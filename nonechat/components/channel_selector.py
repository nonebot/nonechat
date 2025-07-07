from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.message import Message
from textual.containers import Vertical
from textual.widgets import Button, Static

from ..storage import Channel

if TYPE_CHECKING:
    from ..app import Frontend


class ChannelSelectorPressed(Message):
    """频道选择器按钮被按下时发送的消息"""

    def __init__(self, channel: Channel) -> None:
        super().__init__()
        self.channel = channel


class ChannelSelector(Widget):
    """频道选择器组件"""

    DEFAULT_CSS = """
    ChannelSelector {
        layout: vertical;
        height: auto;
        width: 100%;
        border: round rgba(170, 170, 170, 0.7);
        padding: 1;
        margin: 1;
        max-height: 15;
        overflow-y: auto;
    }

    ChannelSelector .title {
        height: 1;
        width: 100%;
        text-align: center;
        text-style: bold;
        color: green;
        margin-bottom: 1;
    }

    ChannelSelector .channel-list {
        layout: vertical;
        height: auto;
        width: 100%;
    }

    ChannelSelector .channel-button {
        width: 100%;
        margin-bottom: 1;
        text-align: center;
    }

    ChannelSelector .channel-button.current {
        background: darkgreen;
        color: white;
    }

    ChannelSelector .add-channel-button {
        width: 100%;
        margin-top: 1;
        background: darkblue;
        color: white;
    }
    """

    def __init__(self):
        super().__init__()
        self.channel_buttons = {}

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        yield Static("📺 频道列表", classes="title")
        yield Vertical(classes="channel-list", id="channel-list")
        yield Button("➕ 添加频道", classes="add-channel-button", id="add-channel")

    def on_mount(self):
        self.update_channel_list()

    def update_channel_list(self):
        """更新频道列表"""
        channel_list = self.query_one("#channel-list")

        for channel in self.app.storage.channels:
            if channel.id in self.channel_buttons:
                button = self.channel_buttons[channel.id][0]
            else:
                button = Button(
                    f"{channel.emoji} {channel.name}", classes="channel-button", id=f"channel-{channel.id}"
                )
                self.channel_buttons[channel.id] = (button, channel)
                channel_list.mount(button)

            # 标记当前频道
            if self.app.storage.current_channel and channel.id == self.app.storage.current_channel.id:
                button.add_class("current")
            else:
                button.remove_class("current")

    async def on_button_pressed(self, event: Button.Pressed):
        """处理按钮点击事件"""
        if event.button.id == "add-channel":
            await self._add_new_channel()
        elif event.button.id and event.button.id.startswith("channel-"):
            # 查找对应的频道
            for button, channel in self.channel_buttons.values():
                if button == event.button:
                    self.post_message(ChannelSelectorPressed(channel))
                    break

    async def _add_new_channel(self):
        """添加新频道的逻辑"""
        import random
        import string

        # 生成随机频道ID
        channel_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))

        # 一些预设的频道
        emojis = ["💬", "🎮", "🎵", "📚", "🎯", "🏆", "🚀", "🌟", "🔥", "💡"]
        names = [
            "随机讨论",
            "游戏频道",
            "音乐分享",
            "学习讨论",
            "技术交流",
            "项目讨论",
            "闲聊",
            "问答",
            "分享",
            "创意",
        ]

        new_channel = Channel(
            id=channel_id,
            name=random.choice(names),
            emoji=random.choice(emojis),
            description="自动生成的频道",
        )

        self.app.storage.add_channel(new_channel)
        self.update_channel_list()
