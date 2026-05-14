import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_db
from services.logger import auto_snapshot_loop
from router.ws_receiver import router as receiver_router
from router.ws_broadcast import router as broadcast_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 시작 ──
    await init_db()
    print("[main] DB 초기화 완료")

    snapshot_task = asyncio.create_task(auto_snapshot_loop())
    print("[main] 자동 스냅샷 루프 시작 (30초 주기)")

    yield

    # ── 종료 ──
    snapshot_task.cancel()
    try:
        await snapshot_task
    except asyncio.CancelledError:
        pass
    print("[main] 서버 종료")


app = FastAPI(
    title="DroneGuard Edge — PC Server",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receiver_router)
app.include_router(broadcast_router)

@app.get("/")
async def index():
    return FileResponse("dashboard.html")

@app.get("/health")
async def health():
    return {"status": "ok"}