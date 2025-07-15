from typing import Union
from dataclasses import field, dataclass

from ..model import DIRECT, User, Channel, MessageEvent

MAX_MSG_RECORDS = 500


@dataclass
class MessageStorage:
    # 多用户和频道支持
    users: list[User] = field(default_factory=list)
    channels: list[Channel] = field(default_factory=list)

    # 按频道分组的聊天历史记录
    chat_history_by_channel: dict[str, list[MessageEvent]] = field(default_factory=dict)
    chat_history_by_user: dict[str, list[MessageEvent]] = field(default_factory=dict)

    def __post_init__(self):
        self.channels.append(DIRECT)

    def chat_history(self, target: Union[Channel, User]) -> list[MessageEvent]:
        """获取当前频道的聊天历史"""
        if isinstance(target, User):
            return self.chat_history_by_user.get(target.id, [])
        return self.chat_history_by_channel.get(target.id, [])

    def add_user(self, user: User):
        """添加新用户"""
        if user not in self.users:
            self.users.append(user)

    def add_channel(self, channel: Channel):
        """添加新频道"""
        if channel not in self.channels:
            self.channels.append(channel)

    def write_chat(self, message: "MessageEvent", target: Union[Channel, User]) -> None:
        if isinstance(target, User):
            if target.id not in self.chat_history_by_user:
                self.chat_history_by_user[target.id] = []
            # 添加消息到当前用户的私聊历史
            current_history = self.chat_history_by_user[target.id]
            current_history.append(message)
            if len(current_history) > MAX_MSG_RECORDS:
                self.chat_history_by_user[target.id] = current_history[-MAX_MSG_RECORDS:]
        else:
            if target.id not in self.chat_history_by_channel:
                self.chat_history_by_channel[target.id] = []
            # 添加消息到当前频道
            current_history = self.chat_history_by_channel[target.id]
            current_history.append(message)
            # 限制历史记录数量
            if len(current_history) > MAX_MSG_RECORDS:
                self.chat_history_by_channel[target.id] = current_history[-MAX_MSG_RECORDS:]

    def clear_chat_history(self, target: Union[Channel, User]):
        """清空当前频道的聊天历史"""
        if isinstance(target, User):
            self.chat_history_by_user[target.id] = []
        else:
            self.chat_history_by_channel[target.id] = []
