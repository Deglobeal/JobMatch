"""Groq implementation of the JobMatch AI provider."""

import json
import os

from dotenv import load_dotenv
from groq import AsyncGroq
from pydantic import BaseModel

from app.ai.provider import AIProvider

load_dotenv(".env")


class GroqProvider(AIProvider):
    """Generate structured responses using Groq."""

    def __init__(self, model: str = "openai/gpt-oss-120b"):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured"
            )

        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Generate and validate a structured response."""

        schema = response_model.model_json_schema()

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": schema,
                },
            },
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "Groq returned no structured response."
            )

        try:
            return response_model.model_validate(
                json.loads(content)
            )
        except (json.JSONDecodeError, ValueError) as error:
            raise RuntimeError(
                "Groq returned an invalid structured response."
            ) from error
