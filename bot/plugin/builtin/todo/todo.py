import logging
import websockets, asyncio
from bot.types import CommandEvent, TodoItem
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender
from bot.plugin.basic_plugin import BasicPlugin
from bot.apis.registries import register_llm_tool, register_command, register_active
from bot.llm.llm_tool_registry import LLMToolContext
from bot.plugin.builtin.todo.todo_tools import descriptions
from bot.config.config import config
from database import TodoDatabase

logger = logging.getLogger(__name__)


class TodoHandler(BasicPlugin):
    def __init__(self):
        self.todo_db = TodoDatabase()
        self.todo_db.initialize_table()
        self.parameter_handlers = {
            "default": self.default,
            "parameter_not_found": self.parameter_not_found,
            "help": self.help,
            "show": self.show,
            "add": self.add,
            "delete": self.delete,
            "done": self.done,
            "undone": self.undone,
        }

    @register_command("todo")
    async def handle(self, command_event: CommandEvent):
        """待办事项管理

        处理todo命令的函数

        :param user_id: 用户id
        :type user_id: int
        :param parameters: 解析获得的参数
        :type parameters: list
        """

        if len(command_event.parameters) == 0:
            handler = self.parameter_handlers["default"]
            logger.debug("第一参数: None")
        else:
            param = command_event.parameters[0]
            handler = self.parameter_handlers.get(
                param, self.parameter_handlers["parameter_not_found"]
            )
            logger.debug("第一参数: %s", param)

        if handler is not None:
            reply = handler(command_event)
        else:
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("todo_handler已执行，但未找到对应的处理函数。")
                .build()
            )
        await sender.send(reply)

    def help(self, command_event: CommandEvent):
        """显示待办事项的帮助信息"""

        help_message = (
            "待办事项命令帮助：\n"
            "/todo add <事项内容> - 添加新的待办事项\n"
            "/todo delete <事项编号> - 删除指定的待办事项\n"
            "/todo show - 列出所有待办事项\n"
            "/todo done <事项编号> - 标记指定的待办事项为已完成\n"
            "/todo help - 显示此帮助信息"
        )
        reply = create_reply().to(command_event.user_id).text(help_message)
        return reply.build()

    def parameter_not_found(self, command_event: CommandEvent):
        """处理未知参数的函数"""

        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("未知的todo命令参数\n请使用/todo help获取帮助信息。")
        )
        return reply.build()

    def default(self, command_event: CommandEvent):
        """处理无参数情况的函数"""

        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("默认todo_handler已执行\n您可以采用/todo help获取帮助信息。")
        )
        return reply.build()

    def get_todos(self, user_id: int):
        """获取用户的待办事项列表，并且是直接获得字符串列表

        :param user_id: 用户id
        :type user_id: int
        :return: 待办事项列表
        :rtype: list
        """
        todo_list = self.todo_db.check_todo(user_id)
        if todo_list is None:
            return None
        else:
            result = []
            for item in todo_list:
                assert isinstance(item, TodoItem)
                result.append(item.get_list_string())
            return result

    def show(self, command_event: CommandEvent):
        """显示用户的待办事项列表"""

        todos = self.get_todos(command_event.user_id)
        if todos is None or len(todos) == 0:
            message = "您的待办事项列表为空。"
        else:
            message = "您的待办事项列表：\n"
            todo_number = 1
            for todo in todos:
                message += f"{todo_number}. {todo}\n"
                todo_number += 1
            message = message[:-1]  # 去掉最后的换行符

        reply = create_reply().to(command_event.user_id).text(message)
        return reply.build()

    def add(self, command_event: CommandEvent):
        """添加新的待办事项"""

        # 在本行内任何参数之后的内容都作为待办事项内容
        # 由于原来就是按空格划分的，所以这里用空格作为分隔符链接所有内容
        full_content = " ".join(command_event.parameters[1:])
        if len(command_event.parameters) < 2 or full_content.strip() == "":
            reply = (
                create_reply().to(command_event.user_id).text("请提供待办事项的内容。")
            )
            return reply.build()

        self.todo_db.add_todo(
            user_id=command_event.user_id,
            content=full_content,
            user_create_time=command_event.user_send_time,
        )

        reply = create_reply().to(command_event.user_id).text("已添加新的待办事项。")
        return reply.build()

    def delete(self, command_event: CommandEvent):
        """删除指定的待办事项

        用户指定的是待办的编号（或者all），从1开始。待办编号是“此用户的第几个待办”，而不是总数据库里的id
        """
        if len(command_event.parameters) < 2:
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("请提供要删除的待办事项编号，如果您想删除所有待办，请使用all。")
            )
            return reply.build()
        if (
            not command_event.parameters[1].isdigit()
            and not command_event.parameters[1] == "all"
        ):
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("待办事项编号必须是数字，如果您想删除所有待办，请使用all。")
            )
            return reply.build()

        if command_event.parameters[1].isdigit():
            todo_index = int(command_event.parameters[1]) - 1
            todo_list = self.todo_db.check_todo(command_event.user_id)
            if todo_list is None or len(todo_list) == 0:
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("您的待办事项列表为空，无法删除。")
                )
                return reply.build()

            if todo_index < 0 or todo_index >= len(todo_list):
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("待办事项编号无效，无法删除。")
                )
                return reply.build()

            todo_item = todo_list[todo_index]
            assert isinstance(todo_item, TodoItem)
            self.todo_db.delete_todo(command_event.user_id, todo_item.database_id)
        elif command_event.parameters[1] == "all":
            todo_list = self.todo_db.check_todo(command_event.user_id)
            if todo_list is None or len(todo_list) == 0:
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("您的待办事项列表为空，无法删除。")
                )
                return reply.build()
            for todo in todo_list:
                assert isinstance(todo, TodoItem)
                self.todo_db.delete_todo(command_event.user_id, todo.database_id)

        reply = create_reply().to(command_event.user_id).text("已删除指定的待办事项。")
        return reply.build()

    def done(self, command_event: CommandEvent):
        """标记指定的待办事项为已完成

        用户指定的是待办的编号，从1开始。待办编号是“此用户的第几个待办”，而不是总数据库里的id
        """
        if len(command_event.parameters) < 2:
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("请提供要完成的待办编号，如果您想完成所有待办，请使用all。")
            )
            return reply.build()
        if (
            not command_event.parameters[1].isdigit()
            and not command_event.parameters[1] == "all"
        ):
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("待办事项编号必须是数字，如果您想完成所有待办，请使用all。")
            )
            return reply.build()

        if command_event.parameters[1].isdigit():
            todo_index = int(command_event.parameters[1]) - 1
            todo_list = self.todo_db.check_todo(command_event.user_id)
            if todo_list is None or len(todo_list) == 0:
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("您的待办事项列表为空，无法完成。")
                )
                return reply.build()

            if todo_index < 0 or todo_index >= len(todo_list):
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("待办事项编号无效，无法完成。")
                )
                return reply.build()

            todo_item = todo_list[todo_index]
            assert isinstance(todo_item, TodoItem)
            self.todo_db.complete_todo(command_event.user_id, todo_item.database_id)
        elif command_event.parameters[1] == "all":
            todo_list = self.todo_db.check_todo(command_event.user_id)
            if todo_list is None or len(todo_list) == 0:
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("您的待办事项列表为空，无法完成。")
                )
                return reply.build()
            for todo in todo_list:
                assert isinstance(todo, TodoItem)
                self.todo_db.complete_todo(command_event.user_id, todo.database_id)

        reply = create_reply().to(command_event.user_id).text("已完成指定的待办事项。")
        return reply.build()

    def undone(self, command_event: CommandEvent):
        """标记指定的待办事项为未完成

        用户指定的是待办的编号，从1开始。待办编号是“此用户的第几个待办”，而不是总数据库里的id
        """
        if len(command_event.parameters) < 2:
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text(
                    "请提供要标记为未完成的待办编号，如果您想将所有待办标记为未完成，请使用all。"
                )
            )
            return reply.build()
        if (
            not command_event.parameters[1].isdigit()
            and not command_event.parameters[1] == "all"
        ):
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text(
                    "待办事项编号必须是数字，如果您想将所有待办标记为未完成，请使用all。"
                )
            )
            return reply.build()

        if command_event.parameters[1].isdigit():
            todo_index = int(command_event.parameters[1]) - 1
            todo_list = self.todo_db.check_todo(command_event.user_id)
            if todo_list is None or len(todo_list) == 0:
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("您的待办事项列表为空，无法标记为未完成。")
                )
                return reply.build()

            if todo_index < 0 or todo_index >= len(todo_list):
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("待办事项编号无效，无法标记为未完成。")
                )
                return reply.build()

            todo_item = todo_list[todo_index]
            assert isinstance(todo_item, TodoItem)
            self.todo_db.complete_todo(command_event.user_id, todo_item.database_id)
        elif command_event.parameters[1] == "all":
            todo_list = self.todo_db.check_todo(command_event.user_id)
            if todo_list is None or len(todo_list) == 0:
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("您的待办事项列表为空，无法标记为未完成。")
                )
                return reply.build()
            for todo in todo_list:
                assert isinstance(todo, TodoItem)
                self.todo_db.complete_todo(command_event.user_id, todo.database_id)

        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("已将指定的待办事项标记为未完成。")
        )
        return reply.build()

    @register_llm_tool("check_todo", description=descriptions["check_todo"])
    def check_todo_llm(self, tool_context: LLMToolContext, arguments):
        user_id = tool_context.user_id
        todos = self.get_todos(user_id)
        if todos is None or len(todos) == 0:
            message = "您的待办事项列表为空。"
        else:
            message = "您的待办事项列表：\n"
            todo_number = 1
            for todo in todos:
                message += f"{todo_number}. {todo}\n"
                todo_number += 1
            message = message[:-1]  # 去掉最后的换行符
        return message

    @register_llm_tool("create_todo", description=descriptions["create_todo"])
    def create_todo_llm(self, tool_context: LLMToolContext, arguments: dict):
        content = arguments["content"]
        date = arguments.get("date")
        if date is None:
            self.todo_db.add_todo(
                user_id=tool_context.user_id,
                content=content,
                user_create_time=tool_context.user_send_time,
            )
            return "已成功创建普通待办"
        else:
            self.todo_db.add_todo(
                user_id=tool_context.user_id,
                content=content,
                user_create_time=tool_context.user_send_time,
                notify_time=date,
            )
            return "已成功创建带有提醒的待办"

    @register_llm_tool("delete_todo", description=descriptions["delete_todo"])
    def delete_todo_llm(self, tool_context: LLMToolContext, arguments: dict):
        todo_id_or_all: str = arguments["todo_id_or_all"]
        if todo_id_or_all.isdigit():
            # 这里似乎还需要检查待办是否存在，顺带给llm提醒一下删除的待办是什么名字
            self.todo_db.delete_todo(tool_context.user_id, int(todo_id_or_all))
            return f"已经删除{int(todo_id_or_all)}号待办"
        elif todo_id_or_all == "all":
            todo_list = self.todo_db.check_todo(tool_context.user_id)
            if todo_list is None or len(todo_list) == 0:
                return "用户没有待办事项，不能删除"
            for todo in todo_list:
                assert isinstance(todo, TodoItem)
                self.todo_db.delete_todo(tool_context.user_id, todo.database_id)
            return "已经删除用户的所有待办事项"

    @staticmethod
    @register_llm_tool("get_current_time", description=descriptions["get_current_time"])
    def get_current_time(tool_context: LLMToolContext, arguments):
        return str(tool_context.user_send_time)


