import contextlib
from datetime import datetime
from typing import Any, TextIO, Generic, TypeVar, Optional, cast

from textual.app import App
from textual.widgets import Input
from textual.binding import Binding

from .backend import Backend
from .storage import Storage, Channel
from .router import RouterView
from .log_redirect import FakeIO
from .setting import ConsoleSetting
from .views.log_view import LogView
from .components.footer import Footer
from .components.header import Header
from .message import Text, ConsoleMessage
from .info import User, Event, MessageEvent, Robot
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
        self._redirect_stdout: Optional[contextlib.redirect_stdout[TextIO]] = None
        self._redirect_stderr: Optional[contextlib.redirect_stderr[TextIO]] = None
        self.backend: TB = backend(self)


    def compose(self):
        yield Header()
        yield RouterView(self.ROUTES, "main")
        yield Footer()

    def on_load(self):
        self.backend.on_console_load()

    def on_mount(self):
        with contextlib.suppress(Exception):
            stdout = contextlib.redirect_stdout(self._fake_output)
            stdout.__enter__()
            self._redirect_stdout = stdout

        with contextlib.suppress(Exception):
            stderr = contextlib.redirect_stderr(self._fake_output)
            stderr.__enter__()
            self._redirect_stderr = stderr

        self.backend.on_console_mount()

    def on_unmount(self):
        if self._redirect_stderr is not None:
            self._redirect_stderr.__exit__(None, None, None)
            self._redirect_stderr = None
        if self._redirect_stdout is not None:
            self._redirect_stdout.__exit__(None, None, None)
            self._redirect_stdout = None
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
