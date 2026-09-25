import asyncio
import os
from typing import Type

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel


load_dotenv(".env")


# ============================================================
# VERIFIED GEMINI / GOOGLE MODELS
# ============================================================

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


# ============================================================
# TEST RESPONSE SCHEMA
# ============================================================

class TestResponse(BaseModel):
    answer: str


# ============================================================
# ERROR CLASSIFICATION
# ============================================================

def classify_gemini_error(error: Exception) -> str:
    """Determine whether the fallback should try another model."""

    error_text = str(error).lower()

    # Authentication/configuration problems should stop immediately.
    if any(
        phrase in error_text
        for phrase in (
            "401",
            "unauthenticated",
            "invalid api key",
            "api key not valid",
        )
    ):
        return "STOP_AUTH"

    # Permission problems should stop immediately.
    if any(
        phrase in error_text
        for phrase in (
            "403",
            "permission_denied",
            "permission denied",
        )
    ):
        return "STOP_PERMISSION"

    # A model that does not exist or is not available for this API
    # should be skipped permanently.
    if any(
        phrase in error_text
        for phrase in (
            "404",
            "not_found",
            "not found",
            "is no longer available",
        )
    ):
        return "NEXT_MODEL"

    # A quota of zero means this model cannot be used on the
    # current free-tier configuration.
    if "limit: 0" in error_text:
        return "NEXT_MODEL"

    # Temporary rate limiting or service unavailability should
    # allow the fallback chain to continue.
    if any(
        phrase in error_text
        for phrase in (
            "429",
            "resource_exhausted",
            "503",
            "service_unavailable",
            "temporarily unavailable",
        )
    ):
        return "NEXT_MODEL"

    # A successful API call that produced no structured response
    # should try the next model.
    if "no structured response" in error_text:
        return "NEXT_MODEL"

    # Unknown errors should stop rather than blindly cycling
    # through every model.
    return "STOP_UNKNOWN"



# ============================================================
# GEMINI FALLBACK TEST
# ============================================================

class GeminiFallbackTest:
    def __init__(self, models: list[str]):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        self.client = genai.Client(api_key=api_key)
        self.models = models

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
    ) -> BaseModel:

        failures = []

        for index, model in enumerate(self.models, start=1):

            print()
            print("=" * 70)
            print(f"TRYING MODEL {index}/{len(self.models)}")
            print(f"MODEL: {model}")
            print("=" * 70)

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

                print()
                print(f"SUCCESS: {model}")
                print(f"RESULT: {response.parsed.model_dump()}")

                return response.parsed

            except Exception as error:
                error_text = str(error)

                failures.append(
                    {
                        "model": model,
                        "error_type": type(error).__name__,
                        "error": error_text,
                    }
                )

                print()
                print(f"FAILED: {model}")
                print(f"ERROR TYPE: {type(error).__name__}")
                print(f"ERROR: {error_text}")

                print()
                print("Moving to next Gemini model...")

        print()
        print("=" * 70)
        print("ALL GEMINI MODELS FAILED")
        print("=" * 70)

        for failure in failures:
            print()
            print(f"MODEL: {failure['model']}")
            print(f"TYPE:  {failure['error_type']}")
            print(f"ERROR: {failure['error']}")

        raise RuntimeError(
            f"All {len(self.models)} Gemini models failed."
        )


# ============================================================
# MAIN TEST
# ============================================================

async def main():

    print()
    print("=" * 70)
    print("JOBMATCH GEMINI FALLBACK TEST")
    print("=" * 70)

    print()
    print("Models in fallback chain:")

    for index, model in enumerate(GEMINI_MODELS, start=1):
        print(f"{index}. {model}")

    fallback = GeminiFallbackTest(GEMINI_MODELS)

    result = await fallback.generate_structured(
        system_prompt=(
            "You are a test AI provider. "
            "Return valid JSON matching the requested schema."
        ),
        user_prompt=(
            "Respond with the word OK in the answer field."
        ),
        response_model=TestResponse,
    )

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print(result.model_dump())


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================
# ERROR CLASSIFIER TEST
# ============================================================

def test_error_classifier():
    test_cases = [
        (
            "404 NOT_FOUND. model is no longer available",
            "NEXT_MODEL",
        ),
        (
            "429 RESOURCE_EXHAUSTED. quota exceeded, limit: 0",
            "NEXT_MODEL",
        ),
        (
            "503 UNAVAILABLE. high demand",
            "NEXT_MODEL",
        ),
        (
            "429 RESOURCE_EXHAUSTED. temporary rate limit",
            "NEXT_MODEL",
        ),
        (
            "401 UNAUTHENTICATED. API key is invalid",
            "STOP_AUTH",
        ),
        (
            "403 PERMISSION_DENIED. permission denied",
            "STOP_PERMISSION",
        ),
        (
            "Gemini returned no structured response.",
            "NEXT_MODEL",
        ),
        (
            "Unexpected SDK parsing error",
            "STOP_UNKNOWN",
        ),
    ]

    print()
    print("=" * 70)
    print("ERROR CLASSIFIER TEST")
    print("=" * 70)

    failed = False

    for error_message, expected in test_cases:
        actual = classify_gemini_error(
            RuntimeError(error_message)
        )

        status = "PASS" if actual == expected else "FAIL"

        print()
        print(f"[{status}]")
        print(f"ERROR:    {error_message}")
        print(f"EXPECTED: {expected}")
        print(f"ACTUAL:   {actual}")

        if actual != expected:
            failed = True

    print()

    if failed:
        raise AssertionError(
            "One or more error-classifier tests failed."
        )

    print("ALL CLASSIFIER TESTS PASSED")


