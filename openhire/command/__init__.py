"""Slash command routing and built-in handlers."""

from openhire.command.builtin import register_builtin_commands
from openhire.command.router import CommandContext, CommandRouter

__all__ = ["CommandContext", "CommandRouter", "register_builtin_commands"]
