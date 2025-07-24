from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Union, Optional

from textual.widget import Widget
from textual.message import Message

from .storage import MessageStorage
from ..message import ConsoleMessage
from ..model import DIRECT, User, Event, Robot, Channel, StateChange, MessageEvent

if TYPE_CHECKING:
    from ..app import Frontend


class BotAdd(Message, bubble=False):
    def __init__(self, bot: User) -> None:
        super().__init__()
        self.bot = bot


class UserAdd(Message, bubble=False):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.user = user


class ChannelAdd(Message, bubble=False):
    def __init__(self, channel: Channel) -> None:
        super().__init__()
        self.channel = channel


class MessageDeleted(Message, bubble=False):
    def __init__(self, message_id: str, channel: Channel) -> None:
        super().__init__()
        self.message_id = message_id
        self.channel = channel


class MessageChanged(Message, bubble=False):
    def __init__(self, message_id: str, content: ConsoleMessage, channel: Channel) -> None:
        super().__init__()
        self.message_id = message_id
        self.channel = channel
        self.content = content


class Backend(ABC):
    frontend: "Frontend"
    storage: "MessageStorage"

    def __init__(self, frontend: "Frontend[Any]"):
        self.frontend = frontend
        self.current_bot = Robot(
            "robot",
            self.frontend.setting.bot_avatar,
            self.frontend.setting.bot_name,
        )
        self.storage = MessageStorage()
        self.current_user = User(
            "console", self.frontend.setting.user_avatar, self.frontend.setting.user_name
        )
        self.current_channel = Channel("general", "通用", "默认聊天频道", "💬")
        self.chat_watchers: list[Widget] = []
        self.user_watchers: list[Widget] = []
        self.channel_wathers: list[Widget] = []
        self.bot_watchers: list[Widget] = []

    @property
    def is_direct(self) -> bool:
        return self.current_channel.id.startswith("private:") or self.current_channel.id == DIRECT.id

    async def get_user(self, user_id: str) -> User:
        if user_id in self.storage.users:
            return self.storage.users[user_id]
        if user_id == self.current_user.id:
            return self.current_user
        raise ValueError(f"User with ID {user_id} not found in storage.")

    async def get_channel(self, channel_id: str) -> Channel:
        if channel_id in self.storage.channels:
            return self.storage.channels[channel_id]
        if channel_id == DIRECT.id:
            return DIRECT
        if channel_id == self.current_channel.id:
            return self.current_channel
        raise ValueError(f"Channel with ID {channel_id} not found in storage.")

    async def list_users(self) -> list[User]:
        return list(self.storage.users.values())

    async def list_channels(self, list_users: bool = False) -> list[Channel]:
        data = list(self.storage.channels.values())
        data.pop(0)
        users = [await self.create_dm(self.current_user)]
        if list_users:
            users += [
                await self.create_dm(user)
                for user in self.storage.users.values()
                if user.id != self.current_user.id
            ]
        users.sort(key=lambda x: x._created_at.timestamp(), reverse=True)
        return users + data

    async def create_dm(self, user: User):
        chl = Channel(f"private:{user.id}", user.nickname, "", user.avatar)
        chl._created_at = user._created_at
        return chl

    async def list_bots(self) -> list[User]:
        return list(self.storage.bots.values())

    async def get_chat_history(self, channel: Union[Channel, None] = None) -> list[MessageEvent]:
        _target = (
            await self.create_dm(self.current_user)
            if (channel or self.current_channel).id == DIRECT.id
            else (channel or self.current_channel)
        )
        return self.storage.chat_history(_target)

    async def get_latest_chat(self, channel: Union[Channel, None] = None) -> Optional[MessageEvent]:
        """获取当前频道的最新聊天消息"""
        history = await self.get_chat_history(channel)
        return history[-1] if history else None

    async def get_chat(self, message_id: str, channel: Union[Channel, None] = None) -> Optional[MessageEvent]:
        """获取指定消息ID的聊天消息"""
        _target = (
            await self.create_dm(self.current_user)
            if (channel or self.current_channel).id == DIRECT.id
            else (channel or self.current_channel)
        )
        return self.storage.get_chat(message_id, _target)

    def set_user(self, user: User):
        self.current_user = user

    def set_channel(self, channel: Channel):
        self.current_channel = channel

    def set_bot(self, bot: Robot):
        self.current_bot = bot

    def add_user_watcher(self, watcher: Widget) -> None:
        self.user_watchers.append(watcher)

    def remove_user_watcher(self, watcher: Widget) -> None:
        self.user_watchers.remove(watcher)

    def add_channel_watcher(self, watcher: Widget) -> None:
        self.channel_wathers.append(watcher)

    def remove_channel_watcher(self, watcher: Widget) -> None:
        self.channel_wathers.remove(watcher)

    def add_bot_watcher(self, watcher: Widget) -> None:
        self.bot_watchers.append(watcher)

    def remove_bot_watcher(self, watcher: Widget) -> None:
        self.bot_watchers.remove(watcher)

    async def add_user(self, user: User):
        if self.storage.add_user(user):
            for watcher in self.user_watchers:
                watcher.post_message(UserAdd(user))

    async def add_channel(self, channel: Channel):
        if self.storage.add_channel(channel):
            for watcher in self.channel_wathers:
                watcher.post_message(ChannelAdd(channel))

    async def add_bot(self, bot: Robot):
        if self.storage.add_bot(bot):
            for watcher in self.bot_watchers:
                watcher.post_message(BotAdd(bot))

    async def write_chat(self, message: "MessageEvent", channel: Channel):
        msg_id = self.storage.write_chat(message, channel)
        self.emit_chat_watcher(message)
        return msg_id

    async def remove_chat(self, message_id: str, channel: Channel):
        self.storage.remove_chat(message_id, channel)
        for watcher in self.chat_watchers:
            watcher.post_message(MessageDeleted(message_id, channel))

    async def edit_chat(self, message_id: str, content: ConsoleMessage, channel: Channel):
        if self.storage.edit_chat(message_id, content, channel):
            for watcher in self.chat_watchers:
                watcher.post_message(MessageChanged(message_id, content, channel))

    async def clear_chat_history(self, channel: Union[Channel, None] = None):
        _target = (
            await self.create_dm(self.current_user)
            if (channel or self.current_channel).id == DIRECT.id
            else (channel or self.current_channel)
        )
        self.storage.clear_chat_history(_target)
        self.emit_chat_watcher()

    def add_chat_watcher(self, watcher: Widget) -> None:
        self.chat_watchers.append(watcher)

    def remove_chat_watcher(self, watcher: Widget) -> None:
        self.chat_watchers.remove(watcher)

    def emit_chat_watcher(self, *messages: "MessageEvent") -> None:
        for watcher in self.chat_watchers:
            watcher.post_message(StateChange(messages))

    @abstractmethod
    def on_console_load(self): ...

    @abstractmethod
    async def on_console_mount(self): ...

    @abstractmethod
    async def on_console_unmount(self): ...

    @abstractmethod
    async def post_event(self, event: Event): ...
