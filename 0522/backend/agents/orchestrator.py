"""
Orchestrator Agent
사용자 발화를 SPECIFIC_FOOD / GENERAL_RECIPE / OFF_TOPIC 으로 분류합니다.
"""

import json
from openai import OpenAI

CLASSIFY_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "classify_intent",
            "description": "사용자 발화를 다이어트 레시피 챗봇 의도에 맞게 분류한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": ["SPECIFIC_FOOD", "GENERAL_RECIPE", "OFF_TOPIC"],
                        "description": (
                            "SPECIFIC_FOOD: 특정 음식명이나 음식 카테고리가 포함된 레시피 요청 "
                            "(예: 떡볶이, 짜장면, 파스타, 디저트, 안주, 한식, 양식, 중식)\n"
                            "GENERAL_RECIPE: 음식명 없이 조건/상황 기반 레시피 요청 "
                            "(예: 포만감, 저칼로리, 제철, 단백질 높은)\n"
                            "OFF_TOPIC: 다이어트/레시피와 무관한 질문"
                        ),
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "분류 이유를 한 문장으로 설명",
                    },
                },
                "required": ["intent", "reasoning"],
            },
        },
    }
]

SYSTEM_PROMPT = """당신은 다이어트 레시피 챗봇의 라우터입니다.
사용자의 발화를 분석해 classify_intent 함수를 반드시 호출하세요.

판단 기준:
- SPECIFIC_FOOD   : 특정 음식명(떡볶이, 짜장면, 파스타) 또는 음식 카테고리(디저트, 안주, 한식 등)가 명시된 경우
- GENERAL_RECIPE  : 음식명 없이 조건(칼로리, 영양, 시간, 기분 등)만 언급한 경우
- OFF_TOPIC       : 수학 계산, 역사, 날씨 일반상식 등 레시피와 무관한 경우
"""


def classify_intent(client: OpenAI, user_input: str, chat_history: list[dict]) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *chat_history[-6:],
        {"role": "user", "content": user_input},
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        tools=CLASSIFY_TOOL,
        tool_choice={"type": "function", "function": {"name": "classify_intent"}},
        messages=messages,
        temperature=0,
    )

    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    return args.get("intent", "OFF_TOPIC")
