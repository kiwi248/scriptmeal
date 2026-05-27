"""
다이어트 레시피 AI - FastAPI 서버

실행:
  uvicorn backend.main:app --reload --port 8000

API 문서:
  http://localhost:8000/docs
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.chat import router
from backend.routers.user import router as user_router



app = FastAPI(
    title="다이어트 레시피 AI API",
    description="멀티에이전트 기반 다이어트 레시피 추천 서비스",
    version="1.0.0",
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
