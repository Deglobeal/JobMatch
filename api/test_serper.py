import asyncio

from app.providers.serper import SerperSearchProvider


async def main():
    provider = SerperSearchProvider()

    results = await provider.search(
        "Junior Python Backend Developer remote jobs",
        num=5,
    )

    for result in results:
        print(result.get("title"))
        print(result.get("link"))
        print(result.get("snippet", ""))
        print("---")


asyncio.run(main())
