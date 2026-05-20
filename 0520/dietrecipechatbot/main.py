"""
다이어트 레시피 멀티 에이전트 (계층형 패턴)
────────────────────────────────────────────
Orchestrator (gpt-4o-mini) → 사용자 의도 분류
  ├─ SPECIFIC_FOOD   → SpecificFoodAgent   (제품 DB + Tavily 검색)
  ├─ GENERAL_RECIPE  → WeatherRecipeAgent  (날씨/날짜/제철 기반)
  └─ OFF_TOPIC       → 다이어트 관련 질문 유도
"""

import os
import json
from openai import OpenAI
from agents.orchestrator import classify_intent
from agents.specific_food_agent import SpecificFoodAgent
from agents.weather_recipe_agent import WeatherRecipeAgent

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))


def run_chatbot():
    print("=" * 55)
    print("🥗 다이어트 레시피 AI 에이전트 (exit 종료)")
    print("=" * 55)
    print()

    chat_history: list[dict] = []

    while True:
        user_input = input("나: ").strip()
        if not user_input or user_input.lower() == "exit":
            print("챗봇을 종료합니다.")
            break

        # ── 1단계: Orchestrator → 의도 분류 ─────────────────────
        intent = classify_intent(client, user_input, chat_history)
        print(f"[Orchestrator] 분류 결과: {intent}\n")

        # ── 2단계: 의도별 Sub-Agent 라우팅 ──────────────────────
        if intent == "SPECIFIC_FOOD":
            agent = SpecificFoodAgent(client)
            reply = agent.run(user_input, chat_history)

        elif intent == "GENERAL_RECIPE":
            agent = WeatherRecipeAgent(client)
            reply = agent.run(user_input, chat_history)

        else:  # OFF_TOPIC
            reply = (
                "저는 다이어트 레시피 전문 챗봇입니다 🥗\n"
                "먹고 싶은 음식이나 원하는 식단 조건을 알려주시면 "
                "맞춤 레시피를 추천해드릴게요!\n\n"
                "예시:\n"
                "  • '떡볶이가 먹고 싶어'\n"
                "  • '포만감 오래가는 저칼로리 레시피 알려줘'\n"
                "  • '단백질 높은 아침 식사 추천해줘'"
            )

        print(f"\n봇: {reply}\n")
        print("-" * 55)

        # 대화 히스토리 누적
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    run_chatbot()
