"""
/api/chat  – 멀티에이전트 챗봇 엔드포인트
"""

import os
from fastapi import APIRouter, HTTPException
from openai import OpenAI

from backend.schemas import ChatRequest, ChatResponse
from backend.agents.orchestrator import classify_intent
from backend.agents.specific_food_agent import SpecificFoodAgent
from backend.agents.weather_recipe_agent import WeatherRecipeAgent

router = APIRouter(prefix="/api")

OFF_TOPIC_REPLY = (
    "저는 다이어트 레시피 전문 챗봇입니다 🥗\n"
    "먹고 싶은 음식이나 원하는 식단 조건을 알려주시면 맞춤 레시피를 추천해드릴게요!\n\n"
    "예시:\n"
    "  • 떡볶이가 먹고 싶어\n"
    "  • 포만감 오래가는 저칼로리 레시피 알려줘"
)


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    print(f"🟡 요청 수신 - 메시지: {request.message}")

    client = _get_client()
    print("🟡 OpenAI 클라이언트 생성 완료")

    history = [{"role": m.role, "content": m.content} for m in request.history]
    print(f"🟡 히스토리 변환 완료 - 대화 수: {len(history)}개")

    intent = classify_intent(client, request.message, history)
    print(f"🟢 의도 분류 완료 - intent: {intent}")

    if intent == "SPECIFIC_FOOD":
        print("🟢🍖 SpecificFoodAgent 실행 시작")
        reply = SpecificFoodAgent(client).run(request.message, history)
        print(f"🟢🍖 SpecificFoodAgent 실행 완료 - 응답: {reply[:30]}")
    elif intent == "GENERAL_RECIPE":
        print("🟢☀️ GENERAL_RECIPE면 WeatherRecipeAgent 실행 시작")
        reply = WeatherRecipeAgent(client).run(request.message, history)
        print(f"🟢☀️ WeatherRecipeAgent 실행 완료 - 응답: {reply[:30]}")
    else:
        print("🟢 OFF_TOPIC 응답 반환")
        reply = OFF_TOPIC_REPLY

    print(f"🔵 최종 응답 반환 완료-reply: {reply} intent: {intent}")
    return ChatResponse(reply=reply, intent=intent)
