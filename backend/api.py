import asyncio

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from api.bind import get_manager, supported_platforms

app = FastAPI()

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


@app.get("/api/bind")
async def bind_check(platform: str = Query(...)):
    if platform not in PLATFORMS:
        return {"error": f"Unsupported platform: {platform}"}
    mgr = get_manager(platform)
    if not mgr.is_bound:
        return {"bound": False}
    meta = mgr.load_meta()
    if not meta or not meta.get("bound"):
        return {"bound": False}
    return meta


@app.post("/api/bind/start")
async def bind_start(platform: str = Query(...)):
    if platform not in PLATFORMS:
        return {"error": f"Unsupported platform: {platform}"}
    mgr = get_manager(platform)
    task = mgr.start_bind()
    return {"task_id": task.task_id}


@app.get("/api/bind/status")
async def bind_status(platform: str = Query(...)):
    if platform not in PLATFORMS:
        return {"error": f"Unsupported platform: {platform}"}
    mgr = get_manager(platform)
    for task in mgr._tasks.values():
        if task.status in ("pending", "bound", "failed"):
            result: dict = {"status": task.status}
            if task.qr_base64:
                result["qr_base64"] = task.qr_base64
            if task.status == "bound":
                result["user_id"] = task.user_id
                if task.profile:
                    result["profile"] = task.profile.model_dump()
            if task.status == "failed":
                result["error"] = task.error
            return result
    meta = mgr.load_meta()
    if meta and meta.get("bound"):
        return {"status": "bound", **meta}
    return {"status": "idle"}


@app.post("/api/bind/refresh")
async def bind_refresh(platform: str = Query(...)):
    if platform not in PLATFORMS:
        return {"error": f"Unsupported platform: {platform}"}
    mgr = get_manager(platform)
    if not mgr.is_bound:
        return {"error": "Not bound"}
    meta = mgr.load_meta()
    if not meta or not meta.get("user_id"):
        return {"error": "No user_id in meta"}
    try:
        http = mgr._session.build_http_session()
        from community.douban.scrapers.profile import ProfileScraper

        profile = ProfileScraper(http, meta["user_id"]).scrape()
        http.close()
    except Exception as e:
        return {"error": str(e)}
    mgr.save_meta(meta["user_id"], profile)
    return {"bound": True, "platform": platform, "user_id": meta["user_id"], "profile": profile.model_dump()}


@app.delete("/api/bind")
async def bind_unbind(platform: str = Query(...)):
    if platform not in PLATFORMS:
        return {"error": f"Unsupported platform: {platform}"}
    mgr = get_manager(platform)
    mgr.delete_meta()
    return {"bound": False}


@app.websocket("/api/bind/ws")
async def bind_ws(ws: WebSocket, platform: str = Query(...)):
    await ws.accept()
    if platform not in PLATFORMS:
        await ws.send_json({"status": "failed", "error": f"Unsupported platform: {platform}"})
        await ws.close()
        return

    mgr = get_manager(platform)
    try:
        while True:
            # Find active task
            task = next((t for t in mgr._tasks.values() if t.status != "idle"), None)
            if task is None:
                await ws.send_json({"status": "idle"})
                await asyncio.sleep(1)
                continue

            # Send current state
            result: dict = {"status": task.status}
            if task.qr_base64:
                result["qr_base64"] = task.qr_base64
            if task.status == "bound":
                result["user_id"] = task.user_id
                if task.profile:
                    result["profile"] = task.profile.model_dump()
            if task.status == "failed":
                result["error"] = task.error
            await ws.send_json(result)

            if task.status in ("bound", "failed"):
                await ws.close()
                return

            # Wait for next status change
            await task.event.wait()
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
