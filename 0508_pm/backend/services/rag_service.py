"""
RAG 서비스 (대화 이력 유지 모드).

LangChain 1.x LCEL 패턴 사용:
  - RunnableWithMessageHistory 로 세션별 대화 이력 관리
  - similarity_search_with_score 로 검색 점수 포함 로깅
  - 각 단계(검색 → 컨텍스트 빌드 → 프롬프트 → LLM → 파싱) 로그 기록

[LangChain 1.x 마이그레이션 변경사항]
  - ChatMessageHistory: langchain_community → langchain_core.chat_history.InMemoryChatMessageHistory
  - 타입 힌트: X | None  →  Optional[X]  (Python 3.9 호환)
"""

import logging
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
# ✅ Fix 1: langchain_community → langchain_core
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_openai import ChatOpenAI

from backend.config import (
    LANGCHAIN_VERBOSE,
    LLM_MODEL,
    LLM_TEMPERATURE,
    OPENAI_API_KEY,
    RETRIEVER_K,
)
from backend.db.chroma_client import get_chroma_db
from backend.models.chat_model import ChatResponse, DebugInfo, RetrievedDoc
from backend.services.recipe_service import extract_source_names, format_docs

logger = logging.getLogger(__name__)

# ── 세션 저장소 (메모리) ───────────────────────────────────
_session_store: dict[str, InMemoryChatMessageHistory] = {}


def _get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _session_store:
        # ✅ Fix 1: ChatMessageHistory → InMemoryChatMessageHistory
        _session_store[session_id] = InMemoryChatMessageHistory()
        logger.debug("[RAGService] 신규 세션 생성 — session_id=%s", session_id)
    else:
        history = _session_store[session_id]
        logger.debug(
            "[RAGService] 기존 세션 로드 — session_id=%s, 메시지 수=%d",
            session_id, len(history.messages),
        )
    return _session_store[session_id]


# ── 체인 싱글톤 ────────────────────────────────────────────
# ✅ Fix 2: X | None 유니온 문법 → Optional[X] (Python 3.9 이하 호환)
_conversational_chain: Optional[RunnableWithMessageHistory] = None
_retriever = None


