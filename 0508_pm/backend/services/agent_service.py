"""
에이전트 서비스 (RAG + Tavily 웹서치 통합 모드).

LangGraph 1.x 패턴:
  - create_react_agent (langgraph) 사용
  - MemorySaver 로 세션별 대화 이력 관리
  - intermediate_steps 에서 사용 툴·입력·출력 전부 로깅

[LangChain/LangGraph 1.x 마이그레이션 변경사항]
  - TavilySearchResults: .tools.tavily_search → .tools (경로 단축)
  - create_react_agent: prompt= → state_modifier= (파라미터명 변경)
  - ToolMessage 파싱: msg.name 단독 사용 불안정
    → AIMessage.tool_calls 에서 tool name 수집 후 ToolMessage와 매핑
"""

import logging
from typing import Any, Optional

from langchain_core.tools import Tool
# ✅ Fix 3: 임포트 경로 단축 (두 경로 모두 동작하나 신규 경로 권장)
from langchain_community.tools import TavilySearchResults
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from backend.config import (
    LANGCHAIN_VERBOSE,
    LLM_MODEL,
    LLM_TEMPERATURE,
    OPENAI_API_KEY,
    RETRIEVER_K,
    TAVILY_API_KEY,
)
from backend.db.chroma_client import get_chroma_db
from backend.models.chat_model import (
    ChatResponse,
    DebugInfo,
    IntermediateStep,
)
from backend.services.recipe_service import format_docs

logger = logging.getLogger(__name__)

TOOL_LABEL_MAP = {
    "recipe_database":            "Food.com DB 검색",
    "tavily_search_results_json": "웹 실시간 검색",
}

SYSTEM_PROMPT = """당신은 친절한 요리 전문 AI 챗봇입니다.
요리/레시피 관련 질문에는 반드시 아래 순서대로 도구를 사용하세요.

[도구 사용 규칙 — 반드시 준수]

1순위: recipe_database 툴
  - 모든 레시피/요리 질문에 무조건 먼저 사용하세요.
  - 재료, 조리법, 대체 재료, 영양 정보 등 모든 요리 관련 질문이 해당됩니다.
  - DB 결과가 나오면 그 결과를 기반으로 답변하세요.

2순위: tavily_search_results_json 툴
  - recipe_database 결과가 부족하거나 없을 때 사용하세요.
  - 최신 트렌드, SNS 유행 레시피, 최근 뉴스 등 시사성 질문일 때 사용하세요.

직접 답변 (도구 없이):
  - 날씨, 인사 등 요리와 전혀 무관한 일상 대화에만 해당합니다.
  - 레시피나 요리에 관한 질문이라면 절대 직접 답변하지 말고 반드시 도구를 먼저 사용하세요.

반드시 한국어로 답변하세요."""

# ── 에이전트 싱글톤 ────────────────────────────────────────
_agent = None
_memory = MemorySaver()


def _build_agent():
    global _agent
    logger.info("[AgentService] 에이전트 빌드 시작")

    # ── LLM ────────────────────────────────────────────────
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        api_key=OPENAI_API_KEY,
    )
    logger.info("[AgentService] LLM 초기화 — model=%s", LLM_MODEL)

    # ── Retriever & RAG 툴 ─────────────────────────────────
    db = get_chroma_db()
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_K},
    )

    def _rag_func(query: str) -> str:
        logger.info("[AgentService][RAG Tool] 쿼리: %s", query)
        docs = retriever.invoke(query)
        logger.info("[AgentService][RAG Tool] 검색 결과 %d개", len(docs))
        for i, doc in enumerate(docs, 1):
            name = doc.metadata.get("recipe_name", "알 수 없음")
            excerpt = doc.page_content[:80].replace("\n", " ")
            logger.debug("[AgentService][RAG Tool] TOP-%d: '%s' | %s…", i, name, excerpt)
        context = format_docs(docs)
        logger.debug("[AgentService][RAG Tool] 컨텍스트 앞 300자:\n%s", context[:300])
        return context

    rag_tool = Tool(
        name="recipe_database",
        description=(
            "Food.com 레시피 DB를 검색합니다. "
            "일반적인 요리 레시피 질문(재료, 조리법, 영양정보 등)에 사용하세요."
        ),
        func=_rag_func,
    )
    logger.info("[AgentService] RAG Tool 등록 완료")

    # ── Tavily 웹서치 툴 ────────────────────────────────────
    web_tool = TavilySearchResults(
        max_results=3,
        tavily_api_key=TAVILY_API_KEY,
    )
    logger.info("[AgentService] Tavily Web Search Tool 등록 완료")

    # ── LangGraph 에이전트 생성 ────────────────────────────
    # ✅ Fix 4: prompt= → state_modifier= (LangGraph 0.2+ 파라미터명 변경)
    _agent = create_react_agent(
        model=llm,
        tools=[rag_tool, web_tool],
        checkpointer=_memory,
        prompt=SYSTEM_PROMPT,  # ← 핵심 수정
    )
    logger.info("[AgentService] LangGraph create_react_agent 생성 완료")


