import asyncio
import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    messages = body.get("messages", [])

    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            parts = msg.get("parts", [])
            for part in parts:
                if part.get("type") == "text":
                    last_user_msg = part["text"]
                    break
            if not last_user_msg:
                last_user_msg = msg.get("content", "")
            break

    async def generate():
        response = (
            f"You said: {last_user_msg}\n\n"
            "This is a mock response from the LifeInk AI backend. "
            "Replace this with your LLM provider integration."
        )
        for char in response:
            yield char
            await asyncio.sleep(0.02)

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
