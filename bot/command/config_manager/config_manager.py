import copy
import logging
from bot.types.command_event import CommandEvent
from bot.config.config import DEFAULT_CONFIG, DEFAULT_CONFIG_BACKUP
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self) -> None:
        self.now_editing_config = DEFAULT_CONFIG

    def _reset(self):
        self.now_editing_config = copy.deepcopy(DEFAULT_CONFIG_BACKUP)

    def _split_path(self, path: str) -> list[str]:
        if path == "" or path is None:
            return []
        return path.strip().split(".")

    def get_value(self, path: str):
        resolved_path = self._split_path(path)
        config = self.now_editing_config
        for i, key in enumerate(resolved_path):
            if not isinstance(config, dict):
                raise KeyError(
                    f"Config正在访问非字典对象 {'.'.join(resolved_path[:i])}"
                )
            if key not in config:
                raise KeyError(f"设置项 {key} 不存在")
            config = config[key]
        return config

    def set_value(self, path: str, value):
        resolved_path = self._split_path(path)
        assert len(resolved_path) != 0, "配置项不能为空"
        config = self.now_editing_config
        for i, key in enumerate(resolved_path[:-1]):
            if not isinstance(config, dict):
                raise KeyError(
                    f"Config正在访问非字典对象 {'.'.join(resolved_path[:i])}"
                )
            if key not in config:
                raise KeyError(f"Key {key} is not Exist")
            config = config[key]
        if resolved_path[-1] not in config:
            raise KeyError(
                f"要求的设置项 {resolved_path[-1]} 在 {resolved_path[:-1]} 不存在"
            )
        # 特殊类型验证部分
        if isinstance(config[resolved_path[-1]], bool):
            if value == "True":
                config[resolved_path[-1]] = True
            elif value == "False":
                config[resolved_path[-1]] = False
            else:
                raise TypeError("提供的值和目标配置的值类型不同")
        elif isinstance(config[resolved_path[-1]], int):
            config[resolved_path[-1]] = int(value)
        elif isinstance(config[resolved_path[-1]], str):
            config[resolved_path[-1]] = value
        logger.info("设置项 %s 已经更改为 %s.", resolved_path[-1], value)


class ConfigManagerHandler:
    def __init__(self) -> None:
        self.config_manager: ConfigManager = ConfigManager()

    def get(self, path):
        try:
            get_result = self.config_manager.get_value(path)
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

    def set(self, path: str, value):
        try:
            self.config_manager.set_value(path, value)
        except KeyError as e:
            logger.exception("配置不存在: %s", e)
            reply = create_reply().text(f"配置不存在：{e}")
        except TypeError as e:
            logger.exception("配置项类型不符: %s", e)
            reply = create_reply().text(f"配置项类型不符：{e}")
        except Exception as e:
            logger.exception("设置配置项时出现问题: %s", e)
            reply = create_reply().text(f"设置配置时出现问题：{e}")
        else:
            reply = create_reply().text(
                f"已经将{path}设定为{value}，类型{type(self.config_manager.get_value(path))}"
            )
        return reply

    async def handle(self, command_event: CommandEvent):
        user_id = command_event.user_id
        admin_user_id = DEFAULT_CONFIG["admin_user_id"]
        if user_id != admin_user_id:
            reply = create_reply().to(user_id).text("您不是管理员，不能使用此命令。")
            # logger.info("管理员用户id:%s 当前用户id:%s", admin_user_id, user_id)
            # print(type(user_id), "H", type(admin_user_id))
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