if __name__ == "__main__":
    test_error_classifier()


# ============================================================
# CONTROLLED FALLBACK LOOP TEST
# ============================================================

class FakeGeminiClient:
    """Simulates Gemini responses without making API calls."""

    def __init__(self, behaviors):
        self.behaviors = behaviors
        self.calls = []

    async def generate(self, model):
        self.calls.append(model)

        behavior = self.behaviors.get(model)

        if behavior is None:
            raise RuntimeError("No behavior configured")

        if behavior == "success":
            return TestResponse(answer="OK")

        raise RuntimeError(behavior)


async def test_controlled_fallback_loop():

    print()
    print("=" * 70)
    print("CONTROLLED FALLBACK LOOP TEST")
    print("=" * 70)

    fake_models = [
        "fake-model-404",
        "fake-model-503",
        "fake-model-success",
    ]

    fake = FakeGeminiClient(
        {
            "fake-model-404": "404 NOT_FOUND. model unavailable",
            "fake-model-503": "503 UNAVAILABLE. high demand",
            "fake-model-success": "success",
        }
    )

    result = None

    for model in fake_models:

        print()
        print(f"TRYING: {model}")

        try:
            result = await fake.generate(model)

            print(f"SUCCESS: {model}")
            break

        except Exception as error:

            decision = classify_gemini_error(error)

            print(f"FAILED: {model}")
            print(f"DECISION: {decision}")

            if decision != "NEXT_MODEL":
                raise AssertionError(
                    f"Fallback should have continued, got {decision}"
                )

    assert result is not None
    assert result.answer == "OK"

    assert fake.calls == [
        "fake-model-404",
        "fake-model-503",
        "fake-model-success",
    ]

    print()
    print("CONTROLLED FALLBACK TEST PASSED")
    print(f"CALL ORDER: {fake.calls}")


async def test_controlled_stop():

    print()
    print("=" * 70)
    print("CONTROLLED STOP TEST")
    print("=" * 70)

    fake_models = [
        "fake-model-auth-error",
        "fake-model-should-not-run",
    ]

    fake = FakeGeminiClient(
        {
            "fake-model-auth-error": (
                "401 UNAUTHENTICATED. API key is invalid"
            ),
            "fake-model-should-not-run": "success",
        }
    )

    for model in fake_models:

        print()
        print(f"TRYING: {model}")

        try:
            await fake.generate(model)

        except Exception as error:

            decision = classify_gemini_error(error)

            print(f"FAILED: {model}")
            print(f"DECISION: {decision}")

            if decision != "NEXT_MODEL":
                print("Fallback correctly stopped.")
                break

    assert fake.calls == [
        "fake-model-auth-error",
    ]

    print()
    print("CONTROLLED STOP TEST PASSED")
    print(f"CALL ORDER: {fake.calls}")


if __name__ == "__main__":
    asyncio.run(test_controlled_fallback_loop())
    asyncio.run(test_controlled_stop())


# ============================================================
# STRUCTURED OUTPUT FAILURE TEST
# ============================================================

class FakeStructuredGeminiClient:
    """Simulates structured-output success and failure."""

    def __init__(self, behaviors):
        self.behaviors = behaviors
        self.calls = []

    async def generate(self, model):
        self.calls.append(model)

        behavior = self.behaviors.get(model)

        if behavior == "empty":
            raise RuntimeError(
                "Gemini returned no structured response."
            )

        if behavior == "success":
            return TestResponse(answer="OK")

        raise RuntimeError(
            behavior or "Unknown simulated error"
        )


async def test_structured_output_fallback():

    print()
    print("=" * 70)
    print("STRUCTURED OUTPUT FALLBACK TEST")
    print("=" * 70)

    fake_models = [
        "fake-model-empty-response",
        "fake-model-success",
    ]

    fake = FakeStructuredGeminiClient(
        {
            "fake-model-empty-response": "empty",
            "fake-model-success": "success",
        }
    )

    result = None

    for model in fake_models:

        print()
        print(f"TRYING: {model}")

        try:
            result = await fake.generate(model)

            print(f"SUCCESS: {model}")
            print(f"RESULT: {result.model_dump()}")
            break

        except Exception as error:

            decision = classify_gemini_error(error)

            print(f"FAILED: {model}")
            print(f"ERROR: {error}")
            print(f"DECISION: {decision}")

            if decision != "NEXT_MODEL":
                raise AssertionError(
                    f"Expected fallback to continue, got {decision}"
                )

    assert result is not None
    assert result.answer == "OK"

    assert fake.calls == [
        "fake-model-empty-response",
        "fake-model-success",
    ]

    print()
    print("STRUCTURED OUTPUT FALLBACK TEST PASSED")
    print(f"CALL ORDER: {fake.calls}")


if __name__ == "__main__":
    asyncio.run(test_structured_output_fallback())
