import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_default_user, get_session, init_db
from db.repository import CommunityMetaRepo, DataRepo
from src.api.douban import supported_platforms, AsyncBindManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Chat ----


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


# ---- Platform Binding ----

PLATFORMS = supported_platforms()


@app.post("/api/community/bind")
async def community_bind(
    action: str = Query(...),
    platform: str = Query(...),
):
    if platform not in PLATFORMS:
        return {"error": f"Unsupported platform: {platform}"}
    if action not in ("status", "start", "refresh", "delete"):
        return {"error": f"Unsupported action: {action}"}
    async with get_session() as db:
        user = await get_default_user(db)
        mgr = AsyncBindManager(db, user.id)
        if action == "status":
            return await mgr.status()
        if action == "start":
            task = mgr.start_bind()
            return {"task_id": task.task_id}
        if action == "refresh":
            return await mgr.refresh()
        if action == "delete":
            return await mgr.unbind()


@app.post("/api/community/sync")
async def community_sync(platform: str = Query(...)):
    if platform not in PLATFORMS:
        return {"error": f"Unsupported platform: {platform}"}
    async with get_session() as db:
        user = await get_default_user(db)
        row = await CommunityMetaRepo.get_binding(db, user.id, "douban")
        if row is None or not row.bound or not row.community_user_id:
            return {"error": "Not bound"}
        mgr = AsyncBindManager(db, user.id)
        task = mgr.start_sync(row.community_user_id)
        return {"task_id": task.task_id}


@app.websocket("/api/community/ws")
async def community_ws(ws: WebSocket, platform: str = Query(...)):
    await ws.accept()
    if platform not in PLATFORMS:
        await ws.send_json({"status": "failed", "error": f"Unsupported platform: {platform}"})
        await ws.close()
        return

    async with get_session() as db:
        user = await get_default_user(db)
        mgr = AsyncBindManager(db, user.id)

        try:
            while True:
                task = next((t for t in mgr._tasks.values() if t.status != "idle"), None)
                if task is None:
                    await ws.send_json({"status": "idle"})
                    await asyncio.sleep(1)
                    continue

                result: dict = {"status": task.status}
                if task.qr_base64:
                    result["qr_base64"] = task.qr_base64
                if task.status == "scraping":
                    result["scrape_phase"] = task.scrape_phase
                    result["scrape_counts"] = task.scrape_counts
                if task.status == "bound":
                    result["user_id"] = task.user_id
                    if task.profile:
                        result["profile"] = task.profile.model_dump()
                    result["scrape_counts"] = task.scrape_counts
                if task.status == "failed":
                    result["error"] = task.error
                await ws.send_json(result)

                if task.status in ("bound", "failed"):
                    await ws.close()
                    return

                await task.event.wait()
        except WebSocketDisconnect:
            pass


# ---- Community Data ----


@app.get("/api/community/data")
async def community_data(platform: str = Query(default="douban")):
    if platform not in PLATFORMS:
        return {"error": f"Unsupported platform: {platform}"}
    async with get_session() as db:
        user = await get_default_user(db)
        books = [row.to_api_dict() for row in await DataRepo.get_books(db, user.id)]
        movies = [row.to_api_dict() for row in await DataRepo.get_movies(db, user.id)]
        notes = [row.to_api_dict() for row in await DataRepo.get_notes(db, user.id)]
        return {"books": books, "movies": movies, "notes": notes}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
