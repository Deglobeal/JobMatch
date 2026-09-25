"""Google Gemini implementation of the JobMatch AI provider."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.ai.provider import AIProvider

load_dotenv(".env")


GEMINI_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-flash-lite-latest",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
]


def classify_gemini_error(error: Exception) -> str:
    """Classify a Gemini error and determine whether fallback should continue."""

    error_text = str(error).lower()

    # Authentication errors should stop immediately.
    if "401" in error_text or "unauthenticated" in error_text:
        return "STOP_AUTH"

    # Permission errors should stop immediately.
    if "403" in error_text or "permission_denied" in error_text:
        return "STOP_PERMISSION"

    # Model unavailable / not found.
    if (
        "404" in error_text
        or "not_found" in error_text
        or "not found" in error_text
        or "no longer available" in error_text
    ):
        return "NEXT_MODEL"

    # A model with zero available quota should be skipped.
    if "limit: 0" in error_text:
        return "NEXT_MODEL"

    # Temporary rate limits or service unavailability.
    if (
        "429" in error_text
        or "resource_exhausted" in error_text
        or "503" in error_text
        or "service_unavailable" in error_text
        or "temporarily unavailable" in error_text
    ):
        return "NEXT_MODEL"

    # Gemini successfully responded but did not produce the
    # structured response required by JobMatch.
    if "no structured response" in error_text:
        return "NEXT_MODEL"

    # Unknown errors should stop rather than blindly cycling
    # through every model.
    return "STOP_UNKNOWN"


class GeminiProvider(AIProvider):
    """Generate structured responses using Google Gemini with model fallback."""

    def __init__(
        self,
        model: str | None = None,
        models: list[str] | None = None,
    ):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured"
            )

        self.client = genai.Client(api_key=api_key)

        # Backward compatibility:
        # if an existing caller supplies `model=...`, use that model
        # first and then continue through the fallback chain.
        if model:
            self.models = [
                model,
                *[candidate for candidate in GEMINI_MODELS if candidate != model],
            ]
        elif models:
            self.models = list(models)
        else:
            self.models = list(GEMINI_MODELS)

        # Preserve the previous public attribute.
        self.model = self.models[0]

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Generate a structured response using Gemini model fallback."""

        last_error: Exception | None = None

        for index, model in enumerate(self.models, start=1):
            print(
                f"[GeminiProvider] Trying model "
                f"{index}/{len(self.models)}: {model}"
            )

            try:
                response = await self.client.aio.models.generate_content(
                    model=model,
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

                print(
                    f"[GeminiProvider] Success with model: {model}"
                )

                return response.parsed

            except Exception as error:
                last_error = error
                decision = classify_gemini_error(error)

                print(
                    f"[GeminiProvider] Model failed: {model}"
                )
                print(
                    f"[GeminiProvider] Error: {error}"
                )
                print(
                    f"[GeminiProvider] Decision: {decision}"
                )

                if decision != "NEXT_MODEL":
                    raise

        if last_error is not None:
            raise RuntimeError(
                "All configured Gemini models failed."
            ) from last_error

        raise RuntimeError(
            "No Gemini models are configured."
        )
