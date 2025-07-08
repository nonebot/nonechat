import random
import string
from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.message import Message
from textual.widgets import Label, Button, ListItem, ListView

from ..model import Channel

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
    }

    ChannelSelector ListView {
        height: auto;
        width: 100%;
        max-height: 85%;
    }

    ChannelSelector ListItem {
        width: 100%;
        margin: 1;
        padding: 1;
        text-align: center;
    }

    ChannelSelector .add-channel-button {
        width: 100%;
        margin-top: 1;
        background: darkgreen;
        color: white;
    }
    """

    def __init__(self):
        super().__init__()
        self.channel_items: dict[str, tuple[ListItem, Channel]] = {}

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        yield ListView(id="channel-list")
        yield Button("➕ 添加频道", classes="add-channel-button", id="add-channel")

    async def on_mount(self):
        await self.update_channel_list()

    async def update_channel_list(self):
        """更新频道列表"""
        channel_list = self.query_one("#channel-list", ListView)
        await channel_list.clear()
        self.channel_items.clear()

        # 假设从 storage 中获取频道列表
        if hasattr(self.app.storage, "channels"):
            for channel in self.app.storage.channels:
                label = Label(f"{channel.avatar} {channel.name}")
                item = ListItem(label, id=f"channel-{channel.id}")
                self.channel_items[channel.id] = (item, channel)
                await channel_list.append(item)

                # 标记当前频道
                if (
                    hasattr(self.app.storage, "current_channel")
                    and channel.id == self.app.storage.current_channel.id
                ):
                    item.add_class("current")
                else:
                    item.remove_class("current")

    async def on_button_pressed(self, event: Button.Pressed):
        """处理按钮点击事件"""
        if event.button.id == "add-channel":
            await self._add_new_channel()

    async def on_list_view_selected(self, event: ListView.Selected):
        """处理列表项选择事件"""
        if event.item and event.item.id and event.item.id.startswith("channel-"):
            # 查找对应的频道
            for item, channel in self.channel_items.values():
                if item == event.item:
                    self.post_message(ChannelSelectorPressed(channel))
                    break

    async def _add_new_channel(self):
        """添加新频道的逻辑"""

        # 生成随机频道ID
        channel_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))

        # 一些预设的频道
        emojis = ["💬", "📢", "🎮", "🎵", "📚", "💻", "🎨", "🌍", "🔧", "⚡"]
        names = ["通用", "公告", "游戏", "音乐", "学习", "技术", "艺术", "世界", "工具", "闪电"]

        new_channel = Channel(
            id=channel_id,
            name=random.choice(names),
            avatar=random.choice(emojis),
            description=f"这是一个{random.choice(names)}频道",
        )

        # 假设 storage 有添加频道的方法
        if hasattr(self.app.storage, "add_channel"):
            self.app.storage.add_channel(new_channel)
        await self.update_channel_list()
