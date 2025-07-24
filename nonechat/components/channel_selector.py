import random
import string
from datetime import datetime
from typing import TYPE_CHECKING, Optional, cast

from textual.widget import Widget
from textual.message import Message
from textual.widgets import Label, ListItem, ListView

from ..model import DIRECT, User, Channel, StateChange, MessageEvent

if TYPE_CHECKING:
    from ..app import Frontend, BotModeChanged


class ChannelSelectorPressed(Message):
    """频道选择器按钮被按下时发送的消息"""

    def __init__(self, channel: Channel, orig_user: Optional[User]) -> None:
        super().__init__()
        self.channel = channel
        self.orig_user = orig_user  # 原始用户，用于私聊频道的处理


class _store:
    """存储当前用户的状态"""

    check_record: dict[str, float] = {}  # 用于记录频道的最后活动时间
    current_channel: Channel = DIRECT  # 默认频道为 DIRECT


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

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        yield ListView(id="channel-list")

    async def on_mount(self):
        _store.current_channel = self.app.backend.current_channel
        await self.update_channel_list()
        self.app.backend.add_channel_watcher(self)
        self.app.bot_mode_watchers.append(self)
        self.app.backend.add_chat_watcher(self)

    def on_unmount(self):
        self.app.backend.remove_channel_watcher(self)
        self.app.bot_mode_watchers.remove(self)
        self.app.backend.remove_chat_watcher(self)

    async def on_state_change(self, event: "StateChange[tuple[MessageEvent, ...]]"):
        await self.update_channel_list()

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

        channels_times = [
            (
                channel,
                (
                    event.time.timestamp()
                    if (event := await self.app.backend.get_latest_chat(channel))
                    else channel._created_at.timestamp()
                ),
            )
            for channel in await self.app.backend.list_channels(list_users=self.is_bot_mode)
        ]
        for channel, time in sorted(channels_times, key=lambda x: x[1], reverse=True):
            color = "auto"
            if channel.id not in _store.check_record:
                _store.check_record[channel.id] = datetime.now().timestamp()
                if time != channel._created_at.timestamp():
                    color = (
                        "auto"
                        if _store.current_channel and channel.id == _store.current_channel.id
                        else "lime blink"
                    )
            elif time > _store.check_record[channel.id]:
                color = (
                    "auto"
                    if _store.current_channel and channel.id == _store.current_channel.id
                    else "lime blink"
                )

            if channel.id.startswith("private:"):
                if not self.is_bot_mode:
                    label = Label(f"{DIRECT.avatar} [{color}]{DIRECT.name}[/]", id="label-dm-direct")
                    item = ListItem(label, id="channel-dm-direct")
                    channel = DIRECT  # 使用 DIRECT 作为私聊频道的标识
                    orig_user = None
                else:
                    label = Label(
                        f"{channel.avatar} [{color}]{channel.name}({channel.id[8:]})[/]",
                        id=f"label-dm-{channel.id[8:]}",
                    )
                    item = ListItem(label, id=f"channel-dm-{channel.id[8:]}")
                    orig_user = await self.app.backend.get_user(channel.id[8:])
            else:
                label = Label(f"{channel.avatar} [{color}]{channel.name}[/]", id=f"label-{channel.id}")
                item = ListItem(label, id=f"channel-{channel.id}")
                orig_user = None

            self.channel_items[channel.id] = (item, (channel, orig_user))
            await channel_list.append(item)
            if _store.current_channel and channel.id == _store.current_channel.id:
                item.highlighted = True

    async def on_list_view_selected(self, event: ListView.Selected):
        """处理列表项选择事件"""
        if event.item and event.item.id and event.item.id.startswith("channel-"):
            # 查找对应的频道
            for item, slots in self.channel_items.values():
                channel, orig_user = slots
                if channel.id == DIRECT.id:
                    ev = ChannelSelectorPressed(
                        await self.app.backend.create_dm(self.app.backend.current_user),
                        self.app.backend.current_user,
                    )
                else:
                    ev = ChannelSelectorPressed(channel, orig_user)
                if item == event.item:
                    key = (
                        f"dm-{channel.id[8:]}"
                        if channel.id.startswith("private:")
                        else ("dm-direct" if channel.id == DIRECT.id else channel.id)
                    )
                    label = self.query_one(f"#label-{key}", Label)
                    label.update(label.renderable.replace("lime blink", "auto"))  # type: ignore
                    self.post_message(ev)
                    item.highlighted = True
                    _store.current_channel = ev.channel
                else:
                    item.highlighted = False
                _store.check_record[ev.channel.id] = datetime.now().timestamp()  # 更新最后活动时间

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
