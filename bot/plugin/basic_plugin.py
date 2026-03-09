class BasicPlugin:
    """所有插件的基类

    本基类设计目的是简单，目前只用于使用__subclasses__来实例化插件类然后注册方法
    """

    def __init__(self) -> None:
        pass
