import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from models import DeepXPayload, DetectionEvent
from services.risk import get_risk_level
from services.logger import add_to_buffer, save_detection_row
from router.ws_broadcast import broadcast

router = APIRouter()


@router.websocket("/ws/deepx")
async def deepx_receiver(ws: WebSocket) -> None:
    """DeepX → PC 수신 엔드포인트"""
    await ws.accept()
    print("[ws_receiver] DeepX 연결됨")

    try:
        while True:
            raw = await ws.receive_text()

            try:
                payload = DeepXPayload.model_validate_json(raw)
            except Exception as e:
                print(f"[ws_receiver] 페이로드 파싱 오류: {e}")
                await ws.send_text(json.dumps({"error": str(e)}))
                continue

            if not payload.detections:
                # 탐지 없음 — Browser에 no_detection 브로드캐스트
                await broadcast({"type": "no_detection", "payload": None})
                continue

            for det in payload.detections:
                risk = get_risk_level(det.confidence)

                event = DetectionEvent(
                    timestamp  = payload.timestamp,
                    frame_id   = payload.frame_id,
                    sensor     = det.sensor,
                    confidence = det.confidence,
                    bbox       = det.bbox,
                    risk_level = risk,
                )

                # 즉시 DB 단건 저장
                await save_detection_row(event)

                # 30초 버퍼에 추가
                add_to_buffer(event)

                # Browser로 브로드캐스트
                await broadcast({
                    "type": "detection",
                    "payload": event.model_dump(),
                })

    except WebSocketDisconnect:
        print("[ws_receiver] DeepX 연결 종료")