class TodoNotifier(BasicPlugin):
    def __init__(self) -> None:
        self.todo_db = TodoDatabase()

    async def todo_sender(self, user_id, todo_items):
        user_todos = []
        for item in todo_items:
            assert isinstance(item, TodoItem)
            if not item.is_done:
                user_todos.append(item.get_list_string())
        if len(user_todos) > 0:
            message = "您有以下待办事项未完成：\n" + "\n".join(user_todos)
            reply = create_reply().to(user_id).text(message).build()
            await sender.send(reply)
            logger.info("已发送待办事项通知给用户%s", user_id)

    @register_active(
        "todo_notifier", 60 * config.get("active.todo.notify_interval")
    )
    async def todo_notify(self):
        """Todo定时通知函数"""
        try:
            logger.info("检查待办事项通知")
            users = self.todo_db.check_all_user()
            if users is not None and len(users) > 0:
                tasks: list[asyncio.Task] = []
                for user_id in users:
                    todo_items = self.todo_db.check_todo(user_id)
                    tasks.append(
                        asyncio.create_task(
                            self.todo_sender(user_id, todo_items), name=f"{user_id}"
                        )
                    )
                    assert todo_items is not None
                await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
                for task in tasks:
                    if task.exception() is not None:
                        logger.exception(
                            "向用户 %s 的待办通知发生错误: %s",
                            task.get_name(),
                            task.exception(),
                        )
        except (websockets.ConnectionClosedError, websockets.ConnectionClosed):
            logger.error("WebSocket连接已关闭，停止待办事项通知")
            return
        except asyncio.CancelledError:
            logger.info("待办事项通知任务已取消")
            raise
        except Exception as e:
            logger.exception("待办事项通知出现错误: %s", str(e))
            raise

    def __del__(self):
        self.todo_db.close()
