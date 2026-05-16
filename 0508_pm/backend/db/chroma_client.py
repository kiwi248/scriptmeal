"""
ChromaDB 싱글톤 클라이언트.

get_chroma_db() 를 호출하면 최초 1회만 디스크에서 로드하고 이후 캐시된
인스턴스를 반환한다. 컬렉션 크기 등 주요 상태를 DEBUG 레벨로 기록한다.
"""

import logging

try:
    from langchain_chroma import Chroma
except ImportError:                              # langchain-chroma 미설치 시 폴백
    from langchain_community.vectorstores import Chroma  # type: ignore

from langchain_openai import OpenAIEmbeddings

from backend.config import OPENAI_API_KEY, CHROMA_DIR, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_db: Chroma | None = None


# ── 임베딩 팩토리 ──────────────────────────────────────────
def get_embeddings() -> OpenAIEmbeddings:
    logger.debug("[ChromaDB] OpenAIEmbeddings 생성: model=%s", EMBEDDING_MODEL)
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
    )


# ── DB 싱글톤 ──────────────────────────────────────────────
def get_chroma_db() -> Chroma:
    global _db
    if _db is not None:
        return _db

    logger.info("[ChromaDB] 벡터 DB 로딩 시작 — persist_dir=%s", CHROMA_DIR)
    embeddings = get_embeddings()

    _db = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )

    count = _db._collection.count()
    logger.info("[ChromaDB] 로드 완료 — 컬렉션 크기: %d 개 문서", count)
    return _db


def get_collection_count() -> int:
    """현재 컬렉션 문서 수 반환 (DB가 로드돼 있어야 함)"""
    db = get_chroma_db()
    return db._collection.count()
