from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.widgets import Button, Static
from textual.containers import Horizontal, Vertical
from textual.message import Message

from ..info import User

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
        max-height: 15;
        overflow-y: auto;
    }
    
    UserSelector .title {
        height: 1;
        width: 100%;
        text-align: center;
        text-style: bold;
        color: cyan;
        margin-bottom: 1;
    }
    
    UserSelector .user-list {
        layout: vertical;
        height: auto;
        width: 100%;
    }
    
    UserSelector .user-button {
        width: 100%;
        margin-bottom: 1;
        text-align: center;
    }
    
    UserSelector .user-button.current {
        background: darkblue;
        color: white;
    }
    
    UserSelector .add-user-button {
        width: 100%;
        margin-top: 1;
        background: darkgreen;
        color: white;
        text-style: bold;
        text-align: center;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.user_buttons: dict[str, tuple[Button, User]] = {}
    
    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)
    
    def compose(self):
        yield Static("👥 用户列表", classes="title")
        yield Vertical(classes="user-list", id="user-list")
        yield Button("➕ 添加用户", classes="add-user-button", id="add-user")
    
    def on_mount(self):
        self.update_user_list()
    
    def update_user_list(self):
        """更新用户列表"""
        user_list = self.query_one("#user-list")
        # user_list.remove_children()
        # self.user_buttons.clear()

        for user in self.app.storage.users:
            if user.id in self.user_buttons:
                button = self.user_buttons[user.id][0]
            else:
                button = Button(
                    f"{user.avatar} {user.nickname}",
                    classes="user-button",
                    id=f"user-{user.id}"
                )
                self.user_buttons[user.id] = (button, user)
                user_list.mount(button)

            # 标记当前用户
            if user.id == self.app.storage.current_user.id:
                button.add_class("current")
            else:
                button.remove_class("current")


    async def on_button_pressed(self, event: Button.Pressed):
        """处理按钮点击事件"""
        if event.button.id == "add-user":
            await self._add_new_user()
        elif event.button.id and event.button.id.startswith("user-"):
            # 查找对应的用户
            for button, user in self.user_buttons.values():
                if button == event.button:
                    self.post_message(UserSelectorPressed(user))
                    break
    
    async def _add_new_user(self):
        """添加新用户的逻辑"""
        # 先简单实现，稍后再创建对话框
        import random
        import string
        
        # 生成随机用户ID
        user_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # 一些预设的用户
        avatars = ["👤", "🧑", "👩", "👨", "🧑‍💻", "👩‍💻", "👨‍💻", "🧑‍🎓", "👩‍🎓", "👨‍🎓"]
        names = ["用户A", "用户B", "用户C", "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace"]
        
        new_user = User(
            id=user_id,
            nickname=random.choice(names),
            avatar=random.choice(avatars)
        )
        
        self.app.storage.add_user(new_user)
        self.update_user_list()
