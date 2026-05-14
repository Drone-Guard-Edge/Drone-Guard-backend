import asyncio
import json
import os
from datetime import datetime, timezone

import aiosqlite

from database import DB_PATH
from models import DetectionEvent, RiskLevel, SnapshotRow
from services.risk import get_max_risk, calc_avg_confidence

SAVE_INTERVAL = int(os.getenv("SAVE_INTERVAL", 30))
LOG_DIR = os.getenv("LOG_DIR", "logs")

# 30초 단위 버퍼
_buffer: list[DetectionEvent] = []


def add_to_buffer(event: DetectionEvent) -> None:
    _buffer.append(event)


async def save_detection_row(event: DetectionEvent) -> None:
    """탐지 즉시 detections 테이블에 단건 저장"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO detections
                (timestamp, frame_id, sensor, confidence,
                 bbox_x, bbox_y, bbox_w, bbox_h, risk_level, raw_json)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                event.timestamp,
                event.frame_id,
                event.sensor,
                event.confidence,
                event.bbox.x,
                event.bbox.y,
                event.bbox.w,
                event.bbox.h,
                event.risk_level,
                event.model_dump_json(),
            ),
        )
        await db.commit()


async def flush_buffer() -> None:
    """버퍼를 snapshots 테이블 + JSON 파일로 저장 후 초기화"""
    if not _buffer:
        return

    now = datetime.now(timezone.utc).isoformat()
    period_start = _buffer[0].timestamp
    period_end   = _buffer[-1].timestamp
    confidences  = [e.confidence for e in _buffer]

    # max_risk: RiskLevel 비교를 위해 Detection-like 객체 대신 직접 계산
    risk_priority: list[RiskLevel] = ["HIGH", "MEDIUM", "LOW", "NONE"]
    levels = [e.risk_level for e in _buffer]
    max_risk: RiskLevel = "NONE"
    for lvl in risk_priority:
        if lvl in levels:
            max_risk = lvl
            break

    data_list = [e.model_dump() for e in _buffer]

    row = SnapshotRow(
        saved_at        = now,
        period_start    = period_start,
        period_end      = period_end,
        detection_count = len(_buffer),
        max_risk        = max_risk,
        avg_confidence  = calc_avg_confidence(confidences),
        data_json       = json.dumps(data_list, ensure_ascii=False),
    )

    # DB 저장
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO snapshots
                (saved_at, period_start, period_end,
                 detection_count, max_risk, avg_confidence, data_json)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                row.saved_at,
                row.period_start,
                row.period_end,
                row.detection_count,
                row.max_risk,
                row.avg_confidence,
                row.data_json,
            ),
        )
        await db.commit()

    # JSON 파일 백업
    os.makedirs(LOG_DIR, exist_ok=True)
    fname = os.path.join(
        LOG_DIR,
        f"snapshot_{now[:19].replace(':', '-')}.json",
    )
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(
            {
                "saved_at":        row.saved_at,
                "period_start":    row.period_start,
                "period_end":      row.period_end,
                "detection_count": row.detection_count,
                "max_risk":        row.max_risk,
                "avg_confidence":  row.avg_confidence,
                "data":            data_list,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"[logger] snapshot saved — {row.detection_count}건 / max:{max_risk} / {fname}")
    _buffer.clear()


async def auto_snapshot_loop() -> None:
    """FastAPI lifespan에서 background task로 실행"""
    while True:
        await asyncio.sleep(SAVE_INTERVAL)
        await flush_buffer()