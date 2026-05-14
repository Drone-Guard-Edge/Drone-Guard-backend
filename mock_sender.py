"""
mock_sender.py — DeepX 역할 대역 테스트 송신기
실행: python3 mock_sender.py
"""
import asyncio
import json
import random
from datetime import datetime, timezone

import websockets

WS_URL = "ws://localhost:8000/ws/deepx"
SEND_INTERVAL = 2.0  # 초


def make_payload(frame_id: int) -> dict:
    """랜덤 탐지 페이로드 생성"""
    sensors = ["EO", "IR", "FUSION"]
    confidence = round(random.uniform(0.20, 0.98), 3)

    # 20% 확률로 탐지 없음
    detections = []
    if random.random() > 0.2:
        detections = [
            {
                "id": 1,
                "confidence": confidence,
                "bbox": {
                    "x": random.randint(50, 400),
                    "y": random.randint(30, 300),
                    "w": random.randint(40, 120),
                    "h": random.randint(30, 90),
                },
                "sensor": random.choice(sensors),
            }
        ]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "frame_id":  frame_id,
        "detections": detections,
    }


async def run():
    print(f"[mock] {WS_URL} 연결 시도...")

    async with websockets.connect(WS_URL) as ws:
        print("[mock] 연결됨. 송신 시작")
        frame_id = 1

        while True:
            payload = make_payload(frame_id)
            await ws.send(json.dumps(payload, ensure_ascii=False))

            det_count = len(payload["detections"])
            if det_count:
                conf = payload["detections"][0]["confidence"]
                sensor = payload["detections"][0]["sensor"]
                print(f"[mock] frame #{frame_id} | {sensor} | conf {conf:.3f} | det {det_count}건")
            else:
                print(f"[mock] frame #{frame_id} | 탐지 없음")

            frame_id += 1
            await asyncio.sleep(SEND_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run())