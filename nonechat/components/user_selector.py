import random
import string
from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.message import Message
from textual.widgets import Label, Button, ListItem, ListView

from ..model import User

if TYPE_CHECKING:
    from ..app import Frontend


class UserSelectorPressed(Message):
    """用户选择器按钮被按下时发送的消息"""

    def __init__(self, user: User) -> None:
        super().__init__()
        self.user = user


class UserSelector(Widget):
    """用户选择器组件"""

    DEFAULT_CSS = """
    UserSelector {
        layout: vertical;
        height: auto;
        width: 100%;
        border: round rgba(170, 170, 170, 0.7);
        padding: 1;
        margin: 1;
    }

    UserSelector ListView {
        height: auto;
        width: 100%;
        max-height: 85%;
    }

    UserSelector ListItem {
        width: 100%;
        margin: 1;
        padding: 1;
        text-align: center;
    }

    UserSelector .add-user-button {
        width: 100%;
        margin-top: 1;
        background: darkblue;
        color: white;
    }
    """

    def __init__(self):
        super().__init__()
        self.user_items: dict[str, tuple[ListItem, User]] = {}

    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)

    def compose(self):
        yield ListView(id="user-list")
        yield Button("➕ 添加用户", classes="add-user-button", id="add-user")

    async def on_mount(self):
        await self.update_user_list()

    async def update_user_list(self):
        """更新用户列表"""
        user_list = self.query_one("#user-list", ListView)
        await user_list.clear()
        self.user_items.clear()

        for user in self.app.storage.users:
            label = Label(f"{user.avatar} {user.nickname}")
            item = ListItem(label, id=f"user-{user.id}")
            self.user_items[user.id] = (item, user)
            await user_list.append(item)

            # 标记当前用户
            if user.id == self.app.storage.current_user.id:
                item.add_class("current")
            else:
                item.remove_class("current")

    async def on_button_pressed(self, event: Button.Pressed):
        """处理按钮点击事件"""
        if event.button.id == "add-user":
            await self._add_new_user()

    async def on_list_view_selected(self, event: ListView.Selected):
        """处理列表项选择事件"""
        if event.item and event.item.id and event.item.id.startswith("user-"):
            # 查找对应的用户
            for item, user in self.user_items.values():
                if item == event.item:
                    self.post_message(UserSelectorPressed(user))
                    break

    async def _add_new_user(self):
        """添加新用户的逻辑"""

        # 生成随机用户ID
        user_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))

        # 一些预设的用户
        avatars = ["🟥", "🟩", "🟦", "🟨", "🟪", "🟫", "🔵", "🔴", "🟠", "🟣", "🟤", "🟡"]
        names = ["用户A", "用户B", "用户C", "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace"]

        new_user = User(id=user_id, nickname=random.choice(names), avatar=random.choice(avatars))

        self.app.storage.add_user(new_user)
        await self.update_user_list()
