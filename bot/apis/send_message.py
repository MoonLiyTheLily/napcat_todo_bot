# 本类未使用
class MessageSender:
    def __init__(self, websocket):
        self.websocket = websocket

    async def send(self, message):
        await self.websocket.send(message)
