import logging
from typing import Any
from bot.types.command_event import CommandEvent
from bot.config.config import config
from bot.apis.create_reply import create_reply, ReplyMessage
from bot.apis.send_message import sender
from bot.plugin.basic_plugin import BasicPlugin
from bot.plugin.manager.plugin_registry import register_command

logger = logging.getLogger(__name__)


class ConfigManagerHandler(BasicPlugin):
    def __init__(self) -> None:
        pass

    def get(self, path: str) -> ReplyMessage:
        try:
            get_result: Any = config.get(path)
        except KeyError as e:
            logger.exception("访问的值不存在 %s", e)
            reply = create_reply().text(f"访问的值不存在： {e}")
        except Exception as e:
            logger.exception("获取配置项时出现问题 %s", e)
            reply = create_reply().text(f"获取配置项时出现问题： {e}")
        else:
            reply = (
                create_reply()
                .text("配置项：\n")
                .text(str(get_result) + "\n")
                .text(f"类型{type(get_result)}")
            )
        return reply

    def set(self, path: str, value: str) -> ReplyMessage:
        try:
            config.set(path, value)
        except KeyError as e:
            logger.exception("配置不存在: %s", e)
            reply = create_reply().text(f"配置不存在：{e}")
        except TypeError as e:
            logger.exception("配置项类型不符: %s", e)
            reply = create_reply().text(f"配置项类型不符：{e}")
        except Exception as e:
            logger.exception("设置配置项时出现问题: %s", e)
            reply = create_reply().text(f"设置配置时出现问题： {e}")
        else:
            reply = create_reply().text(
                f"已经将{path}设定为{value}，类型{type(config.get(path))}"
            )
        return reply

    @register_command("config")
    async def handle(self, command_event: CommandEvent) -> None:
        """在运行时改动配置"""

        user_id = command_event.user_id
        admin_user_id = config.get("admin_user_id")
        if user_id != admin_user_id:
            reply = create_reply().to(user_id).text("您不是管理员，不能使用此命令。")
            await sender.send(reply.build())
        elif (
            len(command_event.parameters) == 1 and command_event.parameters[0] == "help"
        ):
            reply = create_reply().to(user_id).text("help")
            await sender.send(reply.build())
        elif (
            len(command_event.parameters) == 2 and command_event.parameters[0] == "get"
        ):
            reply = self.get(command_event.parameters[1])
            await sender.send(reply.to(user_id).build())
        elif (
            len(command_event.parameters) == 3 and command_event.parameters[0] == "set"
        ):
            reply = self.set(command_event.parameters[1], command_event.parameters[2])
            await sender.send(reply.to(user_id).build())
        else:
            reply = create_reply().to(user_id).text("您可以用/config help查看帮助。")
            await sender.send(reply.build())
        return None