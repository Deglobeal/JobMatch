"""Provider-independent interface for JobMatch AI agents."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class AIProvider(ABC):
    """Base interface that every JobMatch AI provider must implement."""

    @abstractmethod
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        """Generate and validate a structured AI response."""

        raise NotImplementedError
