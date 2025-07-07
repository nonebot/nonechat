import sys
import contextlib
from datetime import datetime
from typing import Any, TextIO, Generic, TypeVar, Optional, cast

from textual.app import App
from textual.widgets import Input
from textual.binding import Binding

from .backend import Backend
from .router import RouterView
from .log_redirect import FakeIO
from .setting import ConsoleSetting
from .views.log_view import LogView
from .components.footer import Footer
from .components.header import Header
from .storage import Channel, Storage
from .message import Text, ConsoleMessage
from .model import User, Event, MessageEvent
from .views.horizontal import HorizontalView

TB = TypeVar("TB", bound=Backend)


class Frontend(App, Generic[TB]):
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=False, priority=True),
        Binding("ctrl+d", "toggle_dark", "Toggle dark mode"),
        Binding("ctrl+s", "screenshot", "Save a screenshot"),
        Binding("ctrl+underscore", "focus_input", "Focus input", key_display="ctrl+/"),
    ]

    ROUTES = {"main": lambda: HorizontalView(), "log": lambda: LogView()}

    def __init__(self, backend: type[TB], setting: ConsoleSetting = ConsoleSetting()):
        super().__init__()
        self.setting = setting
        self.title = setting.title  # type: ignore
        self.sub_title = setting.sub_title  # type: ignore

        # 创建初始用户
        initial_user = User("console", setting.user_avatar, setting.user_name)
        initial_channel = Channel("general", "通用", "默认聊天频道", "💬")
        self.storage = Storage(initial_user, initial_channel)

        self._fake_output = cast(TextIO, FakeIO(self.storage))
        self._origin_stdout = sys.stdout
        self._origin_stderr = sys.stderr
        self._textual_stdout: Optional[TextIO] = None
        self._textual_stderr: Optional[TextIO] = None
        self.backend: TB = backend(self)

    def compose(self):
        yield Header()
        yield RouterView(self.ROUTES, "main")
        yield Footer()

    def on_load(self):
        self.backend.on_console_load()

    def on_mount(self):
        with contextlib.suppress(Exception):
            self._textual_stdout = sys.stdout
            sys.stdout = self._fake_output

        with contextlib.suppress(Exception):
            self._textual_stderr = sys.stderr
            sys.stderr = self._fake_output

        # 应用主题背景色
        self.apply_theme_background()

        self.backend.on_console_mount()

    def on_unmount(self):
        if self._textual_stdout is not None:
            sys.stdout = self._origin_stdout
        if self._textual_stderr is not None:
            sys.stderr = self._origin_stderr
        self.backend.on_console_unmount()

    async def call(self, api: str, data: dict[str, Any]):
        if api == "send_msg":
            self.storage.write_chat(
                MessageEvent(
                    type="console.message",
                    time=datetime.now(),
                    self_id=self.backend.bot.id,
                    message=data["message"],
                    user=self.backend.bot,
                    channel=self.storage.current_channel,
                )
            )
        elif api == "bell":
            await self.run_action("bell")

    def action_focus_input(self):
        with contextlib.suppress(Exception):
            self.query_one(Input).focus()

    async def action_post_message(self, message: str):
        msg = MessageEvent(
            time=datetime.now(),
            self_id=self.backend.bot.id,
            type="console.message",
            user=self.storage.current_user,
            message=ConsoleMessage([Text(message)]),
            channel=self.storage.current_channel,
        )
        self.storage.write_chat(msg)
        await self.backend.post_event(msg)

    async def action_post_event(self, event: Event):
        await self.backend.post_event(event)

    def action_toggle_dark(self) -> None:
        """切换暗色模式并应用相应背景色"""
        # 先调用父类的 toggle_dark 方法
        super().action_toggle_dark()

        # 应用对应的背景色
        self.apply_theme_background()

    def apply_theme_background(self) -> None:
        """根据当前主题模式应用背景色设置"""
        setting = self.setting

        # 查找需要更新背景色的视图
        try:
            horizontal_view = self.query_one(HorizontalView)
            if self.current_theme.dark:
                horizontal_view.styles.background = setting.dark_bg_color
            else:
                horizontal_view.styles.background = setting.bg_color
        except Exception:
            # 视图可能还没有加载
            pass

        # 如果有其他需要设置背景色的组件，可以在这里添加
