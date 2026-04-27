"""Chat channels module with plugin architecture."""

from openhire.channels.base import BaseChannel
from openhire.channels.manager import ChannelManager

__all__ = ["BaseChannel", "ChannelManager"]
