from dataclasses import field, dataclass

from ..model import DIRECT, User, Channel, MessageEvent

MAX_MSG_RECORDS = 500


@dataclass
class MessageStorage:
    # 多用户和频道支持
    users: list[User] = field(default_factory=list)
    channels: list[Channel] = field(default_factory=list)
    bots: list[User] = field(default_factory=list)

    # 按频道分组的聊天历史记录
    _chat_history: dict[str, list[MessageEvent]] = field(default_factory=dict)

    def __post_init__(self):
        self.channels.append(DIRECT)

    def chat_history(self, channel: Channel) -> list[MessageEvent]:
        """获取当前频道的聊天历史"""
        return self._chat_history.get(channel.id, [])

    def add_user(self, user: User):
        """添加新用户"""
        if user not in self.users:
            self.users.append(user)

    def add_bot(self, bot: User):
        """添加新机器人"""
        if bot not in self.bots:
            self.bots.append(bot)

    def add_channel(self, channel: Channel):
        """添加新频道"""
        if channel not in self.channels:
            self.channels.append(channel)

    def write_chat(self, message: "MessageEvent", channel: Channel) -> None:
        key = channel.id
        if key not in self._chat_history:
            self._chat_history[key] = []
        current_history = self._chat_history[key]
        current_history.append(message)
        # 限制历史记录数量
        if len(current_history) > MAX_MSG_RECORDS:
            self._chat_history[key] = current_history[-MAX_MSG_RECORDS:]

    def clear_chat_history(self, channel: Channel):
        """清空当前频道的聊天历史"""
        self._chat_history.pop(channel.id, None)
