"""3D model generation provider base class and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ModelResult:
    """Result from a 3D model generation or query."""
    task_id: str = ""
    status: str = ""  # "processing", "success", "failed"
    model_url: str = ""  # primary download URL (GLB)
    model_urls: dict[str, str] = field(default_factory=dict)  # format -> URL
    thumbnail_url: str = ""
    error: str = ""


class BaseProvider(ABC):
    """Abstract base class for 3D model generation providers."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def free_tier_info(self) -> str: ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        image_url: str | None = None,
        output_format: str = "glb",
    ) -> ModelResult: ...

    @abstractmethod
    async def query(self, task_id: str) -> ModelResult: ...


# --- Provider registry ---

_providers: dict[str, BaseProvider] = {}


def register_provider(provider: BaseProvider) -> None:
    _providers[provider.name] = provider


def get_provider(name: str) -> BaseProvider | None:
    return _providers.get(name)


def list_providers() -> dict[str, BaseProvider]:
    return dict(_providers)
