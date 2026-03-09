import sys
from bot.plugin.basic_plugin import BasicPlugin

command_registry = {}


def register_command(command: str):
    """指定命令，将函数注册为命令处理器

    返回一个装饰器，这个装饰器会给函数添加一个__command_name__属性
    """

    def decorator(func):
        func.__command_name__ = command
        return func

    return decorator


def clear_registry():
    """用于重载插件的时候提前clear"""

    command_registry.clear()


def auto_register():
    """自动扫描import的所有插件，并注册里面的方法"""

    command_registry.clear()
    plugin_class_list = BasicPlugin.__subclasses__()
    for cls in plugin_class_list:

        # 验证该类是否是模块中当前最新（存活）的类，防止重载带来的旧类滞留
        # Gemini写的，主要是为了防止那个PluginManagerInterface在重载插件的时候没把自己正确销毁
        module = sys.modules.get(cls.__module__)
        if not module or getattr(module, cls.__name__, None) is not cls:
            continue

        # 实例化这个类，然后注册它底下所有的命令
        instance = cls()
        for attr_name in dir(instance):
            attr = getattr(instance, attr_name)
            if callable(attr) and hasattr(attr, "__command_name__"):
                command_registry[attr.__command_name__] = attr
