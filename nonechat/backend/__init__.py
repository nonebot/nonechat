from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Union

from textual.widget import Widget
from textual.message import Message

from .storage import MessageStorage
from ..model import DIRECT, User, Event, Robot, Channel, StateChange, MessageEvent

if TYPE_CHECKING:
    from ..app import Frontend


class UserAdd(Message, bubble=False):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.user = user


class ChannelAdd(Message, bubble=False):
    def __init__(self, channel: Channel) -> None:
        super().__init__()
        self.channel = channel


class Backend(ABC):
    frontend: "Frontend"
    storage: "MessageStorage"

    def __init__(self, frontend: "Frontend"):
        self.frontend = frontend
        self.bot = Robot(
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

    @property
    def is_direct(self) -> bool:
        return self.current_channel.id == DIRECT.id

    async def get_users(self) -> list[User]:
        return self.storage.users

    async def get_channels(self) -> list[Channel]:
        return self.storage.channels

    async def get_chat_history(self, target: Union[Channel, User, None] = None) -> list[MessageEvent]:
        if target is None:
            return self.storage.chat_history(self.current_user if self.is_direct else self.current_channel)
        return self.storage.chat_history(self.current_user if target.id == DIRECT.id else target)

    def set_user(self, user: User):
        self.current_user = user

    def set_channel(self, channel: Channel):
        self.current_channel = channel

    def add_user_watcher(self, watcher: Widget) -> None:
        self.user_watchers.append(watcher)

    def remove_user_watcher(self, watcher: Widget) -> None:
        self.user_watchers.remove(watcher)

    def add_channel_watcher(self, watcher: Widget) -> None:
        self.channel_wathers.append(watcher)

    def remove_channel_watcher(self, watcher: Widget) -> None:
        self.channel_wathers.remove(watcher)

    async def add_user(self, user: User):
        self.storage.add_user(user)
        for watcher in self.user_watchers:
            watcher.post_message(UserAdd(user))

    async def add_channel(self, channel: Channel):
        self.storage.add_channel(channel)
        for watcher in self.channel_wathers:
            watcher.post_message(ChannelAdd(channel))

    async def write_chat(self, message: "MessageEvent", target: Union[Channel, User]):
        self.storage.write_chat(message, target)
        self.emit_chat_watcher(message)

    async def clear_chat_history(self, target: Union[Channel, User, None] = None):
        if target is None:
            self.storage.clear_chat_history(self.current_user if self.is_direct else self.current_channel)
        else:
            self.storage.clear_chat_history(self.current_user if target.id == DIRECT.id else target)
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
