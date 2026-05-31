"""
DietAgent (단일 에이전트)
─────────────────────────
기존 Orchestrator + SpecificFoodAgent + WeatherRecipeAgent를 하나로 통합.

흐름:
  1. LLM이 유저 의도를 추론
  2. 필요한 툴을 선택해 호출 (복수 호출 가능)
     - tool1: get_diet_products  – DB에서 시판 제품 조회 (특정 음식 언급 시)
     - tool2: search_recipe      – Tavily로 레시피 웹 검색 (생소한 음식 시)
     - tool3: get_weather_recipe – 기상청 날씨 + 날짜/시간으로 메뉴 추천
  3. 모든 툴 결과를 모은 뒤 최종 응답을 스트리밍으로 생성
  4. 후속 질문(재료/칼로리/대체재료 등)은 툴 없이 바로 스트리밍 답변
"""

import os
import json
import math
import requests
from datetime import datetime, timedelta
from typing import Generator

from openai import OpenAI
from tavily import TavilyClient
from backend.db.product_db import get_db

# ── 기상청 설정 ────────────────────────────────────────────────────────────────
KMA_API_KEY  = os.environ.get("KMA_API_KEY", "")
DEFAULT_LAT  = 37.5665   # 서울 위도
DEFAULT_LON  = 126.9780  # 서울 경도

# ── 시스템 프롬프트 ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """당신은 다이어트 레시피 전문 챗봇입니다.

[툴 사용 기준]
- 특정 음식명·카테고리(떡볶이, 파스타, 디저트, 한식 등) 언급
  → get_diet_products 반드시 먼저 호출
  → 생소하거나 최신 유행 음식이면 search_recipe 추가 호출
- 음식명 없이 메뉴 추천 요청 (포만감, 저칼로리, 제철, 날씨 맞춤 등)
  → get_weather_recipe 호출
- 레시피 재료·칼로리·대체재료·조리 방법 후속 질문
  → 툴 없이 바로 답변 (짧고 명확하게)
- 다이어트·레시피와 무관한 질문
  → 툴 없이 다이어트 레시피 챗봇임을 안내

[레시피 응답 형식]
## 레시피 제목

### 재료
- 재료명 분량 (칼로리)

### 조리법
1. 구체적인 단계 (최소 5단계)

### 칼로리
- 재료1 칼로리 + 재료2 칼로리 = 총 Nkcal

