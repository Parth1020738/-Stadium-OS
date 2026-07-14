import json
from typing import AsyncGenerator

class StreamingService:
    @staticmethod
    async def format_sse_stream(generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """Convert standard token/string stream to Server-Sent Events format."""
        try:
            async for chunk in generator:
                if chunk:
                    data = {"text": chunk}
                    yield f"data: {json.dumps(data)}\n\n"
            # Signal the end of stream
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
