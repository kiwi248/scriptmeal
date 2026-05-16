"""
레시피 관련 유틸리티 서비스.

RAG / 에이전트 서비스가 공통으로 사용하는 헬퍼 함수 모음.
"""

import logging
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def format_docs(docs: list[Document]) -> str:
    """문서 리스트를 LLM 컨텍스트 문자열로 변환하고 내용을 로그에 기록한다."""
    logger.debug("[RecipeService] 컨텍스트 포맷 시작 — 문서 수: %d", len(docs))
    for i, doc in enumerate(docs, start=1):
        name    = doc.metadata.get("recipe_name", "알 수 없음")
        minutes = doc.metadata.get("minutes",     "N/A")
        n_ing   = doc.metadata.get("n_ingredients", "N/A")
        excerpt = doc.page_content[:120].replace("\n", " ")
        logger.debug(
            "[RecipeService] 문서 %d — 이름: %s | 조리시간: %s분 | 재료수: %s | 미리보기: %s…",
            i, name, minutes, n_ing, excerpt,
        )
    joined = "\n\n---\n\n".join(doc.page_content for doc in docs)
    logger.debug("[RecipeService] 컨텍스트 총 길이: %d 문자", len(joined))
    return joined


def extract_source_names(docs: list[Document]) -> list[str]:
    """source_documents 에서 중복 없는 레시피 이름 목록 추출"""
    names = list({doc.metadata.get("recipe_name", "알 수 없음") for doc in docs})
    logger.debug("[RecipeService] 출처 레시피: %s", names)
    return names
