from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

from .model import Event, Robot

if TYPE_CHECKING:
    from .app import Frontend


class Backend(ABC):
    frontend: "Frontend"

    def __init__(self, frontend: "Frontend"):
        self.frontend = frontend
        self.bot = Robot("robot", self.frontend.setting.bot_avatar, self.frontend.setting.bot_name)

    @abstractmethod
    def on_console_load(self): ...

    @abstractmethod
    def on_console_mount(self): ...

    @abstractmethod
    def on_console_unmount(self): ...

    @abstractmethod
    async def post_event(self, event: Event): ...