def get_agent():
    if _agent is None:
        _build_agent()
    return _agent


# ── 공개 invoke API ────────────────────────────────────────
async def invoke_agent(query: str, session_id: str) -> ChatResponse:
    logger.info("=" * 60)
    logger.info("[AgentService] invoke_agent 시작")
    logger.info("[AgentService] 쿼리: %s | session_id: %s", query, session_id)

    agent = get_agent()
    config = {"configurable": {"thread_id": session_id}}

    logger.info("[AgentService] 에이전트 실행 중...")
    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]},
        config=config,
    )

    # ── 최종 답변 추출 ─────────────────────────────────────
    messages = result["messages"]
    answer = messages[-1].content
    logger.info("[AgentService] 응답 수신 — 길이: %d 문자", len(answer))

    # ── 툴 사용 내역 파싱 (LangGraph 1.x 방식) ─────────────
    # ✅ Fix 5: AIMessage.tool_calls → tool_id:name 맵 먼저 구성,
    #           ToolMessage에서 tool_call_id로 매핑 (msg.name은 None일 수 있음)
    steps_parsed: list[IntermediateStep] = []
    tools_used: list[str] = []

    # Step 1: AIMessage에서 tool_call_id → tool_name 맵 구성
    tool_id_to_name: dict[str, str] = {}
    tool_id_to_input: dict[str, Any] = {}
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_id_to_name[tc["id"]] = tc["name"]
                tool_id_to_input[tc["id"]] = tc.get("args", {})

    # Step 2: ToolMessage에서 결과 수집
    for msg in messages:
        if isinstance(msg, ToolMessage):
            tool_call_id = msg.tool_call_id
            # msg.name 이 있으면 우선 사용, 없으면 맵에서 조회
            tool_name = msg.name or tool_id_to_name.get(tool_call_id, "unknown")
            tool_input = tool_id_to_input.get(tool_call_id, {})
            tool_output = str(msg.content)[:500]

            tools_used.append(tool_name)
            steps_parsed.append(IntermediateStep(
                tool=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
            ))
            logger.info("[AgentService] 툴 사용: %s", tool_name)
            logger.debug("[AgentService] 툴 출력 앞 300자:\n%s", tool_output[:300])

    # ── 툴 레이블 조합 ─────────────────────────────────────
    if not tools_used:
        tool_label = "직접 답변"
    elif len(tools_used) == 1:
        tool_label = TOOL_LABEL_MAP.get(tools_used[0], tools_used[0])
    else:
        labels = [TOOL_LABEL_MAP.get(t, t) for t in tools_used]
        tool_label = " → ".join(labels)

    logger.info("[AgentService] 사용 툴 레이블: %s", tool_label)
    logger.info("=" * 60)

    return ChatResponse(
        answer=answer,
        tool_used=tool_label,
        sources=[],
        debug_info=DebugInfo(
            query_used=query,
            tools_used=tools_used,
            intermediate_steps=steps_parsed,
        ),
    )