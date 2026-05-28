import httpx
from common import settings


class GeminiService:
    async def generate(self, prompt: str) -> str:
        if not settings.gemini_api_key:
            return self._mock_response()

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        params = {"key": settings.gemini_api_key}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def _mock_response(self) -> str:
        return (
            "Title: Mock Script\\nEstimated duration: 150s\\nHook: Stop scrolling—this will save you hours.\\n"
            "Timestamped script: 0:00 [excited] ...\\nCTA: Follow for part 2."
        )
