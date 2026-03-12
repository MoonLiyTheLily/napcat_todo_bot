from bot.plugin.manager.plugin_registry import register_command
from bot.llm.llm_tool_registry import register_llm_tool
from bot.active.active_registry import register_active

__all__ = ["register_command", "register_llm_tool", "register_active"]