[시판 제품 안내]
get_diet_products 결과에 레시피와 어울리는 제품이 있으면 재료에 포함하고
응답 마지막에 구매 정보를 추가하세요. 억지로 끼워맞추지 마세요.
"""

# ── 툴 정의 ───────────────────────────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_diet_products",
            "description": (
                "특정 음식 레시피에 활용할 수 있는 다이어트 시판 제품을 DB에서 검색한다. "
                "특정 음식명이나 카테고리가 언급될 때 레시피 생성 전 반드시 호출."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 음식명 또는 재료명. 예: '떡볶이', '파스타'"
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_recipe",
            "description": (
                "모르는 음식의 레시피를 웹에서 검색한다. "
                "get_diet_products 호출 후, 생소하거나 최신 음식이면 추가로 호출."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "레시피 검색 쿼리. 예: '두바이 초콜릿 레시피 만드는법 재료'"
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_recipe",
            "description": (
                "특정 음식명 없이 메뉴 추천을 요청할 때 호출. "
                "기상청 실시간 날씨와 현재 날짜·시간을 조회해 제철 재료 기반 레시피 컨텍스트를 반환."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


class DietAgent:
    def __init__(
        self,
        client: OpenAI,
        lat: float = DEFAULT_LAT,
        lon: float = DEFAULT_LON,
    ):
        self.client = client
        self.lat    = lat
        self.lon    = lon
        self.db     = get_db()
        self.tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))

    # ── 공개 인터페이스 ────────────────────────────────────────────────────────

    def run_stream(
        self,
        user_query: str,
        chat_history: list[dict],
    ) -> Generator[str, None, None]:
        """
        단일 에이전트 실행 (스트리밍).

        yield 형식:
          {"type": "tool_start", "tool": "<툴명>"}          – 툴 실행 시작 알림
          {"type": "chunk",      "value": "<텍스트 조각>"}  – 최종 응답 스트리밍
          {"type": "done",       "value": "<구매정보>"}      – 스트리밍 종료 + 구매정보
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *chat_history[-6:],
            {"role": "user",   "content": user_query},
        ]

        product_details: list[dict] = []   # 실제 사용된 시판 제품 (구매 정보용)

        # ── Agentic Loop: LLM이 툴을 다 쓸 때까지 반복 ──────────────────────
        while True:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                tools=TOOLS,
                tool_choice="auto",
                messages=messages,
            )

            msg = response.choices[0].message

            # 툴 호출 없음 → 루프 종료, 스트리밍으로 최종 응답 생성
            if not msg.tool_calls:
                break

            # 툴 호출 있음 → 실행 후 결과를 messages에 추가
            messages.append(msg)

            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"🔧 [DietAgent] 툴 호출: {tool_name} | args: {tool_args}")
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name})}\n\n"

                # 툴 실행
                if tool_name == "get_diet_products":
                    result, details = self._get_diet_products(tool_args["query"])
                    product_details.extend(details)          # 구매 정보 누적

                elif tool_name == "search_recipe":
                    result = self._search_recipe(tool_args["query"])

                elif tool_name == "get_weather_recipe":
                    result = self._get_weather_recipe()

                else:
                    result = f"알 수 없는 툴: {tool_name}"

                print(f"🔧 [DietAgent] 툴 결과 ({tool_name}): {str(result)[:200]}")

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "content":      result,
                })

        # ── 최종 응답: 스트리밍 ───────────────────────────────────────────────
        stream = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"data: {json.dumps({'type': 'chunk', 'value': delta})}\n\n"

        # 구매 정보가 있으면 done과 함께 전송
        purchase_info = self._build_purchase_info(product_details)
        yield f"data: {json.dumps({'type': 'done', 'value': purchase_info})}\n\n"

    # ── 툴 구현 ───────────────────────────────────────────────────────────────

    def _get_diet_products(self, query: str) -> tuple[str, list[dict]]:
        """tool1: DB에서 관련 시판 제품 Top 5 조회"""
        print(f"🛒 [DietAgent] DB 제품 검색: {query}")

        embedding = self._embed(query)
        products  = self.db.get_similar_products(embedding, top_k=5)

        if not products:
            return "현재 등록된 관련 시판 제품이 없습니다.", []

        lines = [
            f"[id={p['id']}] {p['brand']} {p['product_name']} ({p['calories']}kcal)"
            for p in products
        ]
        result_text = "사용 가능한 시판 제품 후보:\n" + "\n".join(lines)
        print(f"🛒 [DietAgent] DB 검색 결과: {result_text}")
        return result_text, products

    def _search_recipe(self, query: str) -> str:
        """tool2: Tavily로 레시피 웹 검색"""
        print(f"🔍 [DietAgent] Tavily 검색: {query}")

        search_result = self.tavily.search(
            query,
            search_depth="advanced",
            max_results=3,
            include_raw_content=True,
        )
        results = search_result.get("results", [])

        if not results:
            return "레시피 검색 결과가 없습니다."

        # 최대 3개 결과, 각 5000자
        search_text = "\n\n---\n\n".join(
            (r.get("raw_content") or r.get("content", ""))[:5000]
            for r in results[:3]
        )
        for r in results:
            print(f"🔍 [DietAgent] Tavily URL: {r.get('url', '')}")

        return f"검색된 레시피 참고 자료:\n{search_text}"

    def _get_weather_recipe(self) -> str:
        """tool3: 기상청 날씨 + 현재 날짜/시간 컨텍스트 반환"""
        temp, weather = self._fetch_weather()
        now  = datetime.now()
        hour = now.hour

        if   5  <= hour < 10: meal_time = "아침 식사"
        elif 10 <= hour < 14: meal_time = "점심 식사"
        elif 14 <= hour < 17: meal_time = "간식"
        elif 17 <= hour < 21: meal_time = "저녁 식사"
        else:                  meal_time = "야식 (소식)"

        context = (
            f"현재 날짜/시간: {now.strftime('%Y년 %m월 %d일 %H:%M')}\n"
            f"현재 날씨: {weather}, 기온: {temp}°C\n"
            f"현재 시간대: {meal_time}\n"
            f"참고: {now.month}월 대한민국 제철 재료를 활용하고, "
            f"날씨/기온에 맞는 {meal_time} 메뉴를 추천하세요. "
            f"(비/눈이면 따뜻한 국물, 30°C 이상이면 시원한 음식)"
        )
        print(f"☀️ [DietAgent] 날씨 컨텍스트: {context}")
        return context

    # ── 유틸 ─────────────────────────────────────────────────────────────────

    def _embed(self, text: str) -> list[float]:
        return (
            self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            .data[0]
            .embedding
        )

    def _build_purchase_info(self, product_details: list[dict]) -> str:
        """사용된 시판 제품 구매 정보 문자열 생성"""
        if not product_details:
            return ""
        lines = [
            f"{p['product_name']} {p['calories']}kcal "
            f"| 약 {p['price_range']} | {', '.join(p['retailers'])}"
            for p in product_details
        ]
        return "\n\n---\n🛒 사용된 제품 구매 정보\n" + "\n".join(lines)

    # ── 기상청 API ────────────────────────────────────────────────────────────

    @staticmethod
    def _latlon_to_grid(lat: float, lon: float) -> tuple[int, int]:
        """위경도 → 기상청 격자(nx, ny) 변환 (Lambert Conformal Conic)"""
        RE, GRID = 6371.00877, 5.0
        SLAT1, SLAT2 = 30.0, 60.0
        OLON, OLAT   = 126.0, 38.0
        XO,   YO     = 43, 136
        D  = math.pi / 180.0
        re = RE / GRID
        sn = math.log(
            math.cos(SLAT1 * D) / math.cos(SLAT2 * D)
        ) / math.log(
            math.tan(math.pi * 0.25 + SLAT2 * D * 0.5) /
            math.tan(math.pi * 0.25 + SLAT1 * D * 0.5)
        )
        sf = math.tan(math.pi * 0.25 + SLAT1 * D * 0.5) ** sn * math.cos(SLAT1 * D) / sn
        ro = re * sf / math.tan(math.pi * 0.25 + OLAT * D * 0.5) ** sn
        ra = re * sf / math.tan(math.pi * 0.25 + lat * D * 0.5) ** sn
        theta = lon * D - OLON * D
        if theta >  math.pi: theta -= 2 * math.pi
        if theta < -math.pi: theta += 2 * math.pi
        nx = int(ra * math.sin(theta * sn) + XO + 0.5)
        ny = int(ro - ra * math.cos(theta * sn) + YO + 0.5)
        return nx, ny

    def _fetch_weather(self) -> tuple[float, str]:
        now = datetime.now()
        if now.minute < 10:
            now -= timedelta(hours=1)
        nx, ny = self._latlon_to_grid(self.lat, self.lon)

        try:
            res = requests.get(
                "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst",
                params={
                    "serviceKey": KMA_API_KEY,
                    "numOfRows": 10, "pageNo": 1, "dataType": "JSON",
                    "base_date": now.strftime("%Y%m%d"),
                    "base_time": now.strftime("%H00"),
                    "nx": nx, "ny": ny,
                },
                timeout=10,
            ).json()

            obs  = {i["category"]: i["obsrValue"] for i in res["response"]["body"]["items"]["item"]}
            temp = float(obs.get("T1H", 20))
            pty  = obs.get("PTY", "0")
            sky  = obs.get("SKY", "1")

            if pty != "0":
                weather = {"1":"비","2":"비/눈","3":"눈","5":"빗방울","6":"빗방울/눈","7":"눈날림"}.get(pty, "맑음")
            else:
                weather = {"1":"맑음","3":"구름많음","4":"흐림"}.get(sky, "맑음")

            print(f"☀️ [DietAgent] 날씨 API 성공 - {temp}°C {weather}")

        except Exception as e:
            print(f"☀️ [DietAgent] 날씨 API 오류: {e} → 기본값 사용")
            temp, weather = 20.0, "맑음"

        return temp, weather
