import logging
import datetime
import httpx
from bot.types import CommandEvent
from bot.apis.plugin_context import PluginContext
from bot.apis.create_reply import create_reply
from bot.plugin.basic_plugin import BasicPlugin
from bot.plugin.manager.plugin_registry import register_command

logger = logging.getLogger(__name__)


class YurikotoHandler(BasicPlugin):
    def __init__(self) -> None:
        pass

    @staticmethod
    async def get_yurikoto_picture_async_file(
        time_type: str = "default", orientation: str = "default"
    ):
        URL = "https://v1.yurikoto.com/wallpaper"
        url_params = {"encode": "json"}

        if time_type != "default":
            if time_type in ("rand", "day", "night"):
                url_params.update({"type": time_type})
            else:
                logger.warning("不正确的壁纸类型. 只接受rand, day, night.")
            if orientation in ("rand", "horizontal", "vertical"):
                url_params.update({"orientation": orientation})
            else:
                logger.warning("不正确的屏幕方向. 只接受rand, horizontal, vertical.")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    "GET", URL, timeout=1, params=url_params
                )
                response.raise_for_status()
                res_json = response.json()
                picture = await client.request(
                    "GET", res_json["link"], timeout=1, follow_redirects=True
                )
                picture.raise_for_status()
            except (httpx.HTTPError, ValueError) as e:
                logger.exception("请求发生错误:%s", e)
                return
            # httpx是默认不跟重定向的，和requests不同

        with open(
            f"pic_at_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.jpg", "wb"
        ) as f:
            f.write(picture.content)
        logger.info("写入图片成功")

    @staticmethod
    async def get_yurikoto_picture_async_link(
        time_type: str = "default", orientation: str = "default"
    ) -> str | None:
        URL = "https://v1.yurikoto.com/wallpaper"
        url_params = {"encode": "json"}

        if time_type != "default":
            if time_type in ("rand", "day", "night"):
                url_params.update({"type": time_type})
            else:
                logger.warning("不正确的壁纸类型. 只接受rand, day, night.")
            if orientation in ("rand", "horizontal", "vertical"):
                url_params.update({"orientation": orientation})
            else:
                logger.warning("不正确的屏幕方向. 只接受rand, horizontal, vertical.")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    "GET", URL, timeout=1, params=url_params
                )
                response.raise_for_status()
                res_json = response.json()
            except (httpx.HTTPError, ValueError) as e:
                logger.exception("请求发生错误:%s", e)
                return
            # httpx是默认不跟重定向的，和requests不同
        return res_json["link"]

    @staticmethod
    async def get_yurikoto_line():
        """获取一句台词"""

        URL = "https://v1.yurikoto.com/sentence"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request("GET", URL)
                response.raise_for_status()
                res_json = response.json()
                logger.info("获取Yurikoto台词成功")
                return (res_json["content"], res_json["source"])
            except (httpx.HTTPError, ValueError) as e:
                logger.exception("请求发生错误: %s", e)
                return ("获取台词失败", "Yurikoto模块")

    @register_command("yurikoto")
    async def handler(self, context: PluginContext, command_event: CommandEvent):
        user_id = command_event.user_id
        image_link = await self.get_yurikoto_picture_async_link()
        if image_link is not None:
            reply = create_reply().to(user_id).image(image_link)
            await context.sender.send(reply.build())
        else:
            reply = create_reply().to(user_id).text("获取Yurikoto随机图片失败。")
            await context.sender.send(reply.build())

    @register_command("yuriline")
    async def handler_line(self, context: PluginContext, command_event: CommandEvent):
        user_id = command_event.user_id
        line, source = await self.get_yurikoto_line()
        if line is not None:
            reply = create_reply().to(user_id).text(line + "\n- " + source)
            await context.sender.send(reply.build())
        else:
            reply = create_reply().to(user_id).text("获取Yurikoto随机台词失败。")
            await context.sender.send(reply.build())
