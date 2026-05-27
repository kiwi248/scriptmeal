"""
ProductDB
─────────
pgvector 기반 제품 검색 및 조회.

테이블 구조:
  products          (id, brand, product_name, category,
                     calories_per_unit, calories_per_100g, price_range, retailers)
  product_embeddings (id, product_id, chunk_type, text, embedding)
"""

import os
import psycopg2
from pgvector.psycopg2 import register_vector


class ProductDB:
    def __init__(self):
        self._conn: psycopg2.extensions.connection | None = None

    @property
    def conn(self) -> psycopg2.extensions.connection:
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=os.environ.get("DB_HOST"),
                port=int(os.environ.get("DB_PORT", 5432)),
                dbname=os.environ.get("DB_NAME"),
                user=os.environ.get("DB_USER"),
                password=os.environ.get("DB_PASSWORD"),
            )
            register_vector(self._conn)
        return self._conn

    def get_similar_products(self, embedding: list[float], top_k: int = 5) -> list[dict]:
        """임베딩 유사도(코사인 거리)로 제품 Top-K 조회."""
        sql = """
            WITH ranked AS (
                SELECT product_id,
                       MIN(embedding <=> %s::vector) AS min_dist
                FROM product_embeddings
                GROUP BY product_id
                ORDER BY min_dist
                LIMIT %s
            )
            SELECT p.id,
                   p.brand,
                   p.product_name,
                   p.category,
                   COALESCE(p.calories_per_100g, p.calories_per_unit) AS calories,
                   p.price_range,
                   p.retailers
            FROM ranked r
            JOIN products p ON p.id = r.product_id
            ORDER BY r.min_dist
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (embedding, top_k))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_products_by_ids(self, ids: list[int]) -> list[dict]:
        """ID 목록으로 제품 상세 정보 조회."""
        if not ids:
            return []
        sql = """
            SELECT id,
                   brand,
                   product_name,
                   category,
                   COALESCE(calories_per_100g, calories_per_unit) AS calories,
                   price_range,
                   retailers
            FROM products
            WHERE id = ANY(%s)
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (ids,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


# 모듈 레벨 싱글턴 (요청마다 새 연결 방지)
_db_instance: ProductDB | None = None


def get_db() -> ProductDB:
    global _db_instance
    if _db_instance is None:
        _db_instance = ProductDB()
    return _db_instance
