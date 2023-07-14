# Nonechat

通用控制台聊天界面

## 使用

```python
from nonechat.app import Frontend
from nonechat.backend import Backend
from nonechat.info import User, MessageEvent, Event
from nonechat.message import ConsoleMessage, Text
from datetime import datetime


class ExampleBackend(Backend):

    def on_console_init(self):
        print("on_console_init")

    def on_console_load(self):
        print("on_console_load")

    def on_console_mount(self):
        print("on_console_mount")

    def on_console_unmount(self):
        print("on_console_unmount")

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


app = Frontend(ExampleBackend)
app.run()
```
