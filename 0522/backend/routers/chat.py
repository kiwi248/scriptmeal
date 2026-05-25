from fastapi import APIRouter, HTTPException
from openai import OpenAI

from backend.config import OPENAI_API_KEY
from backend.models.schemas import ChatRequest, ChatResponse
from backend.agents.orchestrator import classify_intent
from backend.agents.specific_food_agent import SpecificFoodAgent
from backend.agents.weather_recipe_agent import WeatherRecipeAgent

router = APIRouter(prefix="/api", tags=["chat"])

_client = OpenAI(api_key=OPENAI_API_KEY)

OFF_TOPIC_REPLY = (
    "저는 다이어트 레시피 전문 챗봇입니다 🥗\n"
    "먹고 싶은 음식이나 원하는 식단 조건을 알려주시면 맞춤 레시피를 추천해드릴게요!\n\n"
    "예시:\n"
    "  • '떡볶이가 먹고 싶어'\n"
    "  • '포만감 오래가는 저칼로리 레시피 알려줘'\n"
    "  • '단백질 높은 아침 식사 추천해줘'"
)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    history = [{"role": m.role, "content": m.content} for m in req.history]

    try:
        intent = classify_intent(_client, req.message, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"의도 분류 실패: {e}")

    try:
        if intent == "SPECIFIC_FOOD":
            reply = SpecificFoodAgent(_client).run(req.message, history)
        elif intent == "GENERAL_RECIPE":
            reply = WeatherRecipeAgent(_client).run(req.message, history)
        else:
            reply = OFF_TOPIC_REPLY
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에이전트 실행 실패: {e}")

    return ChatResponse(reply=reply, intent=intent)
