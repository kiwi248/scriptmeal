from pydantic import BaseModel
from typing import Optional


class RecipeDocument(BaseModel):
    """CSV 한 행 → LangChain Document 변환 전 중간 모델"""
    name: str
    minutes: Optional[int] = None
    n_ingredients: Optional[int] = None
    ingredients: str
    steps: str
    description: Optional[str] = None
    tags: Optional[str] = None
    nutrition: Optional[str] = None


class DBStatusResponse(BaseModel):
    """벡터 DB 현재 상태 응답"""
    chroma_dir: str
    collection_count: int
    last_index: int
    total_recipes: int
    target_recipes: int
    is_ready: bool
