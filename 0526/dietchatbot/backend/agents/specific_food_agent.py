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

import os
import json
from openai import OpenAI
from tavily import TavilyClient
from backend.db.product_db import get_db

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
    "recipe_text": "## 레시피 제목\\n\\n### 재료\\n- 재료1 (칼로리)\\n- 재료2 (칼로리)\\n\\n### 조리법\\n1. 상세한 1단계\\n2. 상세한 2단계\\n3. 상세한 3단계\\n\\n### 칼로리\\n- 전체 칼로리: 재료1 칼로리 + 재료2 칼로리 = 총 Nkcal",
    "used_product_ids": [1, 3]
}

recipe_text 작성 규칙:
- 재료는 각각 칼로리 표기 필수 (예: 오뚜기 컵누들 1개 (170kcal))
- 조리법은 최소 5단계 이상, 각 단계를 구체적으로 작성
- 칼로리는 재료별 합산 과정을 보여줄 것
"""


class SpecificFoodAgent:
    def __init__(self, client: OpenAI):
        self.client = client
        self.db = get_db()
        self.tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))

    def run(self, user_query: str, chat_history: list[dict]) -> str:
        print(f"🍖🟥 [SpecificFood] 시작 - 쿼리: {user_query}")
        # 1단계: 쿼리 임베딩
        query_embedding = self._embed(user_query)

        # 2단계: 관련 시판 제품 Top 5
        products = self.db.get_similar_products(query_embedding, top_k=5)
        products_text = self._format_products(products)
        print(f"🍖🟥 [SpecificFood] 검색된 제품: {products_text}")

        # 3단계: LLM 첫 번째 호출
        system_prompt = f"""당신은 다이어트 레시피 챗봇입니다.
        아래 시판 제품 후보 중 레시피와 실제로 어울리는 제품만 선택적으로 사용하세요.
        어울리는 제품이 없으면 used_product_ids를 빈 배열로 반환하세요. 
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
            print(f"🍖🟧 [SpecificFood] Tavily 검색 실행")
            response = self._handle_tool_call(
                response, user_query, chat_history, products_text
            )
        else:
            print(f"🍖🟨 [SpecificFood] Tavily 검색 없이 진행")
            print(f"🍖🟨 [SpecificFood] LLM 원본 응답: {response.choices[0].message.content[:200]}")
        
        # 5단계: JSON 파싱
        try:
            raw = response.choices[0].message.content or ""
            print(f"🍖🟩 [SpecificFood] JSON 파싱 시작 - raw: {raw[:200]}")  # 파싱 전 원본
            raw = (
                raw.strip()
                .removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )
            recipe = json.loads(raw)

            # 어떤 제품 ID가 선택됐는지 확인
            print(f"🍖🟩 [SpecificFood] JSON 파싱 성공 - used_product_ids: {recipe.get('used_product_ids')}")       
        except json.JSONDecodeError:
            print(f"🍖🟩 [SpecificFood] JSON 파싱 실패 - 에러: {e}, raw: {raw[:200]}")
            return "레시피 생성 중 오류가 발생했습니다. 다시 시도해주세요."

        # 6단계: 사용된 제품 구매 정보 조회
        used_ids = recipe.get("used_product_ids", [])
        print(f"🍖🟦 [SpecificFood] 사용된 제품 ID: {used_ids}")
        product_details = self.db.get_products_by_ids(used_ids)
        # ID로 조회한 제품명 확인
        print(f"🍖🟦 [SpecificFood] 조회된 제품 상세: {[p['product_name'] for p in product_details]}")


        # 7단계: 최종 응답 포맷
        return self._build_response(recipe["recipe_text"], product_details)
        print(f"🍖🟪 [SpecificFood] 최종 응답 완료 - 길이: {len(result)}자")
        return result

    def _embed(self, text: str) -> list[float]:
        return (
            self.client.embeddings.create(
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
        search_result = self.tavily.search(search_query)

        # 검색 결과에서 텍스트만 추출
        search_text = "\n".join(
            r.get("content", "") for r in search_result.get("results", [])
        )
        print(f"🍖 ✅ [SpecificFood] Tavily 검색 결과: {search_text[:200]}")  # 확인용
        
        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""당신은 다이어트 레시피 챗봇입니다.
아래 검색된 레시피를 참고해서 시판 제품을 활용한 다이어트 버전으로 재구성하세요.
어울리는 제품이 없거나 억지로 끼워맞추게 되면 used_product_ids를 빈 배열로 반환하고 일반 신선재료를 사용하세요.
{JSON_SCHEMA}

[검색된 레시피 참고]
{search_text}

[사용 가능한 시판 제품(어울릴 때만 사용)]
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

