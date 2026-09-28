import logging
import json
from pathlib import Path
from bot.types import CommandEvent, Todo
from bot.apis.plugin_context import PluginContext
from bot.apis.create_reply import create_reply
from bot.plugin.basic_plugin import BasicPlugin
from bot.apis.registries import register_llm_tool, register_command
from bot.llm.llm_tool_registry import LLMToolContext
from database import TodoDatabase
from datetime import datetime

from .todo_notifier import TodoNotifier

with open(Path(__file__).parent / "todo_tools.json", "r", encoding="utf-8") as fp:
    descriptions = json.load(fp)

logger = logging.getLogger(__name__)


class TodoHandler(BasicPlugin):
    def __init__(self) -> None:
        self.todo_db: TodoDatabase = TodoDatabase()
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

    async def initialize(self) -> None:
        await super().initialize()
        await self.todo_db.initialize()

    async def shutdown(self) -> None:
        await self.todo_db.close()

    @register_command("todo")
    async def handle(self, context: PluginContext, command_event: CommandEvent):
        """待办事项管理

        处理todo命令的函数
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
        reply = await handler(command_event)
        await context.sender.send(reply)

    async def help(self, command_event: CommandEvent):
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

    async def parameter_not_found(self, command_event: CommandEvent):
        """处理未知参数的函数"""

        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("未知的todo命令参数\n请使用/todo help获取帮助信息。")
        )
        return reply.build()

    async def default(self, command_event: CommandEvent):
        """处理无参数情况的函数"""

        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("默认todo_handler已执行\n您可以采用/todo help获取帮助信息。")
        )
        return reply.build()

    async def get_todos(self, user_id: int):
        """获取用户的待办事项列表，并且是直接获得字符串列表"""

        todo_list = await self.todo_db.get_todos(user_id)
        if todo_list is None:
            return None
        else:
            result = []
            for item in todo_list:
                result.append(item.get_list_string())
            return result

    async def show(self, command_event: CommandEvent):
        """显示用户的待办事项列表"""

        todos = await self.get_todos(command_event.user_id)
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

    async def add(self, command_event: CommandEvent):
        """添加新的待办事项"""

        # 在本行内任何参数之后的内容都作为待办事项内容
        # 由于原来就是按空格划分的，所以这里用空格作为分隔符链接所有内容
        full_content = " ".join(command_event.parameters[1:])
        if len(command_event.parameters) < 2 or full_content.strip() == "":
            reply = (
                create_reply().to(command_event.user_id).text("请提供待办事项的内容。")
            )
            return reply.build()

        new_todo = Todo(
            user_id=command_event.user_id,
            content=full_content,
            create_time=datetime.strptime(
                command_event.user_send_time, "%Y-%m-%d %H:%M:%S"
            ),
        )

        await self.todo_db.add_todo(new_todo)
        reply = create_reply().to(command_event.user_id).text("已添加新的待办事项。")
        return reply.build()

    async def delete(self, command_event: CommandEvent):
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
            todo_list = await self.todo_db.get_todos(command_event.user_id)
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
            await self.todo_db.delete(
                user_id=command_event.user_id, todo_id=todo_item.todo_id  # type: ignore
            )

        elif command_event.parameters[1] == "all":
            todo_list = await self.todo_db.get_todos(command_event.user_id)
            if todo_list is None or len(todo_list) == 0:
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("您的待办事项列表为空，无法删除。")
                )
                return reply.build()
            for todo in todo_list:
                await self.todo_db.delete(
                    user_id=command_event.user_id, todo_id=todo.todo_id  # type: ignore
                )

        reply = create_reply().to(command_event.user_id).text("已删除指定的待办事项。")
        return reply.build()

    async def done(self, command_event: CommandEvent):
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
            todo_list = await self.todo_db.get_todos(command_event.user_id)
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
            await self.todo_db.done(todo_item.todo_id)  # type: ignore
        elif command_event.parameters[1] == "all":
            todo_list = await self.todo_db.get_todos(command_event.user_id)
            if todo_list is None or len(todo_list) == 0:
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("您的待办事项列表为空，无法完成。")
                )
                return reply.build()
            for todo in todo_list:
                await self.todo_db.done(todo.todo_id)  # type: ignore

        reply = create_reply().to(command_event.user_id).text("已完成指定的待办事项。")
        return reply.build()

    async def undone(self, command_event: CommandEvent):
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
            todo_list = await self.todo_db.get_todos(command_event.user_id)
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
            await self.todo_db.undone(todo_item.todo_id)  # type: ignore
        elif command_event.parameters[1] == "all":
            todo_list = await self.todo_db.get_todos(command_event.user_id)
            if todo_list is None or len(todo_list) == 0:
                reply = (
                    create_reply()
                    .to(command_event.user_id)
                    .text("您的待办事项列表为空，无法标记为未完成。")
                )
                return reply.build()
            for todo in todo_list:
                await self.todo_db.undone(todo.todo_id)  # type: ignore

        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("已将指定的待办事项标记为未完成。")
        )
        return reply.build()

    @register_llm_tool("check_todo", description=descriptions["check_todo"])
    async def check_todo_llm(self, tool_context: LLMToolContext, arguments: dict):
        user_id = tool_context.user_id
        todos = await self.get_todos(user_id)
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
    async def create_todo_llm(self, tool_context: LLMToolContext, arguments: dict):
        content = arguments["content"]
        date = arguments.get("date")
        if date is None:
            new_todo = Todo(
                user_id=tool_context.user_id,
                content=content,
                create_time=datetime.strptime(
                    tool_context.user_send_time, "%Y-%m-%d %H:%M:%S"
                ),
            )
            async with self.todo_db.get_session() as s:
                s.add(new_todo)
                await s.commit()
                await s.refresh(new_todo)
            return f"已成功创建普通待办。内容：{new_todo.content}，创建时间{new_todo.create_time}"
        else:
            new_todo = Todo(
                user_id=tool_context.user_id,
                content=content,
                create_time=datetime.strptime(
                    tool_context.user_send_time, "%Y-%m-%d %H:%M:%S"
                ),
                notify_time=datetime.strptime(date, "%Y-%m-%d %H:%M:%S"),
            )
            async with self.todo_db.get_session() as s:
                s.add(new_todo)
                await s.commit()
                await s.refresh(new_todo)
            return f"已成功创建带有提醒的待办。内容：{new_todo.content}，创建时间{new_todo.create_time}，提醒时间{new_todo.notify_time}"

    @register_llm_tool("delete_todo", description=descriptions["delete_todo"])
    async def delete_todo_llm(self, tool_context: LLMToolContext, arguments: dict):
        todo_id_or_all = arguments.get("todo_id_or_all")
        if not isinstance(todo_id_or_all, str):
            return "请提供待办列表中的编号，或使用all删除所有待办"

        todo_list = await self.todo_db.get_todos(tool_context.user_id)
        if not todo_list:
            return "用户没有待办事项，不能删除"

        if todo_id_or_all == "all":
            for todo in todo_list:
                await self.todo_db.delete(
                    user_id=tool_context.user_id, todo_id=todo.todo_id  # type: ignore
                )
            return "已经删除用户的所有待办事项"

        if not todo_id_or_all.isdecimal():
            return "待办编号无效，请使用待办列表中的编号"
        todo_index = int(todo_id_or_all) - 1
        if todo_index < 0 or todo_index >= len(todo_list):
            return "待办编号无效，请使用待办列表中的编号"

        todo = todo_list[todo_index]
        if not await self.todo_db.delete(
            user_id=tool_context.user_id, todo_id=todo.todo_id  # type: ignore
        ):
            return "待办已不存在，请重新查看待办列表"
        return f"已经删除第{todo_index + 1}号待办：{todo.content}"

    @staticmethod
    @register_llm_tool("get_current_time", description=descriptions["get_current_time"])
    async def get_current_time(tool_context: LLMToolContext, arguments):
        return str(tool_context.user_send_time)


PLUGIN_CLASSES = (TodoHandler, TodoNotifier)

__all__ = ["TodoHandler", "TodoNotifier", "PLUGIN_CLASSES"]
