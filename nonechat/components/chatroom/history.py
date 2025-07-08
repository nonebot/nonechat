from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional, cast

from textual.widget import Widget

from .message import Timer, Message

if TYPE_CHECKING:
    from nonechat.app import Frontend
    from nonechat.model import MessageEvent
    from nonechat.storage import Storage, StateChange


class ChatHistory(Widget):
    DEFAULT_CSS = """
    ChatHistory {
        layout: vertical;
        height: 100%;
        overflow: hidden scroll;
        scrollbar-size-vertical: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.last_msg: Optional[MessageEvent] = None
        self.last_time: Optional[datetime] = None

    @property
    def storage(self) -> "Storage":
        return cast("Frontend", self.app).storage

    async def on_mount(self):
        await self.on_new_message(self.storage.chat_history)
        self.storage.add_chat_watcher(self)

    def on_unmount(self):
        self.storage.remove_chat_watcher(self)

    async def action_new_message(self, message: "MessageEvent"):
        if (
            not self.last_time
            or message.time - self.last_time > timedelta(minutes=5)
            or (self.last_msg and message.time - self.last_msg.time > timedelta(minutes=1))
        ):
            self.mount(Timer(message.time))  # noqa
            self.last_time = message.time
        await self.mount(Message(message))
        self.last_msg = message

        self.scroll_end()

    async def on_state_change(self, event: "StateChange[tuple[MessageEvent, ...]]"):
        await self.on_new_message(event.data)

    async def on_new_message(self, messages: Iterable["MessageEvent"]):
        for message in messages:
            if message.channel == self.storage.current_channel:
                await self.action_new_message(message)

    def action_clear_history(self):
        self.last_msg = None
        self.last_time = None
        for msg in self.walk_children():
            cast(Widget, msg).remove()
        self.storage.clear_chat_history()

    async def refresh_history(self):
        """刷新聊天历史记录显示"""
        # 清除当前显示的消息
        self.last_msg = None
        self.last_time = None
        for msg in self.walk_children():
            await cast(Widget, msg).remove()

        # 重新加载当前频道的历史记录
        await self.on_new_message(self.storage.chat_history)
