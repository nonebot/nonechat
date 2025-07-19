import random
import string
from typing import TYPE_CHECKING, Optional, cast

from textual.widget import Widget
from textual.message import Message
from textual.widgets import Label, ListItem, ListView

from ..model import DIRECT, User, Channel

if TYPE_CHECKING:
    from ..app import Frontend, BotModeChanged


class ChannelSelectorPressed(Message):
    """频道选择器按钮被按下时发送的消息"""

    def __init__(self, channel: Channel, orig_user: Optional[User]) -> None:
        super().__init__()
        self.channel = channel
        self.orig_user = orig_user  # 原始用户，用于私聊频道的处理


class ChannelSelector(Widget):
    """频道选择器组件"""

    DEFAULT_CSS = """
    ChannelSelector {
        layout: vertical;
        height: 100%;
        width: 100%;
        padding: 0 1;
    }

    ChannelSelector ListView {
        height: 1fr;
        width: 100%;
    }

    ChannelSelector ListItem {
        width: 100%;
        margin: 1;
        text-align: center;
    }
    """

    def __init__(self):
        super().__init__()
        self.channel_items: dict[str, tuple[ListItem, tuple[Channel, Optional[User]]]] = {}
        self.is_bot_mode = self.app.is_bot_mode
        self.app.bot_mode_watchers.append(self)

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        yield ListView(id="channel-list")

    async def on_mount(self):
        await self.update_channel_list()
        self.app.backend.add_channel_watcher(self)

    def on_unmount(self):
        self.app.backend.remove_channel_watcher(self)

    async def on_channel_add(self, event):
        await self.update_channel_list()

    async def on_bot_mode_changed(self, event: "BotModeChanged"):
        """处理模式切换"""
        self.is_bot_mode = event.is_bot_mode
        await self.update_channel_list()

    async def update_channel_list(self):
        """更新频道列表"""
        channel_list = self.query_one("#channel-list", ListView)
        await channel_list.clear()
        self.channel_items.clear()

        if self.is_bot_mode:
            # Bot 模式：显示用户私聊频道
            users = await self.app.backend.get_users()
            for user in users:
                label = Label(f"{user.avatar} {user.nickname}({user.id})")
                item = ListItem(label, id=f"channel-dm-{user.id}")
                # 使用特殊的 channel 来表示用户私聊
                fake_channel = Channel(f"private:{user.id}", user.nickname, "", user.avatar)
                self.channel_items[f"dm_{user.id}"] = (item, (fake_channel, user))
                await channel_list.append(item)

                # 在 bot 模式下，如果当前是 DIRECT 且当前用户是这个用户，则标记为当前
                if (
                    self.app.backend.current_channel.id == DIRECT.id
                    and user.id == self.app.backend.current_user.id
                ):
                    item.add_class("current")
                else:
                    item.remove_class("current")
        # 普通模式：显示频道列表
        for channel in await self.app.backend.get_channels():
            label = Label(f"{channel.avatar} {channel.name}")
            item = ListItem(label, id=f"channel-{channel.id}")
            if channel.id == DIRECT.id:
                if self.is_bot_mode:
                    continue
                channel = Channel(
                    f"private:{self.app.backend.current_user.id}",
                    self.app.backend.current_user.nickname,
                    "",
                    self.app.backend.current_user.avatar,
                )
            self.channel_items[channel.id] = (
                item,
                (channel, self.app.backend.current_user if channel.id.startswith("private:") else None),
            )
            await channel_list.append(item)

            # 标记当前频道
            if channel.id == self.app.backend.current_channel.id:
                item.add_class("current")
            else:
                item.remove_class("current")

    async def on_list_view_selected(self, event: ListView.Selected):
        """处理列表项选择事件"""
        if event.item and event.item.id:
            if event.item.id.startswith("channel-"):
                # 查找对应的频道
                for item, channel in self.channel_items.values():
                    if item == event.item:
                        self.post_message(ChannelSelectorPressed(*channel))
                        break

    async def add_new_channel(self):
        """添加新频道的逻辑"""
        # 在 Bot 模式下禁用添加频道功能
        if self.app.is_bot_mode:
            self.app.notify("Cannot add channels in bot mode", title="Action Disabled")
            return

        # 生成随机频道ID
        channel_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))

        # 一些预设的频道
        emojis = ["📢", "🎮", "🎵", "📚", "💻", "🎨", "🌍", "🔧", "⚡"]
        names = ["公告", "游戏", "音乐", "学习", "技术", "艺术", "世界", "工具", "闪电"]

        new_channel = Channel(
            id=channel_id,
            name=random.choice(names),
            avatar=random.choice(emojis),
            description=f"这是一个{random.choice(names)}频道",
        )

        # 假设 storage 有添加频道的方法
        await self.app.backend.add_channel(new_channel)
