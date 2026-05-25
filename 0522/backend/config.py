import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
TAVILY_API_KEY: str = os.environ.get("TAVILY_API_KEY", "")
KMA_API_KEY: str = os.environ.get("KMA_API_KEY", "")
DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
