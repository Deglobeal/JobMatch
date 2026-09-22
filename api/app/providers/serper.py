import os

import httpx
from dotenv import load_dotenv


load_dotenv(".env")


class SerperSearchProvider:
    """Search Google results through the Serper API."""

    BASE_URL = "https://google.serper.dev/search"

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")

        if not self.api_key:
            raise RuntimeError("SERPER_API_KEY is not configured")

    async def search(self, query: str, num: int = 10) -> list[dict]:
        """Search Google through Serper and return organic results."""

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "q": query,
            "num": num,
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
            )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Serper API error {response.status_code}: "
                f"{response.text}"
            )

        data = response.json()

        return data.get("organic", [])
