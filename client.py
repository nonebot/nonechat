import sys
from inspect import cleandoc
from datetime import datetime
from asyncio import run, sleep, gather, create_task

from loguru import logger
from textual.color import Color

from nonechat.app import Frontend
from nonechat.backend import Backend
from nonechat.setting import ConsoleSetting
from nonechat.message import Text, Markdown, ConsoleMessage
from nonechat.model import User, Event, Channel, MessageEvent


class ExampleBackend(Backend):
    callbacks = []

    def __init__(self, frontend: "Frontend"):
        super().__init__(frontend)
        self._stderr = sys.stderr
        self._logger_id = None

    def on_console_load(self):
        print("on_console_load")
        logger.remove()
        self._logger_id = logger.add(self.frontend._fake_output, level=0, diagnose=False)

    async def on_console_mount(self):
        logger.info("on_console_mount")

    async def on_console_unmount(self):
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

    async def post_event(self, event: Event):
        logger.info("post_event")
        if isinstance(event, MessageEvent):
            await gather(*[create_task(callback(event)) for callback in self.callbacks])

    def register(self):
        def wrapper(func):
            self.callbacks.append(func)
            return func

        return wrapper


app = Frontend(
    ExampleBackend,
    ConsoleSetting(
        title="Multi-User Chat",
        sub_title="支持多用户和频道的聊天应用",
        room_title="聊天室",
        icon="💻",  # 浅色模式背景色
        dark_bg_color=Color(40, 44, 52),  # 暗色模式背景色 (更深一些)
        title_color=Color(229, 192, 123),
        header_color=Color(90, 99, 108, 0.6),
        icon_color=Color.parse("#22b14c"),
        toolbar_exit="❌",
        bot_name="ChatBot",
    ),
    bot_mode=True,  # 启用 Bot 模式
)


@app.backend.register()
async def on_message(event: MessageEvent):
    """处理消息事件 - 支持多用户和频道"""
    message_text = str(event.message)

    # 简单的机器人响应逻辑
    if message_text == "ping":
        await app.send_message(ConsoleMessage([Text("pong!")]), event.channel)
    elif message_text == "inspect":
        user_name = event.user.nickname
        channel_name = event.channel.name
        await app.send_message(
            ConsoleMessage([Text(f"当前频道: {channel_name}\n当前用户: {user_name}")]), event.channel
        )
    elif message_text == "help":
        help_text = cleandoc("""
            🤖 可用命令:
            - ping - 测试连接
            - inspect - 查看当前频道和用户
            - help - 显示帮助
            - broadcast - 向所有用户发送消息
            """)
        await app.send_message(ConsoleMessage([Markdown(help_text)]), event.channel)
    elif message_text == "broadcast":
        for user in await app.backend.list_users():
            await app.send_message(ConsoleMessage([Text("测试消息")]), await app.backend.create_dm(user))
    elif message_text == "bell":
        await app.toggle_bell()
    elif message_text == "md":
        with open("./README.md", encoding="utf-8") as md_file:
            md_text = md_file.read()
        await app.send_message(ConsoleMessage([Markdown(md_text)]), event.channel)
    else:
        # 在不同频道中有不同的回复
        channel_name = app.backend.current_channel.name
        if "技术" in channel_name:
            await app.send_message(ConsoleMessage([Text(f"💻 在{channel_name}中讨论技术话题很有趣!")]), event.channel)
        elif "游戏" in channel_name:
            await app.send_message(ConsoleMessage([Text(f"🎮 {channel_name}中有什么好玩的游戏推荐吗?")]), event.channel)
        else:
            await app.send_message(ConsoleMessage([Text(f"😊 在{channel_name}中收到了你的消息")]), event.channel)


if __name__ == "__main__":

    async def generate_event():
        """生成一个测试事件"""
        user = User(id="1", nickname="TestUser", avatar="👤")
        channel = Channel(id="2", name="General", avatar="🌐")
        message = ConsoleMessage([Text("help")])
        event = MessageEvent(
            time=datetime.now(),
            self_id=user.id,
            type="console.message",
            user=user,
            message=message,
            message_id="test_message_1",
            channel=channel,
        )
        await app.receive_message(event)

    async def generate_event_loop():
        """循环生成测试事件"""
        await sleep(5)  # 等待一段时间后开始生成事件
        while True:
            user = User(id="1", nickname="TestUser", avatar="👤")
            channel = Channel(id="2", name="General", avatar="🌐")
            message = ConsoleMessage([Text("1")])
            event = MessageEvent(
                time=datetime.now(),
                self_id=user.id,
                type="console.message",
                user=user,
                message=message,
                message_id=f"test_message_{datetime.now().timestamp()}",
                channel=channel,
            )
            await app.receive_message(event)
            await app.backend.post_event(event)
            await sleep(3)

    async def main():
        create_task(generate_event())
        create_task(generate_event_loop())
        await app.run_async()

    run(main())
