"""Message bus module for decoupled channel-agent communication."""

from openhire.bus.events import InboundMessage, OutboundMessage
from openhire.bus.queue import MessageBus

__all__ = ["MessageBus", "InboundMessage", "OutboundMessage"]
