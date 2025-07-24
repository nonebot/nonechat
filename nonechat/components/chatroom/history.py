from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional, cast

from textual.widget import Widget

from nonechat.message import Markup, ConsoleMessage

from .message import Timer, Message

if TYPE_CHECKING:
    from nonechat.app import Frontend, BotModeChanged
    from nonechat.backend import MessageChanged, MessageDeleted
    from nonechat.model import Channel, StateChange, MessageEvent


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
        self.is_bot_mode = self.app.is_bot_mode

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    async def on_mount(self):
        await self.on_new_message(await self.app.backend.get_chat_history())
        self.app.backend.add_chat_watcher(self)
        self.app.bot_mode_watchers.append(self)

    def on_unmount(self):
        self.app.backend.remove_chat_watcher(self)
        self.app.bot_mode_watchers.remove(self)

    async def on_bot_mode_changed(self, event: "BotModeChanged"):
        self.is_bot_mode = event.is_bot_mode
        await self.refresh_history()

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
        if self.is_bot_mode and message.user.id == self.app.backend.current_bot.id:
            self.scroll_end(animate=True)
        elif message.user.id != self.app.backend.current_bot.id:
            self.scroll_end(animate=True)

    async def on_state_change(self, event: "StateChange[tuple[MessageEvent, ...]]"):
        await self.on_new_message(event.data)

    async def on_new_message(self, messages: Iterable["MessageEvent"]):
        for message in messages:
            if message.channel.id == self.app.backend.current_channel.id:
                await self.action_new_message(message)

    async def action_clear_history(self):
        self.last_msg = None
        self.last_time = None
        for msg in self.walk_children():
            await cast(Widget, msg).remove()
        await self.app.backend.clear_chat_history()

    async def refresh_history(self, channel: "Optional[Channel]" = None):
        """刷新聊天历史记录显示"""
        # 清除当前显示的消息
        self.last_msg = None
        self.last_time = None
        for msg in self.walk_children():
            await cast(Widget, msg).remove()

        # 重新加载当前频道的历史记录
        await self.on_new_message(await self.app.backend.get_chat_history(channel))

    def on_message_deleted(self, event: "MessageDeleted"):
        for msg in self.walk_children():
            if isinstance(msg, Message) and msg.event.message_id == event.message_id:
                msg.content = ConsoleMessage([Markup("该消息已撤回", style="dim")])
                msg.refresh(layout=True, recompose=True)

    def on_message_changed(self, event: "MessageChanged"):
        for msg in self.walk_children():
            if isinstance(msg, Message) and msg.event.message_id == event.message_id:
                msg.content = event.content
                msg.refresh(layout=True, recompose=True)
