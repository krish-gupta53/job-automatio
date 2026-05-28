import httpx
from app.core.config import settings


class GeminiService:
    """Small wrapper. Replace with Vertex AI SDK or Google ADK during final integration."""

    async def generate(self, prompt: str) -> str:
        if not settings.gemini_api_key:
            return self._mock_response(prompt)

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-1.5-flash:generateContent"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        params = {"key": settings.gemini_api_key}
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def _mock_response(self, prompt: str) -> str:
        return (
            "MOCK_GEMINI_RESPONSE: Add GEMINI_API_KEY to enable real generation.\n\n"
            "Generated script will include hook, timestamps, emotion, pauses, B-roll, captions, CTA, "
            "and learning-based reasoning."
        )
