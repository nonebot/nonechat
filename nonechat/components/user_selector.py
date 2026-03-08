import random
import string
from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.message import Message
from textual.widgets import Label, ListItem, ListView

from ..backend import BotAdd
from ..model import User, Robot

if TYPE_CHECKING:
    from ..app import Frontend, BotModeChanged


class UserSelectorPressed(Message):
    """用户选择器按钮被按下时发送的消息"""

    def __init__(self, user: User) -> None:
        super().__init__()
        self.user = user


class _store:
    _current_user: User | None = None
    _current_bot: Robot | None = None

    @classmethod
    def get_current_user(cls, is_bot_mode: bool) -> User | None:
        return cls._current_bot if is_bot_mode else cls._current_user

    @classmethod
    def set_current_user(cls, user: User, is_bot_mode: bool = False):
        if is_bot_mode:
            cls._current_bot = user  # type: ignore
        else:
            cls._current_user = user


class UserSelector(Widget):
    """用户选择器组件"""

    DEFAULT_CSS = """
    UserSelector {
        layout: vertical;
        height: 100%;
        width: 100%;
        padding: 0 1;
    }

    UserSelector ListView {
        height: 1fr;
        width: 100%;
    }

    UserSelector ListItem {
        width: 100%;
        margin: 1;
        text-align: center;
    }
    """

    def __init__(self):
        super().__init__()
        self.user_items: dict[str, tuple[ListItem, User]] = {}
        self.is_bot_mode = self.app.is_bot_mode

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        yield ListView(id="user-list")

    async def on_mount(self):
        _store._current_user = self.app.backend.current_user
        _store._current_bot = self.app.backend.current_bot
        await self.update_user_list()
        self.app.backend.add_user_watcher(self)
        self.app.backend.add_bot_watcher(self)
        self.app.bot_mode_watchers.append(self)

    def on_unmount(self):
        self.app.backend.remove_user_watcher(self)
        self.app.backend.remove_bot_watcher(self)
        self.app.bot_mode_watchers.remove(self)

    async def on_user_add(self, event):
        await self.update_user_list()

    async def on_bot_add(self, event: BotAdd):
        await self.update_user_list()

    async def on_bot_mode_changed(self, event: "BotModeChanged"):
        """处理模式切换"""
        self.is_bot_mode = event.is_bot_mode
        await self.update_user_list()

    async def update_user_list(self):
        """更新用户列表"""
        user_list = self.query_one("#user-list", ListView)
        await user_list.clear()
        self.user_items.clear()

        # 根据模式显示不同的列表
        if self.is_bot_mode:
            # Bot 模式：显示 bot 列表
            users = await self.app.backend.list_bots()
        else:
            # 普通模式：显示用户列表
            users = await self.app.backend.list_users()

        for user in users:
            label = Label(f"{user.avatar} {user.nickname}")
            item = ListItem(label, id=f"user-{user.id}")
            self.user_items[user.id] = (item, user)
            await user_list.append(item)

            current_user = _store.get_current_user(self.is_bot_mode)
            # 标记当前用户/bot
            if current_user and user.id == current_user.id:
                item.highlighted = True

    async def on_list_view_selected(self, event: ListView.Selected):
        """处理列表项选择事件"""
        if event.item and event.item.id and event.item.id.startswith("user-"):
            # 查找对应的用户
            for item, user in self.user_items.values():
                if item == event.item:
                    self.post_message(UserSelectorPressed(user))
                    item.highlighted = True
                    _store.set_current_user(user, self.is_bot_mode)
                else:
                    item.highlighted = False

    async def add_new_user(self):
        """添加新用户的逻辑"""
        # 生成随机用户ID
        user_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        avatars = ["🟥", "🟩", "🟦", "🟨", "🟪", "🟫", "🔵", "🔴", "🟠", "🟣", "🟤", "🟡"]

        if self.is_bot_mode:
            names = ["机器人A", "机器人B", "机器人C", "Bot1", "Bot2", "Bot3"]
            new_bot = Robot(id=user_id, nickname=random.choice(names), avatar=random.choice(avatars))
            await self.app.backend.add_bot(new_bot)
        else:
            names = ["用户A", "用户B", "用户C", "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace"]
            new_user = User(id=user_id, nickname=random.choice(names), avatar=random.choice(avatars))
            await self.app.backend.add_user(new_user)
