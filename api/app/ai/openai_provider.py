"""OpenAI implementation of the JobMatch AI provider."""

import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.ai.provider import AIProvider

load_dotenv(".env")


class OpenAIProvider(AIProvider):
    """Generate structured responses using OpenAI."""

    def __init__(self, model: str = "gpt-5.6-luna"):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured"
            )

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Generate a response validated against a Pydantic model."""

        response = await self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            text_format=response_model,
        )

        if response.output_parsed is None:
            raise RuntimeError(
                "OpenAI returned no structured response."
            )

        return response.output_parsed
