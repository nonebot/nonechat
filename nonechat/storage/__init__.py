from dataclasses import field, dataclass
from typing import Union, Generic, TypeVar

from textual.widget import Widget
from textual.message import Message
from rich.console import RenderableType

from ..model import DIRECT, User, Channel, MessageEvent

MAX_LOG_RECORDS = 500
MAX_MSG_RECORDS = 500


T = TypeVar("T")


class StateChange(Message, Generic[T], bubble=False):
    def __init__(self, data: T) -> None:
        super().__init__()
        self.data = data


@dataclass
class Storage:
    current_user: User
    current_channel: Channel

    log_history: list[RenderableType] = field(default_factory=list)
    log_watchers: list[Widget] = field(default_factory=list)

    # 多用户和频道支持
    users: list[User] = field(default_factory=list)
    channels: list[Channel] = field(default_factory=list)

    # 按频道分组的聊天历史记录
    chat_history_by_channel: dict[str, list[MessageEvent]] = field(default_factory=dict)
    chat_history_by_user: dict[str, list[MessageEvent]] = field(default_factory=dict)
    chat_watchers: list[Widget] = field(default_factory=list)

    def __post_init__(self):
        self.channels.append(DIRECT)
        if self.current_channel not in self.channels:
            self.channels.append(self.current_channel)

        # 添加当前用户到用户列表
        if self.current_user not in self.users:
            self.users.append(self.current_user)

    @property
    def is_direct(self) -> bool:
        return self.current_channel == DIRECT

    @property
    def chat_history(self) -> list[MessageEvent]:
        """获取当前频道的聊天历史"""
        if self.current_channel == DIRECT:
            return self.chat_history_by_user.get(self.current_user.id, [])
        return self.chat_history_by_channel.get(self.current_channel.id, [])

    def set_user(self, user: User):
        """切换当前用户"""
        self.current_user = user
        if user not in self.users:
            self.users.append(user)

    def set_channel(self, channel: Channel):
        """切换当前频道"""
        self.current_channel = channel
        if channel not in self.channels:
            self.channels.append(channel)

    def add_user(self, user: User):
        """添加新用户"""
        if user not in self.users:
            self.users.append(user)

    def add_channel(self, channel: Channel):
        """添加新频道"""
        if channel not in self.channels:
            self.channels.append(channel)

    def write_log(self, *logs: RenderableType) -> None:
        self.log_history.extend(logs)
        if len(self.log_history) > MAX_LOG_RECORDS:
            self.log_history = self.log_history[-MAX_LOG_RECORDS:]
        self.emit_log_watcher(*logs)

    def add_log_watcher(self, watcher: Widget) -> None:
        self.log_watchers.append(watcher)

    def remove_log_watcher(self, watcher: Widget) -> None:
        self.log_watchers.remove(watcher)

    def emit_log_watcher(self, *logs: RenderableType) -> None:
        for watcher in self.log_watchers:
            watcher.post_message(StateChange(logs))

    def write_chat(self, message: "MessageEvent", target: Union[Channel, User]) -> None:
        if isinstance(target, User):
            if target.id not in self.chat_history_by_user:
                self.chat_history_by_user[target.id] = []
            # 添加消息到当前用户的私聊历史
            current_history = self.chat_history_by_user[target.id]
            current_history.append(message)
            if len(current_history) > MAX_MSG_RECORDS:
                self.chat_history_by_user[self.current_user.id] = current_history[-MAX_MSG_RECORDS:]
        else:
            if target.id not in self.chat_history_by_channel:
                self.chat_history_by_channel[target.id] = []
            # 添加消息到当前频道
            current_history = self.chat_history_by_channel[target.id]
            current_history.append(message)
            # 限制历史记录数量
            if len(current_history) > MAX_MSG_RECORDS:
                self.chat_history_by_channel[self.current_channel.id] = current_history[-MAX_MSG_RECORDS:]

        self.emit_chat_watcher(message)

    def clear_chat_history(self):
        """清空当前频道的聊天历史"""
        if self.current_channel == DIRECT:
            self.chat_history_by_user[self.current_user.id] = []
        else:
            self.chat_history_by_channel[self.current_channel.id] = []
        self.emit_chat_watcher()

    def add_chat_watcher(self, watcher: Widget) -> None:
        self.chat_watchers.append(watcher)

    def remove_chat_watcher(self, watcher: Widget) -> None:
        self.chat_watchers.remove(watcher)

    def emit_chat_watcher(self, *messages: "MessageEvent") -> None:
        for watcher in self.chat_watchers:
            watcher.post_message(StateChange(messages))
