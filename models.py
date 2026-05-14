from pydantic import BaseModel, Field
from typing import Literal


# ── DeepX → PC 수신 스키마 ──────────────────────────────────────

class BBox(BaseModel):
    x: int = Field(..., description="좌상단 x 픽셀 좌표")
    y: int = Field(..., description="좌상단 y 픽셀 좌표")
    w: int = Field(..., description="박스 너비 (픽셀)")
    h: int = Field(..., description="박스 높이 (픽셀)")


class Detection(BaseModel):
    id:         int
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox:       BBox
    sensor:     Literal["EO", "IR", "FUSION"]


class DeepXPayload(BaseModel):
    timestamp:  str                  # ISO 8601 e.g. "2026-05-14T10:23:01.123Z"
    frame_id:   int
    detections: list[Detection]


# ── 위험도 ──────────────────────────────────────────────────────

RiskLevel = Literal["HIGH", "MEDIUM", "LOW", "NONE"]


# ── PC → Browser 송신 스키마 ────────────────────────────────────

class DetectionEvent(BaseModel):
    """단건 탐지 이벤트 — Browser로 브로드캐스트"""
    timestamp:  str
    frame_id:   int
    sensor:     Literal["EO", "IR", "FUSION"]
    confidence: float
    bbox:       BBox
    risk_level: RiskLevel


class BroadcastMessage(BaseModel):
    """Browser WebSocket 송신 메시지"""
    type:       Literal["detection", "snapshot_saved", "no_detection"]
    payload:    DetectionEvent | dict | None = None


# ── DB 저장용 ────────────────────────────────────────────────────

class DetectionRow(BaseModel):
    """detections 테이블 단건 row"""
    timestamp:  str
    frame_id:   int
    sensor:     str
    confidence: float
    bbox_x:     int
    bbox_y:     int
    bbox_w:     int
    bbox_h:     int
    risk_level: RiskLevel
    raw_json:   str


class SnapshotRow(BaseModel):
    """snapshots 테이블 row"""
    saved_at:        str
    period_start:    str
    period_end:      str
    detection_count: int
    max_risk:        RiskLevel
    avg_confidence:  float
    data_json:       str