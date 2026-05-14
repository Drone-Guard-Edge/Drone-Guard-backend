import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# 연결된 Browser 클라이언트 목록
_clients: set[WebSocket] = set()


@router.websocket("/ws/browser")
async def browser_ws(ws: WebSocket) -> None:
    """Browser → PC 연결 엔드포인트"""
    await ws.accept()
    _clients.add(ws)
    print(f"[ws_broadcast] Browser 연결됨 (현재 {len(_clients)}개)")

    try:
        while True:
            # Browser에서 오는 메시지는 현재 무시 (ping 등)
            await ws.receive_text()
    except WebSocketDisconnect:
        _clients.discard(ws)
        print(f"[ws_broadcast] Browser 연결 종료 (현재 {len(_clients)}개)")


async def broadcast(message: dict[str, Any]) -> None:
    """연결된 모든 Browser 클라이언트에 메시지 전송"""
    global _clients
    if not _clients:
        return

    data = json.dumps(message, ensure_ascii=False)
    disconnected: set[WebSocket] = set()

    for client in _clients:
        try:
            await client.send_text(data)
        except Exception:
            disconnected.add(client)

    # 끊긴 클라이언트 정리
    _clients -= disconnected