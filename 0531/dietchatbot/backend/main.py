"""
다이어트 레시피 AI - FastAPI 서버

실행:
  uvicorn backend.main:app --reload --port 8000

API 문서:
  http://localhost:8000/docs
"""

from dotenv import load_dotenv
load_dotenv()

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from backend.routers.chat import router, init_client
from backend.routers.user import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 앱 시작 시 OpenAI 클라이언트 한 번만 생성 ──────────────────────────
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다. .env를 확인해주세요.")
    client = OpenAI(api_key=api_key)
    init_client(client)
    print("✅ OpenAI 클라이언트 초기화 완료")
    yield
    # ── 앱 종료 시 정리 (OpenAI client는 별도 close 불필요) ────────────────
    print("🛑 서버 종료")


app = FastAPI(
    title="다이어트 레시피 AI API",
    description="AI 에이전트 기반 다이어트 레시피 추천 서비스",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 개발 환경용 — 운영 시 Streamlit 도메인으로 제한
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(user_router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
