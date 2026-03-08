import sys
from inspect import cleandoc
from asyncio import sleep, gather, create_task

from loguru import logger
from textual.color import Color

from nonechat.app import Frontend
from nonechat.backend import Backend
from nonechat.setting import ConsoleSetting
from nonechat.model import Event, MessageEvent
from nonechat.message import Text, Markdown, ConsoleMessage


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
        icon="💻",  # 浅色模式背景色
        dark_bg_color=Color(40, 44, 52),  # 暗色模式背景色 (更深一些)
        title_color=Color(229, 192, 123),
        header_color=Color(90, 99, 108, 0.6),
        icon_color=Color.parse("#22b14c"),
        toolbar_exit="❌",
        bot_name="ChatBot",
    ),
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
    elif message_text == "recall":
        msg_id = await app.send_message(ConsoleMessage([Text("这条消息将被撤回")]), event.channel)
        await sleep(3)
        await app.recall_message(msg_id, event.channel)
    elif message_text == "倒计时":
        msg_id = await app.send_message(ConsoleMessage([Text("倒计时开始")]), event.channel)
        await sleep(1)
        for i in range(5, 0, -1):
            await app.edit_message(
                msg_id,
                ConsoleMessage([Text(f"倒计时: {i}秒")]),
                event.channel,
            )
            await sleep(1)
        await app.edit_message(
            msg_id,
            ConsoleMessage([Text("时间到!")]),
            event.channel,
        )
    elif message_text == "stream":
        content = "这是一个用消息编辑模拟的流式消息\n正在打字..."
        msg_id = await app.send_message(ConsoleMessage([Text(content[0])]), event.channel)
        out = content[0]
        for char in content[1:]:
            out += char
            await sleep(0.6 if char == "\n" else 0.3)  # 模拟打字延迟
            await app.edit_message(
                msg_id,
                ConsoleMessage([Text(out)]),
                event.channel,
            )
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
    app.run()
