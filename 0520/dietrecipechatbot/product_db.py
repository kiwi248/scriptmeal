"""
ProductDB
─────────
pgvector를 활용한 제품 데이터베이스 모듈.

실제 환경에서는 psycopg2 + pgvector 익스텐션이 설치된
PostgreSQL DB가 필요합니다.

개발/테스트 시에는 아래 MockProductDB를 사용하세요.
"""

import os
import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector

DATABASE_URL = os.environ.get("DATABASE_URL", "")


class ProductDB:
    """
    실제 PostgreSQL + pgvector 기반 제품 DB.
    DATABASE_URL 환경변수가 없으면 MockProductDB로 자동 폴백.
    """

    def __init__(self):
        if not DATABASE_URL:
            print("[ProductDB] DATABASE_URL 미설정 → MockProductDB로 폴백")
            self._mock = MockProductDB()
        else:
            self._mock = None
            self._conn = psycopg2.connect(DATABASE_URL)
            register_vector(self._conn)

    def get_similar_products(self, embedding: list[float], top_k: int = 5) -> list[dict]:
        if self._mock:
            return self._mock.get_similar_products(embedding, top_k)

        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT p.id, p.brand, p.product_name, p.calories
                FROM product_embeddings pe
                JOIN products p ON pe.product_id = p.id
                ORDER BY pe.embedding <=> %s
                LIMIT %s
                """,
                (embedding, top_k),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_products_by_ids(self, ids: list[int]) -> list[dict]:
        if self._mock:
            return self._mock.get_products_by_ids(ids)

        if not ids:
            return []

        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT brand, product_name, calories, price_range, retailers
                FROM products
                WHERE id = ANY(%s)
                """,
                (ids,),
            )
            return [dict(row) for row in cur.fetchall()]


# ── 개발/테스트용 Mock DB ──────────────────────────────────────────────────────

MOCK_PRODUCTS = [
    {
        "id": 1,
        "brand": "농심",
        "product_name": "누들핏 짜파구리",
        "calories": 135,
        "price_range": "9,010원",
        "retailers": ["쿠팡"],
        "tags": ["짜장", "라면", "저칼로리"],
    },
    {
        "id": 2,
        "brand": "곰곰",
        "product_name": "제로슈가 스테비아 400g",
        "calories": 0,
        "price_range": "3,670원",
        "retailers": ["쿠팡"],
        "tags": ["감미료", "제로", "설탕대체"],
    },
    {
        "id": 3,
        "brand": "CJ",
        "product_name": "햇반 곤약밥 210g",
        "calories": 130,
        "price_range": "2,500원",
        "retailers": ["쿠팡", "GS25"],
        "tags": ["밥", "곤약", "저탄수"],
    },
    {
        "id": 4,
        "brand": "오뚜기",
        "product_name": "로스팅 닭가슴살 100g",
        "calories": 100,
        "price_range": "2,200원",
        "retailers": ["쿠팡", "이마트"],
        "tags": ["단백질", "닭가슴살", "고단백"],
    },
    {
        "id": 5,
        "brand": "풀무원",
        "product_name": "두부면 200g",
        "calories": 80,
        "price_range": "3,500원",
        "retailers": ["쿠팡", "홈플러스"],
        "tags": ["면", "두부", "저칼로리"],
    },
]


class MockProductDB:
    """개발·테스트용 인메모리 Mock DB (pgvector 없이도 동작)"""

    def get_similar_products(self, embedding: list[float], top_k: int = 5) -> list[dict]:
        # 실제 벡터 유사도 없이 전체 반환 (테스트용)
        return [
            {"id": p["id"], "brand": p["brand"], "product_name": p["product_name"], "calories": p["calories"]}
            for p in MOCK_PRODUCTS[:top_k]
        ]

    def get_products_by_ids(self, ids: list[int]) -> list[dict]:
        return [
            {
                "brand": p["brand"],
                "product_name": p["product_name"],
                "calories": p["calories"],
                "price_range": p["price_range"],
                "retailers": p["retailers"],
            }
            for p in MOCK_PRODUCTS
            if p["id"] in ids
        ]
