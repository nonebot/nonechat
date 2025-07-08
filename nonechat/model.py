from datetime import datetime
from dataclasses import field, dataclass

from .message import ConsoleMessage


@dataclass(frozen=True, eq=True)
class User:
    """用户"""

    id: str
    avatar: str = field(default="👤")
    nickname: str = field(default="User")


@dataclass(frozen=True, eq=True)
class Robot(User):
    """机器人"""

    avatar: str = field(default="🤖")
    nickname: str = field(default="Bot")


@dataclass(frozen=True, eq=True)
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
