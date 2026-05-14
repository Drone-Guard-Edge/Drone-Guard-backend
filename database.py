import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "droneGuard.db")


async def get_db() -> aiosqlite.Connection:
    """DB 커넥션 반환 — 호출 측에서 async with 로 사용"""
    return aiosqlite.connect(DB_PATH)


async def init_db() -> None:
    """앱 시작 시 테이블 초기화 (없으면 생성)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                frame_id    INTEGER,
                sensor      TEXT,
                confidence  REAL,
                bbox_x      INTEGER,
                bbox_y      INTEGER,
                bbox_w      INTEGER,
                bbox_h      INTEGER,
                risk_level  TEXT,
                raw_json    TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                saved_at         TEXT    NOT NULL,
                period_start     TEXT,
                period_end       TEXT,
                detection_count  INTEGER,
                max_risk         TEXT,
                avg_confidence   REAL,
                data_json        TEXT
            )
        """)

        # 조회 성능을 위한 인덱스
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_detections_timestamp
            ON detections (timestamp)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_detections_risk
            ON detections (risk_level)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_saved_at
            ON snapshots (saved_at)
        """)

        await db.commit()