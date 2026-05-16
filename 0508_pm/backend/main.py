"""
FastAPI 애플리케이션 엔트리 포인트.

실행:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

또는 프로젝트 루트에서:
    python -m uvicorn backend.main:app --reload
"""

import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import CORS_ORIGINS, LANGCHAIN_DEBUG, LANGCHAIN_VERBOSE
from backend.controllers.chat_controller import router as chat_router
from backend.controllers.recipe_controller import router as recipe_router
from backend.db.embedder import ensure_embeddings
from backend.services.agent_service import get_agent
from backend.services.rag_service import get_rag_chain

# ── 로깅 설정 ─────────────────────────────────────────────
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class":     "logging.StreamHandler",
            "formatter": "detailed",
            "level":     "DEBUG",
        },
    },
    "root": {
        "handlers": ["console"],
        "level":    "DEBUG",
    },
    # 너무 시끄러운 서드파티 라이브러리 억제
    "loggers": {
        "httpx":          {"level": "WARNING"},
        "httpcore":       {"level": "WARNING"},
        "openai":         {"level": "WARNING"},
        "chromadb":       {"level": "INFO"},
        "uvicorn.access": {"level": "INFO"},
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# ── LangChain 전역 verbose / debug ────────────────────────
from langchain_core.globals import set_debug, set_verbose  # noqa: E402

set_verbose(LANGCHAIN_VERBOSE)
set_debug(LANGCHAIN_DEBUG)
logger.info(
    "LangChain 설정 — verbose=%s, debug=%s",
    LANGCHAIN_VERBOSE, LANGCHAIN_DEBUG,
)


# ── 수명주기 핸들러 ───────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 DB 임베딩 확인 및 체인 워밍업"""
    logger.info("=" * 60)
    logger.info("서버 시작 — 임베딩 확인 중...")
    ensure_embeddings()          # 누락 레시피 임베딩 (이미 완료면 바로 반환)
    logger.info("RAG 체인 초기화 중...")
    get_rag_chain()              # 체인 미리 빌드
    logger.info("에이전트 초기화 중...")
    get_agent()                  # 에이전트 미리 빌드
    logger.info("서버 준비 완료!")
    logger.info("=" * 60)
    yield
    logger.info("서버 종료")


# ── FastAPI 앱 ────────────────────────────────────────────
app = FastAPI(
    title="AI 레시피 챗봇 API",
    description="Food.com 레시피 DB + 실시간 웹서치 기반 요리 챗봇",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat_router)
app.include_router(recipe_router)

# 프론트엔드 정적 파일 서빙
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