def _build_rag_chain():
    global _conversational_chain, _retriever

    logger.info("[RAGService] RAG 체인 빌드 시작")

    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        api_key=OPENAI_API_KEY,
        verbose=LANGCHAIN_VERBOSE,
    )
    logger.info("[RAGService] LLM 초기화 완료 — model=%s, temperature=%.1f",
                LLM_MODEL, LLM_TEMPERATURE)

    db = get_chroma_db()
    _retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_K},
    )
    logger.info("[RAGService] Retriever 초기화 완료 — k=%d", RETRIEVER_K)

    # ── 대화 이력 기반 질문 재구성 프롬프트 ──────────────
    contextualize_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "주어진 대화 이력과 최신 질문을 바탕으로 대화 이력 없이도 이해 가능한 "
            "단독 질문을 생성하세요. 답변하지 말고, 필요하면 재구성하고 "
            "그렇지 않으면 그대로 반환하세요.",
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    contextualize_chain = contextualize_prompt | llm | StrOutputParser()

    # ── QA 프롬프트 ────────────────────────────────────────
    qa_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """당신은 친절하고 전문적인 요리 챗봇입니다.
아래 Food.com 레시피 정보를 바탕으로 한국어로 답변하세요.

답변 규칙:
- 제공된 레시피 정보에 근거해서 레시피 하나만 답변하세요.
- 레시피 이름(한국어), 재료 목록(한국어), 상세 조리 순서(번호 포함, 한국어)를 알려주세요.
- 데이터에 없는 내용은 "해당 정보가 데이터에 없습니다"라고 답하세요.

[참고 레시피 정보]
{context}""",
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    # ── 컨텍스트 조합 함수 ─────────────────────────────────
    def build_context(input_dict: dict) -> dict:
        raw_query    = input_dict["input"]
        chat_history = input_dict.get("chat_history", [])

        # 대화 이력이 있으면 질문을 독립형으로 재구성
        if chat_history:
            logger.debug("[RAGService] 대화 이력 있음(%d개) → 질문 재구성 중...", len(chat_history))
            search_query = contextualize_chain.invoke({
                "input":        raw_query,
                "chat_history": chat_history,
            })
            logger.debug("[RAGService] 재구성된 검색 쿼리: %s", search_query)
        else:
            search_query = raw_query
            logger.debug("[RAGService] 대화 이력 없음 → 원문 쿼리 사용: %s", search_query)

        # ChromaDB 검색
        logger.info("[RAGService] ChromaDB 검색 시작 — 쿼리: %s", search_query)
        docs = _retriever.invoke(search_query)
        logger.info("[RAGService] ChromaDB 검색 완료 — 반환 문서 수: %d", len(docs))

        for i, doc in enumerate(docs, 1):
            name    = doc.metadata.get("recipe_name", "알 수 없음")
            excerpt = doc.page_content[:80].replace("\n", " ")
            logger.debug("[RAGService] TOP-%d: '%s' | 미리보기: %s…", i, name, excerpt)

        context_str = format_docs(docs)
        logger.debug("[RAGService] 컨텍스트 앞 300자:\n%s", context_str[:300])

        return {
            "input":        raw_query,
            "chat_history": chat_history,
            "context":      context_str,
        }

    # ── LCEL 체인 조립 ─────────────────────────────────────
    rag_chain = (
        RunnableLambda(build_context)
        | qa_prompt
        | llm
        | StrOutputParser()
    )
    logger.info("[RAGService] LCEL 체인 조립 완료")

    # ── 대화 이력 래핑 ─────────────────────────────────────
    _conversational_chain = RunnableWithMessageHistory(
        rag_chain,
        _get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    logger.info("[RAGService] RunnableWithMessageHistory 래핑 완료")


def get_rag_chain() -> RunnableWithMessageHistory:
    if _conversational_chain is None:
        _build_rag_chain()
    return _conversational_chain  # type: ignore


# ── 공개 invoke API ────────────────────────────────────────
async def invoke_rag(query: str, session_id: str) -> ChatResponse:
    """RAG 체인 호출 + 디버그 정보 수집"""
    logger.info("=" * 60)
    logger.info("[RAGService] invoke_rag 시작")
    logger.info("[RAGService] 쿼리: %s | session_id: %s", query, session_id)

    chain = get_rag_chain()
    db    = get_chroma_db()

    # ── 검색 결과 수집 (디버그용 점수 포함) ────────────────
    logger.info("[RAGService] similarity_search_with_score 실행 중...")
    scored_docs = db.similarity_search_with_score(query, k=RETRIEVER_K)
    logger.info("[RAGService] 검색 결과 %d개:", len(scored_docs))
    retrieved = []
    for rank, (doc, score) in enumerate(scored_docs, 1):
        name    = doc.metadata.get("recipe_name", "알 수 없음")
        excerpt = doc.page_content[:200]
        logger.info(
            "[RAGService] Rank %d | 레시피: '%s' | 유사도 점수: %.4f",
            rank, name, score,
        )
        logger.debug("[RAGService] Rank %d 내용 미리보기:\n%s", rank, excerpt)
        retrieved.append(RetrievedDoc(recipe_name=name, excerpt=excerpt, score=round(score, 4)))

    source_names = [d.recipe_name for d in retrieved]

    # ── 체인 실행 ──────────────────────────────────────────
    logger.info("[RAGService] LLM 체인 실행 중...")
    answer: str = chain.invoke(
        {"input": query},
        config={"configurable": {"session_id": session_id}},
    )
    logger.info("[RAGService] LLM 응답 수신 완료 — 길이: %d 문자", len(answer))
    logger.debug("[RAGService] 응답 앞 300자:\n%s", answer[:300])
    logger.info("=" * 60)

    return ChatResponse(
        answer    = answer,
        tool_used = "Food.com DB 검색",
        sources   = source_names,
        debug_info=DebugInfo(
            query_used     = query,
            retrieved_docs = retrieved,
            context_excerpt= format_docs([d for d, _ in scored_docs])[:500],
            tools_used     = ["recipe_database"],
        ),
    )