from console.app import Frontend
from console.backend import Backend
from console.info import User, MessageEvent, Event, Robot
from console.message import ConsoleMessage, Text
from datetime import datetime
from asyncio import gather, create_task
from loguru import logger
import sys

class ExampleBackend(Backend):
    callbacks = []

    def __init__(self, frontend: "Frontend"):
        super().__init__(frontend)
        self._stderr = sys.stderr
        self._logger_id = None

    def on_console_init(self):
        print("on_console_init")

    def on_console_load(self):
        print("on_console_load")
        logger.remove()
        self._logger_id = logger.add(
            self.frontend._fake_output,
            level=0,
            diagnose=False
        )

    def on_console_mount(self):
        print("on_console_mount")

    def on_console_unmount(self):
        if self._logger_id is not None:
            logger.remove(self._logger_id)
            self._logger_id = None
        logger.add(
            self._stderr,
            backtrace=True,
            diagnose=True,
            colorize=True,
        )

        # logger.success("Console exit.")
        # logger.warning("Press Ctrl-C for Application exit")

    async def build_message_event(self, message: str, user: User) -> MessageEvent:
        return MessageEvent(
            time=datetime.now(),
            self_id="robot",
            type="console.message",
            user=user,
            message=ConsoleMessage([Text(message)])
        )

    async def post_event(self, event: Event):
        print("post_event")
        if isinstance(event, MessageEvent):
            await gather(*[create_task(callback(event)) for callback in self.callbacks])

    def register(self):
        def wrapper(func):
            self.callbacks.append(func)
            return func
        return wrapper

app = Frontend(ExampleBackend)

async def send_message(message: ConsoleMessage):
    await app.call("send_msg", {
        "message": message,
        "info": Robot("robot")
    })

@app.backend.register()
async def on_message(event: MessageEvent):
    if str(event.message) == "ping":
        await send_message(ConsoleMessage([Text("pong!")]))

app.run()
