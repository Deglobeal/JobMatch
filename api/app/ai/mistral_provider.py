"""Mistral implementation of the JobMatch AI provider."""

import json
import os

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

from app.ai.provider import AIProvider

load_dotenv(".env")


class MistralProvider(AIProvider):
    """Generate structured responses using the Mistral API."""

    def __init__(self, model: str = "mistral-small-latest"):
        api_key = os.getenv("MISTRAL_API_KEY")

        if not api_key:
            raise RuntimeError(
                "MISTRAL_API_KEY is not configured"
            )

        self.api_key = api_key
        self.model = model

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Generate and validate a structured response."""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": response_model.model_json_schema(),
                },
            },
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Mistral API error ({response.status_code}): "
                f"{response.text[:500]}"
            )

        data = response.json()

        content = data["choices"][0]["message"]["content"]

        if not content:
            raise RuntimeError(
                "Mistral returned no structured response."
            )

        try:
            return response_model.model_validate(
                json.loads(content)
            )
        except (json.JSONDecodeError, ValueError) as error:
            raise RuntimeError(
                "Mistral returned an invalid structured response."
            ) from error
