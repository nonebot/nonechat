from typing import Optional
from secrets import token_hex
from dataclasses import field, dataclass

from ..message import ConsoleMessage
from ..model import DIRECT, User, Robot, Channel, MessageEvent

MAX_MSG_RECORDS = 500


@dataclass
class MessageStorage:
    # 多用户和频道支持
    users: dict[str, User] = field(default_factory=dict)
    channels: dict[str, Channel] = field(default_factory=dict)
    bots: dict[str, Robot] = field(default_factory=dict)

    # 按频道分组的聊天历史记录
    _chat_history: dict[str, dict[str, MessageEvent]] = field(default_factory=dict)

    def __post_init__(self):
        self.channels[DIRECT.id] = DIRECT  # 添加默认的 DIRECT 频道

    def chat_history(self, channel: Channel) -> list[MessageEvent]:
        """获取当前频道的聊天历史"""
        return list(self._chat_history.get(channel.id, {}).values())

    def add_user(self, user: User):
        """添加新用户"""
        if user.id not in self.users:
            self.users[user.id] = user
            return True
        return False

    def add_bot(self, bot: Robot):
        """添加新机器人"""
        if bot.id not in self.bots:
            self.bots[bot.id] = bot
            return True
        return False

    def add_channel(self, channel: Channel):
        """添加新频道"""
        if channel.id not in self.channels:
            self.channels[channel.id] = channel
            return True
        return False

    def write_chat(self, message: "MessageEvent", channel: Channel) -> str:
        key = channel.id
        if key not in self._chat_history:
            self._chat_history[key] = {}
        if message.message_id == "_unset_":
            message_id = token_hex(8)
            message.message_id = message_id
        else:
            message_id = message.message_id
        current_history = self._chat_history[key]
        current_history[message_id] = message
        # 限制历史记录数量
        if len(current_history) > MAX_MSG_RECORDS:
            self._chat_history[key] = dict(list(current_history.items())[-MAX_MSG_RECORDS:])
        return message_id

    def remove_chat(self, message_id: str, channel: Channel):
        if channel.id in self._chat_history:
            self._chat_history[channel.id].pop(message_id, None)

    def edit_chat(self, message_id: str, content: ConsoleMessage, channel: Channel):
        """编辑当前频道的聊天消息"""
        if channel.id in self._chat_history:
            current_history = self._chat_history[channel.id]
            if message_id in current_history:
                current_history[message_id].message = content
                return True
        return False

    def get_chat(self, message_id: str, channel: Channel) -> Optional[MessageEvent]:
        """获取当前频道的聊天消息"""
        if channel.id in self._chat_history:
            return self._chat_history[channel.id].get(message_id, None)
        return None

    def clear_chat_history(self, channel: Channel):
        """清空当前频道的聊天历史"""
        self._chat_history.pop(channel.id, None)
