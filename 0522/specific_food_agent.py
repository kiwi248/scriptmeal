"""
SpecificFoodAgent
─────────────────
특정 음식명이 포함된 요청을 처리합니다.

흐름:
  1. 유저 쿼리 임베딩
  2. pgvector로 관련 시판 제품 Top 5 조회
  3. LLM 첫 번째 호출 (레시피 생성 + search_recipe tool 판단)
  4. tool 호출 시 Tavily로 최신 레시피 검색 후 LLM 재호출
  5. JSON 파싱 (실패 시 에러 메시지 반환)
  6. 실제 사용된 제품 구매 정보 조회
  7. 최종 응답 포맷 구성
"""

import json
import openai
from openai import OpenAI
from tavily import TavilyClient
from db.product_db import ProductDB   # 아래 db/product_db.py 참조

TAVILY_API_KEY = __import__("os").environ.get("TAVILY_API_KEY", "")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

SEARCH_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "search_recipe",
            "description": "모르는 음식이나 최신 유행 음식 레시피를 검색할 때 사용",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 레시피 키워드"}
                },
                "required": ["query"],
            },
        },
    }
]

JSON_SCHEMA = """
반드시 아래 JSON 형식으로만 응답하세요 (코드블록 없이 순수 JSON):
{
    "recipe_text": "레시피 제목\\n\\n재료: ...\\n\\n조리법:\\n1. ...\\n2. ...\\n\\n칼로리: ...kcal",
    "used_product_ids": [1, 3]
}
"""


class SpecificFoodAgent:
    def __init__(self, client: OpenAI):
        self.client = client
        self.db = ProductDB()

    # ── public entry point ────────────────────────────────────────────────────

    def run(self, user_query: str, chat_history: list[dict]) -> str:
        # 1단계: 쿼리 임베딩
        query_embedding = self._embed(user_query)

        # 2단계: 관련 시판 제품 Top 5
        products = self.db.get_similar_products(query_embedding, top_k=5)
        products_text = self._format_products(products)

        # 3단계: LLM 첫 번째 호출
        system_prompt = f"""당신은 다이어트 레시피 챗봇입니다.
아래 시판 제품 후보 중 적합한 1~2개를 골라 사용하세요.
나머지 재료는 일반 신선재료로 채우세요.
모르는 음식이거나 최신 유행 음식이면 반드시 search_recipe tool을 먼저 호출하세요.
{JSON_SCHEMA}

[사용 가능한 시판 제품]
{products_text}"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            tools=SEARCH_TOOL,
            messages=[
                {"role": "system", "content": system_prompt},
                *chat_history[-6:],
                {"role": "user", "content": user_query},
            ],
        )

        # 4단계: tool 호출 분기
        if response.choices[0].message.tool_calls:
            response = self._handle_tool_call(
                response, user_query, chat_history, products_text
            )

        # 5단계: JSON 파싱
        try:
            raw = response.choices[0].message.content or ""
            # 혹시 ```json 펜스가 붙어있을 경우 제거
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            recipe = json.loads(raw)
        except json.JSONDecodeError:
            return "레시피 생성 중 오류가 발생했습니다. 다시 시도해주세요."

        # 6단계: 사용된 제품 구매 정보 조회
        used_ids = recipe.get("used_product_ids", [])
        product_details = self.db.get_products_by_ids(used_ids)

        # 7단계: 최종 응답 포맷
        return self._build_response(recipe["recipe_text"], product_details)

    # ── private helpers ───────────────────────────────────────────────────────

    def _embed(self, text: str) -> list[float]:
        return (
            openai.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            .data[0]
            .embedding
        )

    def _format_products(self, products: list[dict]) -> str:
        if not products:
            return "현재 등록된 시판 제품이 없습니다."
        return "\n".join(
            f"[id={p['id']}] {p['brand']} {p['product_name']} ({p['calories']}kcal)"
            for p in products
        )

    def _handle_tool_call(self, first_response, user_query, chat_history, products_text):
        """Tavily 검색 후 LLM 재호출"""
        tool_call = first_response.choices[0].message.tool_calls[0]
        search_query = json.loads(tool_call.function.arguments)["query"]

        print(f"[SpecificFoodAgent] Tavily 검색: {search_query}")
        search_result = tavily_client.search(search_query)

        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""당신은 다이어트 레시피 챗봇입니다.
아래 검색된 레시피를 참고해서 시판 제품을 활용한 다이어트 버전으로 재구성하세요.
{JSON_SCHEMA}

[검색된 레시피 참고]
{search_result}

[사용 가능한 시판 제품]
{products_text}""",
                },
                *chat_history[-6:],
                {"role": "user", "content": user_query},
            ],
        )

    def _build_response(self, recipe_text: str, product_details: list[dict]) -> str:
        if not product_details:
            return recipe_text.strip()

        product_lines = "\n".join(
            f"{p['brand']} {p['product_name']} {p['calories']}kcal "
            f"| 약 {p['price_range']} | {', '.join(p['retailers'])}"
            for p in product_details
        )
        return f"{recipe_text.strip()}\n\n---\n🛒 사용된 제품 구매 정보\n{product_lines}"
