import logging
from bot.types import CommandEvent, TodoItem
from bot.apis.create_reply import create_reply
from database import TodoDatabase

logger = logging.getLogger(__name__)


class TodoHandler:
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

    async def handle(self, command_event: CommandEvent):
        """
        处理todo命令的函数

        :param user_id: 用户id
        :type user_id: str
        :param parameters: 解析获得的参数
        :type parameters: list
        """
        logger.info("handle已执行")

        if len(command_event.parameters) == 0:
            handler = self.parameter_handlers["default"]
            logger.info("第一参数: None")
        else:
            param = command_event.parameters[0]
            handler = self.parameter_handlers.get(
                param, self.parameter_handlers["parameter_not_found"]
            )
            logger.info("第一参数: %s", param)

        if handler is not None:
            reply = handler(command_event)
        else:
            # reply = {
            #     "action": "send_private_msg",
            #     "params": {
            #         "user_id": command_event.user_id,
            #         "message": "todo_handler已执行，但未找到对应的处理函数。",
            #     },
            # }
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("todo_handler已执行，但未找到对应的处理函数。")
                .build()
            )

        return reply

    def help(self, command_event: CommandEvent):
        """
        显示待办事项的帮助信息
        """
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
        """
        处理未知参数的函数
        """
        # reply = {
        #     "action": "send_private_msg",
        #     "params": {
        #         "user_id": command_event.user_id,
        #         "message": {
        #             "type": "text",
        #             "data": {
        #                 "text": "未知的todo命令参数\n请使用/todo help获取帮助信息。"
        #             },
        #         },
        #     },
        # }
        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("未知的todo命令参数\n请使用/todo help获取帮助信息。")
        )
        return reply.build()

    def default(self, command_event: CommandEvent):
        """
        处理无参数情况的函数
        """
        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("默认todo_handler已执行\n您可以采用/todo help获取帮助信息。")
        )
        return reply.build()

    def get_todos(self, user_id: str):
        """
        获取用户的待办事项列表，并且是直接获得字符串列表

        :param user_id: 用户id
        :type user_id: str
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
        """
        显示用户的待办事项列表
        """
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
        """
        添加新的待办事项
        """
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
        self.todo_db.commit_operation()
        return reply.build()

    def delete(self, command_event: CommandEvent):
        """
        删除指定的待办事项
        用户指定的是待办的编号，从1开始。待办编号是“此用户的第几个待办”，而不是总数据库里的id
        """
        if len(command_event.parameters) < 2:
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("请提供要删除的待办事项编号。")
            )
            return reply.build()
        if not command_event.parameters[1].isdigit():
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("待办事项编号必须是数字。")
            )
            return reply.build()

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

        reply = create_reply().to(command_event.user_id).text("已删除指定的待办事项。")
        self.todo_db.commit_operation()
        return reply.build()

    def done(self, command_event: CommandEvent):
        """
        标记指定的待办事项为已完成
        用户指定的是待办的编号，从1开始。待办编号是“此用户的第几个待办”，而不是总数据库里的id
        """
        if len(command_event.parameters) < 2:
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("请提供要标记为完成的待办事项编号。")
            )
            return reply.build()
        if not command_event.parameters[1].isdigit():
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("待办事项编号必须是数字。")
            )
            return reply.build()

        todo_index = int(command_event.parameters[1]) - 1

        todo_list = self.todo_db.check_todo(command_event.user_id)
        if todo_list is None or len(todo_list) == 0:
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("您的待办事项列表为空，无法标记完成。")
            )
            return reply.build()

        if todo_index < 0 or todo_index >= len(todo_list):
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("待办事项编号无效，无法标记完成。")
            )
            return reply.build()

        todo_item = todo_list[todo_index]
        assert isinstance(todo_item, TodoItem)
        self.todo_db.complete_todo(
            command_event.user_id,
            todo_item.database_id,
            command_event.user_send_time,
        )
        self.todo_db.commit_operation()

        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("已将指定的待办事项标记为完成。")
        )
        return reply.build()

    def undone(self, command_event: CommandEvent):
        """
        标记指定的待办事项为未完成
        用户指定的是待办的编号，从1开始。待办编号是“此用户的第几个待办”，而不是总数据库里的id
        """
        if len(command_event.parameters) < 2:
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("请提供要标记为未完成的待办事项编号。")
            )
            return reply.build()
        if not command_event.parameters[1].isdigit():
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("待办事项编号必须是数字。")
            )
            return reply.build()

        todo_index = int(command_event.parameters[1]) - 1

        todo_list = self.todo_db.check_todo(command_event.user_id)
        if todo_list is None or len(todo_list) == 0:
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("您的待办事项列表为空，无法标记未完成。")
            )
            return reply.build()
        if todo_index < 0 or todo_index >= len(todo_list):
            reply = (
                create_reply()
                .to(command_event.user_id)
                .text("待办事项编号无效，无法标记未完成。")
            )
            return reply.build()

        todo_item = todo_list[todo_index]
        assert isinstance(todo_item, TodoItem)
        self.todo_db.uncomplete_todo(
            command_event.user_id,
            todo_item.database_id,
        )
        self.todo_db.commit_operation()

        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("已将指定的待办事项标记为未完成。")
        )
        return reply.build()
