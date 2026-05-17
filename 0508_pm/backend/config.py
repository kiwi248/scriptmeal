import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ─────────────────────────────────────────────────
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY  = os.getenv("TAVILY_API_KEY", "")

# ── File Paths ───────────────────────────────────────────────
CSV_PATH        = os.getenv("CSV_PATH",       r"D:\scriptmealdata\kaggle_data\RAW_recipes.csv")
CHROMA_DIR      = os.getenv("CHROMA_DIR",     r"D:\scriptmealdata\chroma_cooking_db")
PROGRESS_FILE   = os.getenv("PROGRESS_FILE",  r"D:\scriptmeal\0508_pm\chroma_progress.json")

# ── Embedding / RAG ──────────────────────────────────────────
TARGET_RECIPES   = int(os.getenv("TARGET_RECIPES",   "100000"))
LLM_MODEL        = os.getenv("LLM_MODEL",            "gpt-4o-mini")
EMBEDDING_MODEL  = os.getenv("EMBEDDING_MODEL",      "text-embedding-ada-002")
LLM_TEMPERATURE  = float(os.getenv("LLM_TEMPERATURE", "0.3"))
RETRIEVER_K      = int(os.getenv("RETRIEVER_K",      "3"))

# ── Server ───────────────────────────────────────────────────
CORS_ORIGINS = ["*"]

# ── LangChain verbose ────────────────────────────────────────
LANGCHAIN_VERBOSE = True   # verbose=True → 체인/에이전트 실행 로그 출력
LANGCHAIN_DEBUG   = False  # True 시 모든 입출력 원문 출력 (매우 상세)
