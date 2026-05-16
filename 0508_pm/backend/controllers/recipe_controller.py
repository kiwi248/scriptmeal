"""
레시피 / DB 상태 컨트롤러 — GET /api/recipes/status

ChromaDB 현재 상태와 임베딩 진행상황을 반환한다.
"""

import json
import logging
import os

from fastapi import APIRouter, HTTPException

from backend.config import CHROMA_DIR, PROGRESS_FILE, TARGET_RECIPES
from backend.db.chroma_client import get_collection_count
from backend.models.recipe_model import DBStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("/status", response_model=DBStatusResponse)
async def get_db_status() -> DBStatusResponse:
    """
    벡터 DB 현재 상태를 반환한다.
    - 컬렉션 문서 수
    - 마지막 임베딩 인덱스
    - 목표 레시피 수
    """
    logger.info("[RecipeController] GET /api/recipes/status")

    try:
        count = get_collection_count()
        logger.info("[RecipeController] 컬렉션 크기: %d", count)
    except Exception as exc:
        logger.error("[RecipeController] ChromaDB 접근 실패: %s", exc)
        raise HTTPException(status_code=503, detail=f"DB 접근 실패: {exc}") from exc

    last_index = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            progress   = json.load(f)
            last_index = progress.get("last_index", 0)
    logger.debug("[RecipeController] last_index=%d", last_index)

    return DBStatusResponse(
        chroma_dir      = CHROMA_DIR,
        collection_count= count,
        last_index      = last_index,
        total_recipes   = last_index,
        target_recipes  = TARGET_RECIPES,
        is_ready        = count > 0,
    )
