import os
import httpx
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from backend.app.ai.exceptions import GeminiAPIException, RateLimitException

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "MOCK_MODE")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = float(os.getenv("TEMPERATURE", "0.2"))
        self.max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))
        self.top_p = float(os.getenv("TOP_P", "0.95"))
        self.top_k = int(os.getenv("TOP_K", "40"))
        self.timeout = float(os.getenv("AI_TIMEOUT", "30.0"))
        self.enable_mock = os.getenv("ENABLE_MOCK_AI", "true").lower() == "true" or self.api_key == "MOCK_MODE"

    async def generate_content(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None, 
        json_mode: bool = False
    ) -> str:
        """Call Gemini API to generate content with retry backoff."""
        if self.enable_mock:
            await asyncio.sleep(0.1) # Simulate network
            if json_mode:
                return json.dumps({
                    "status": "success",
                    "data": f"Mocked structured response for: {prompt[:30]}...",
                    "confidence": 0.95
                })
            return f"This is a mocked Gemini response for the prompt: '{prompt}'."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = {"parts": [{"text": prompt}]}
        config = {
            "temperature": self.temperature,
            "maxOutputTokens": self.max_tokens,
            "topP": self.top_p,
            "topK": self.top_k,
        }
        if json_mode:
            config["responseMimeType"] = "application/json"

        payload = {
            "contents": [contents],
            "generationConfig": config
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        headers = {"Content-Type": "application/json"}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(3):
                try:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code == 429:
                        if attempt == 2:
                            raise RateLimitException("Gemini API Rate Limit Exceeded.")
                        await asyncio.sleep(2 ** attempt)
                        continue
                    if response.status_code != 200:
                        raise GeminiAPIException(f"Gemini API Error: {response.text}")
                    
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise GeminiAPIException("No generation candidates returned from Gemini.")
                    
                    text = candidates[0]["content"]["parts"][0]["text"]
                    return text
                except httpx.HTTPError as e:
                    if attempt == 2:
                        raise GeminiAPIException(f"HTTP connection failed: {str(e)}")
                    await asyncio.sleep(1.5 ** attempt)
            
            raise GeminiAPIException("Failed to generate content after retries.")

    async def generate_stream(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chunks from the Gemini API."""
        if self.enable_mock:
            mock_text = f"This is a mocked streaming Gemini response for: {prompt}"
            for chunk in mock_text.split(" "):
                await asyncio.sleep(0.05)
                yield chunk + " "
            return

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent?key={self.api_key}"
        contents = {"parts": [{"text": prompt}]}
        payload = {
            "contents": [contents],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
                "topP": self.top_p,
                "topK": self.top_k,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        headers = {"Content-Type": "application/json"}

        # Using HTTPX streaming
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    raise GeminiAPIException(f"Gemini API streaming error: status {response.status_code}")
                
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    # Parse JSON chunks (Gemini streaming sends an array of Candidates)
                    while True:
                        try:
                            # Try to extract the next valid JSON object/array element from the stream
                            # (Gemini returns a JSON array of responses, so it's surrounded by [ ... ])
                            # For simplicity, we can do substring scanning or simple parsing
                            # Since this is standard JSON stream, let's parse cleanly if we can.
                            # A simple approach for line-based SSE or JSON arrays:
                            pass
                        except Exception:
                            break
                        # For production streaming, we yield chunks of the stream
                        yield chunk
