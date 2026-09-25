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

        def make_strict_schema(value):
            if isinstance(value, dict):
                if value.get("type") == "object":
                    value["additionalProperties"] = False
                    properties = value.get("properties", {})
                    value["required"] = list(properties.keys())
                    for property_schema in properties.values():
                        make_strict_schema(property_schema)

                for key in ("items", "anyOf", "oneOf", "allOf"):
                    nested = value.get(key)
                    if isinstance(nested, dict):
                        make_strict_schema(nested)
                    elif isinstance(nested, list):
                        for item in nested:
                            make_strict_schema(item)

                for key, nested in value.items():
                    if key not in {
                        "properties",
                        "items",
                        "anyOf",
                        "oneOf",
                        "allOf",
                    } and isinstance(nested, dict):
                        make_strict_schema(nested)

            elif isinstance(value, list):
                for item in value:
                    make_strict_schema(item)

        make_strict_schema(schema)

        print(
            "GROQ REQUEST:",
            {
                "response_model": response_model.__name__,
                "system_prompt_chars": len(system_prompt),
                "user_prompt_chars": len(user_prompt),
                "schema_chars": len(json.dumps(schema)),
                "total_input_chars": (
                    len(system_prompt)
                    + len(user_prompt)
                    + len(json.dumps(schema))
                ),
                "max_completion_tokens": 7000,
            },
        )

        try:
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
                reasoning_effort="low",
                max_completion_tokens=7000,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_model.__name__,
                        "strict": True,
                        "schema": schema,
                    },
                },
            )
        except Exception as error:
            print(
                f"Groq structured-output request failed: "
                f"{type(error).__name__}: {error}"
            )
            raise

        print(
            "GROQ USAGE:",
            {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
                "completion_tokens": getattr(response.usage, "completion_tokens", None),
                "total_tokens": getattr(response.usage, "total_tokens", None),
                "finish_reason": getattr(response.choices[0], "finish_reason", None),
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
