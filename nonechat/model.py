from datetime import datetime
from typing import Generic, TypeVar
from dataclasses import field, dataclass

from textual.message import Message

from .message import ConsoleMessage

T = TypeVar("T")


@dataclass(frozen=True, eq=True, unsafe_hash=True)
class User:
    """用户"""

    id: str
    avatar: str = field(default="👤")
    nickname: str = field(default="User")


@dataclass(frozen=True, eq=True, unsafe_hash=True)
class Robot(User):
    """机器人"""

    avatar: str = field(default="🤖")
    nickname: str = field(default="Bot")


@dataclass(frozen=True, eq=True, unsafe_hash=True)
class Channel:
    """频道信息"""

    id: str
    name: str
    description: str = ""
    avatar: str = "💬"


@dataclass
class Event:
    time: datetime
    self_id: str
    type: str
    user: User
    channel: Channel


@dataclass
class MessageEvent(Event):
    message: ConsoleMessage


DIRECT = Channel("_direct", "私聊", "私聊频道", "🔏")


class StateChange(Message, Generic[T], bubble=False):
    def __init__(self, data: T) -> None:
        super().__init__()
        self.data = data
