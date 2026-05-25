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
    "  • 포만감 오래가는 저칼로리 레시피 알려줘\n"
    "  • 단백질 높은 아침 식사 추천해줘"
)


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    client = _get_client()
    history = [{"role": m.role, "content": m.content} for m in request.history]

    intent = classify_intent(client, request.message, history)

    if intent == "SPECIFIC_FOOD":
        reply = SpecificFoodAgent(client).run(request.message, history)
    elif intent == "GENERAL_RECIPE":
        reply = WeatherRecipeAgent(client).run(request.message, history)
    else:
        reply = OFF_TOPIC_REPLY

    return ChatResponse(reply=reply, intent=intent)
