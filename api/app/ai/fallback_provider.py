"""Fallback AI provider that tries multiple providers in order."""

from pydantic import BaseModel

from app.ai.provider import AIProvider


class FallbackAIProvider(AIProvider):
    """Try providers sequentially until one succeeds."""

    def __init__(self, providers: list[AIProvider]):
        if not providers:
            raise ValueError("At least one AI provider is required.")

        self.providers = providers

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Try each provider in order and return the first successful result."""

        errors: list[str] = []

        for provider in self.providers:
            try:
                return await provider.generate_structured(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=response_model,
                )
            except Exception as error:
                errors.append(
                    f"{type(provider).__name__}: {error}"
                )

        raise RuntimeError(
            "All configured AI providers failed. "
            + " | ".join(errors)
        )
