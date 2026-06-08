"""
/api/chat  – 단일 에이전트 챗봇 엔드포인트
"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI

from backend.schemas import ChatRequest, ChatResponse
from backend.agents.diet_agent import DietAgent

router = APIRouter(prefix="/api")

# ── 싱글턴 클라이언트 ─────────────────────────────────────────────────────────
# main.py lifespan에서 init_client()로 한 번만 초기화됨
_client: OpenAI | None = None


def init_client(client: OpenAI) -> None:
    """앱 시작 시 main.py lifespan에서 호출."""
    global _client
    _client = client


def get_client() -> OpenAI:
    if _client is None:
        raise HTTPException(status_code=500, detail="서버가 아직 초기화되지 않았습니다.")
    return _client


OFF_TOPIC_REPLY = (
    "저는 다이어트 레시피 전문 챗봇입니다 🥗\n"
    "먹고 싶은 음식이나 원하는 식단 조건을 알려주시면 맞춤 레시피를 추천해드릴게요!\n\n"
    "예시:\n"
    "  • 떡볶이가 먹고 싶어\n"
    "  • 포만감 오래가는 저칼로리 레시피 알려줘"
)


# ── 스트리밍 엔드포인트 (실제 서비스용) ──────────────────────────────────────
@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    print(f"🟡 [STREAM] 요청 수신 - 메시지: {request.message}")

    history = [{"role": m.role, "content": m.content} for m in request.history]
    agent   = DietAgent(get_client())

    return StreamingResponse(
        agent.run_stream(request.message, history),
        media_type="text/event-stream",
    )


# ── 스웨거 테스트용 (비스트리밍) ─────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Swagger 테스트용. 프론트엔드는 /chat/stream 사용."""
    print(f"🟡 요청 수신 - 메시지: {request.message}")

    history      = [{"role": m.role, "content": m.content} for m in request.history]
    agent        = DietAgent(get_client())
    reply        = ""
    purchase_info = ""
    intent_guess  = "GENERAL_RECIPE"

    for raw in agent.run_stream(request.message, history):
        if not raw.startswith("data: "):
            continue
        payload = json.loads(raw[6:])

        if payload["type"] == "tool_start":
            tool = payload["tool"]
            if tool in ("get_diet_products", "search_recipe"):
                intent_guess = "SPECIFIC_FOOD"
            elif tool == "get_weather_recipe":
                intent_guess = "GENERAL_RECIPE"

        elif payload["type"] == "chunk":
            reply += payload["value"]

        elif payload["type"] == "done":
            purchase_info = payload["value"]

    full_reply = (reply + purchase_info).strip()
    if not full_reply:
        full_reply = OFF_TOPIC_REPLY

    print(f"🔵 최종 응답 완료 - intent: {intent_guess}, 길이: {len(full_reply)}자")
    return ChatResponse(reply=full_reply, intent=intent_guess)
