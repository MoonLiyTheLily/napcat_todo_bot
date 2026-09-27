class BasicPlugin:
    """所有插件的基类

    入口模块通过 PLUGIN_CLASSES 显式声明需要加载的插件类。
    """

    def __init__(self) -> None:
        pass

    async def initialize(self) -> None:
        """异步初始化方法，插件可重写此方法进行异步初始化"""

    async def shutdown(self) -> None:
        """异步卸载方法，插件可重写此方法进行异步卸载"""
