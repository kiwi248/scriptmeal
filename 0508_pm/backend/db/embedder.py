"""
CSV → ChromaDB 누적 임베딩 모듈.

InteractiveChatbot9.py 의 build_agent() 내 임베딩 로직을 서비스 레이어로 분리.
진행상황은 PROGRESS_FILE 에 JSON 으로 저장하며 재시작 시 이어서 처리한다.
"""

import json
import logging
import os

import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma  # type: ignore

from backend.config import (
    CSV_PATH,
    CHROMA_DIR,
    PROGRESS_FILE,
    TARGET_RECIPES,
)
from backend.db.chroma_client import get_chroma_db, get_embeddings

logger = logging.getLogger(__name__)

BATCH_SIZE  = 1000   # 로그 출력 간격
CHROMA_MAX  = 5000   # Chroma add_documents 최대 배치 크기


# ── Document 생성 ──────────────────────────────────────────
def _make_documents(df_slice: pd.DataFrame) -> list[Document]:
    """DataFrame 슬라이스 → LangChain Document 리스트 변환"""
    documents: list[Document] = []
    for _, row in df_slice.iterrows():
        parts = [
            f"[요리 이름] {row['name']}",
            f"[조리 시간] {int(row['minutes'])}분"      if pd.notna(row.get("minutes")) else "",
            (
                f"[재료 ({int(row['n_ingredients'])}가지)] {row['ingredients']}"
                if pd.notna(row.get("n_ingredients"))
                else f"[재료] {row['ingredients']}"
            ),
            (
                f"[조리 방법 ({int(row['n_steps'])}단계)] {row['steps']}"
                if pd.notna(row.get("n_steps"))
                else f"[조리 방법] {row['steps']}"
            ),
            f"[설명] {row['description']}"   if pd.notna(row.get("description")) else "",
            f"[태그] {row['tags']}"          if pd.notna(row.get("tags"))        else "",
            f"[영양 정보] {row['nutrition']}" if pd.notna(row.get("nutrition"))   else "",
        ]
        content = "\n".join(p for p in parts if p)
        documents.append(Document(
            page_content=content,
            metadata={
                "recipe_name":   row["name"],
                "minutes":       int(row["minutes"])       if pd.notna(row.get("minutes"))       else None,
                "n_ingredients": int(row["n_ingredients"]) if pd.notna(row.get("n_ingredients")) else None,
            },
        ))
    return documents


# ── Chroma 배치 임베딩 ─────────────────────────────────────
def _embed_in_batches(db: Chroma, docs: list[Document], label: str = "임베딩") -> None:
    total    = len(docs)
    inserted = 0
    for i in range(0, total, CHROMA_MAX):
        batch     = docs[i : i + CHROMA_MAX]
        db.add_documents(batch)
        inserted += len(batch)
        pct = inserted / total * 100
        logger.info("[Embedder][%s] %d/%d 청크 완료 (%.1f%%)", label, inserted, total, pct)
    logger.info("[Embedder][%s] 전체 완료!", label)


# ── 진행상황 로드 ──────────────────────────────────────────
def _load_progress() -> int:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("last_index", 0)
    return 0


def _save_progress(last_index: int) -> None:
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"last_index": last_index, "total_recipes": last_index},
            f, ensure_ascii=False, indent=2,
        )
    logger.info("[Embedder] 진행상황 저장 — last_index=%d", last_index)


# ── 공개 API ───────────────────────────────────────────────
def ensure_embeddings() -> None:
    """
    TARGET_RECIPES 개까지 레시피가 임베딩돼 있는지 확인하고
    부족하면 누적 추가한다. 서버 시작 시 1회 호출하면 된다.
    """
    last_index = _load_progress()
    splitter   = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    if os.path.exists(CHROMA_DIR):
        if TARGET_RECIPES <= last_index:
            logger.info(
                "[Embedder] DB 이미 최신 — last_index=%d, target=%d (추가 없음)",
                last_index, TARGET_RECIPES,
            )
            return

        logger.info("[Embedder] 누적 추가 모드: %d → %d", last_index, TARGET_RECIPES)
        logger.info("[Embedder] CSV 읽는 중: %s", CSV_PATH)
        df       = pd.read_csv(CSV_PATH)
        df_clean = df.dropna(subset=["name", "ingredients", "steps"]).reset_index(drop=True)
        df_new   = df_clean.iloc[last_index:TARGET_RECIPES]
        logger.info("[Embedder] 새로 추가할 레시피: %d개 (%d번 ~ %d번)",
                    len(df_new), last_index + 1, last_index + len(df_new))

        if len(df_new) == 0:
            return

        db         = get_chroma_db()
        new_docs   = _make_documents(df_new)
        split_docs = splitter.split_documents(new_docs)
        logger.info("[Embedder] 청킹 완료 — %d개 청크 생성, 임베딩 시작...", len(split_docs))

        _embed_in_batches(db, split_docs, label="누적 추가")
        _save_progress(last_index + len(df_new))

    else:
        logger.info("[Embedder] DB 없음 — 최초 생성 시작: %s", CHROMA_DIR)
        logger.info("[Embedder] CSV 읽는 중: %s", CSV_PATH)
        df       = pd.read_csv(CSV_PATH)
        df_clean = df.dropna(subset=["name", "ingredients", "steps"]).reset_index(drop=True)
        df_init  = df_clean.iloc[0:TARGET_RECIPES]
        logger.info("[Embedder] 레시피 %d개 로드 완료, Document 생성 중...", len(df_init))

        documents  = _make_documents(df_init)
        split_docs = splitter.split_documents(documents)
        logger.info("[Embedder] 청킹 완료 — %d개 청크 생성, 최초 임베딩 시작...", len(split_docs))

        embeddings  = get_embeddings()
        first_batch = split_docs[:BATCH_SIZE]
        db = Chroma.from_documents(first_batch, embeddings, persist_directory=CHROMA_DIR)
        logger.info("[Embedder][최초 생성] %d/%d 청크 완료 (%.1f%%)",
                    len(first_batch), len(split_docs),
                    len(first_batch) / len(split_docs) * 100)

        remaining = split_docs[BATCH_SIZE:]
        if remaining:
            _embed_in_batches(db, remaining, label="최초 생성")

        _save_progress(len(df_init))
        logger.info("[Embedder] DB 최초 생성 완료 — 총 %d개 레시피", len(df_init))
