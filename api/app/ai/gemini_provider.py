"""Google Gemini implementation of the JobMatch AI provider."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.ai.provider import AIProvider

load_dotenv(".env")


class GeminiProvider(AIProvider):
    """Generate structured responses using Google Gemini."""

    def __init__(self, model: str = "gemini-3.5-flash"):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured"
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Generate a response validated against a Pydantic model."""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_model,
            ),
        )

        if not response.parsed:
            raise RuntimeError(
                "Gemini returned no structured response."
            )

        return response.parsed
