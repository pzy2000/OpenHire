"""Docker agent adapter registry."""

from __future__ import annotations

from openhire.adapters.base import DockerAgent


class AdapterRegistry:
    """Registry of available Docker agent adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, DockerAgent] = {}

    def register(self, adapter: DockerAgent) -> None:
        self._adapters[adapter.agent_name] = adapter

    def get(self, name: str) -> DockerAgent | None:
        return self._adapters.get(name)

    def names(self) -> list[str]:
        return list(self._adapters.keys())


def build_default_registry() -> AdapterRegistry:
    """Create a registry with all built-in adapters."""
    from openhire.adapters.agents.hermes import HermesAdapter
    from openhire.adapters.agents.nanobot import NanobotAdapter
    from openhire.adapters.agents.openclaw import OpenClawAdapter
    # OpenHands is intentionally disabled across OpenHire.
    # from openhire.adapters.agents.openhands import OpenHandsAdapter

    reg = AdapterRegistry()
    # OpenHandsAdapter is intentionally not registered.
    # for cls in (OpenClawAdapter, OpenHandsAdapter, HermesAdapter, NanobotAdapter):
    for cls in (OpenClawAdapter, HermesAdapter, NanobotAdapter):
        reg.register(cls())
    return reg
