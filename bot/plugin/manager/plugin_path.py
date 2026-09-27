import os

@staticmethod
def get_bot_root():
    return os.path.realpath(os.getcwd())


def get_builtin_plugin_path():
    return os.path.realpath(os.path.join(get_bot_root(), "bot", "plugin", "builtin"))


def get_other_plugin_path():
    return os.path.realpath(os.path.join(get_bot_root(), "bot", "plugin", "other"))


def get_config_path():
    return os.path.realpath(os.path.join(get_bot_root(), "config"))