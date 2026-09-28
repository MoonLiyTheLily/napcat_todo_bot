# Napcat Todo Bot

本项目是一个基于NapcatQQ框架的QQ机器人。主要功能为待办列表。
## 运行
本项目使用uv管理依赖。请先安装uv。

随后，Clone此项目：
```
git clone https://github.com/MoonLiyTheLily/napcat_todo_bot.git
```
安装依赖：
```
cd napcat_todo_bot
uv sync
```
随后，可能还需要创建配置文件：
```
cp bot/config/config_example.json bot/config/config.json
```
如果需要使用大模型聊天，请编辑配置文件，将`llm`下的`enable`改为`true`，随后更改`config.json`或项目根目录下`.env`里的`api_key`，并设置`base_url`和`admin_user_id`。

`.env`的`api_key`、`base_url`和`admin_user_id`具有更高优先级，会覆盖从`config.json`中读取到的设置。

随后，启动NapcatQQ，创建一个Websocket Client，URL设置为`ws://localhost:8000`（本项目端口默认为`8000`），上报自身消息可设为关闭。消息格式请设为`Array`。

最后，使用如下命令启动本程序：
```
uv run ./main.py
```


## 开发简述
简单的机器人，开发的初衷是为了给自己写一个Todo机器人，后来是为了熟悉Python和Python的项目组织架构，也是学习AstrBot项目的机会，虽然我现在还看不太懂。

目前支持待办的创建、删除、完成，以及自然语言创建和删除。提醒分为两种独立功能：周期发送所有未完成待办的汇总；在待办指定的提醒时间到达后，发送一次该待办的提醒。太久没回复机器人会触发重力文案，大概是彩蛋。

### 待办提醒

- `active.todo.notify_interval` 是未完成待办汇总的发送间隔，单位为秒。示例值 `1800` 表示 30 分钟；任务启动时也会立即检查并发送一次。
- 带 `notify_time` 的待办由独立任务每 30 秒检查一次。到期、未完成且尚未发送的待办会按用户合并发送。发送失败时保留待办，下次检查重试；发送时间直接记录在该待办的 `reminder_sent_at` 字段中，重启后不会再次提醒。同一待办仍会出现在周期汇总中。
- 待办表对用户列表、未完成汇总和到期提醒分别建有索引。此版本不包含数据库迁移代码；其他已有开发数据库需重建或手动更新字段与索引。
- 时间按运行机器的本地时区解释。发送成功指消息已写入 WebSocket；目前尚未核对 NapCat 或 QQ 的最终投递回执。
- `active.gravity.check_interval` 也以秒为单位，示例值 `3600` 表示 1 小时。

预期添加功能：

1. done 根据Todo指定时间单独通知
2. done 接入大模型聊天
3. doing 接入大模型以自然语言创建、删除、完成Todo
4. 自动清理过时Todo（由用户选择是否启用）
5. doing 提供一个在聊天窗口修改配置的功能

预期项目优化：

1. done 统一的Sender
2. done 自动的插件加载
3. oing 统一的配置文件
4. 更多的重力文案
5. doing 梳理数据库文件，提供统一的数据库接口供继承（尚在考虑）
6. doing 添加一个通用的数据库操作接口
7. 减少消息处理层await的层数
8. 改进错误处理，梳理层次
9. 增加可注册指令组的功能，自动路由子指令，不需要插件自己处理
10. done 为插件自动提供上下文，包括框架的各种状态等等
11. LLM支持保存记录到文件，以免重启了记录全丢
12. 支持LLM Tool为LLM添加上下文要求，例如Todo可以给LLM提供当前时间等等（尚在考虑）
13. doing 改用ORM

远期规划：

1. 升级为使用事件队列处理，设计基本事件类和各种子类
2. LLM插件化、解耦合，并随时开关（尚在考虑）
3. 配置管理器
4. 设计消息类
5. 升级为支持处理群聊消息（可开关）
6. doing 增加生命周期管理类
7. doing 优化热重载功能
8. 提供一个简易的Webui，不打算做得很复杂但是应该至少不需要改代码来改动配置

## 插件入口约定

每个插件放在 `bot/plugin/builtin/<插件名>/` 或 `bot/plugin/other/<插件名>/`，入口文件为 `main.py` 或 `<插件名>.py`。入口模块需要声明 `PLUGIN_CLASSES`，列出该目录中要加载的所有 `BasicPlugin` 子类；一个目录可以包含多个插件类，例如待办插件同时包含命令处理器和通知器：

```python
PLUGIN_CLASSES = (TodoHandler, TodoNotifier)
```

插件管理器会为每个目录保留一条记录，并按声明顺序实例化、初始化这些类；整个插件初始化成功后才注册其方法。类没有出现在 `PLUGIN_CLASSES` 中就不会被加载。

命令、LLM 工具和主动任务的装饰器只声明元数据；插件初始化成功后，`PluginManager` 调用 `registers.py` 中对应的函数写入注册表。这些函数接收插件实例列表，采用增量注册；完整重建前需先清空对应注册表。

插件可以重写 `BasicPlugin.shutdown()` 释放资源。机器人退出时会先停止主动任务，再按加载的逆序等待各插件的 `shutdown()` 完成。
