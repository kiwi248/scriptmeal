import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 제품 데이터
products = [
      {
        "brand": "농심",
        "product_name": "누들핏 김치사발면맛",
        "category": "면류",
        "calories": 130,
        "price_range": "8개 9,890원(개당1,236원)",
        "retailers": ["쿠팡"],
    }
]

# ── 섹션별 임베딩 청크 ────────────────────────────────────────────────────────
# 같은 product_id에 대해 chunk_type별로 행을 나눠 저장
# → 유저 쿼리 성격에 따라 가장 관련 있는 청크가 매칭되고,
#   동일 제품이 여러 각도에서 검색에 걸림

embeddings_to_insert = [

    # ── [기본 정보] ─────────────────────────────────────────────────────────
    {
        "product_id": 1,
        "chunk_type": "basic_info",
        "text": "농심 누들핏 김치사발면맛 / 면류 김치 / 130kcal"
    },

    # ── [가상 질문] 5개 ──────────────────────────────────────────────────────
    {
        "product_id": 1,
        "chunk_type": "question",
        "text": "살 안 찌는 김치라면 먹고 싶어"
    },
    {
        "product_id": 1,
        "chunk_type": "question",
        "text": "죄책감 없이 먹을 수 있는 매콤한 컵라면"
    },
    {
        "product_id": 1,
        "chunk_type": "question",
        "text": "다이어트 중인데 칼칼한 국물 당길 때"
    },
    {
        "product_id": 1,
        "chunk_type": "question",
        "text": "일반 김치라면 대신 먹을 수 있는 거 뭐야"
    },
    {
        "product_id": 1,
        "chunk_type": "question",
        "text": "국물까지 다 먹어도 130칼로리인 라면"
    },

    # ── [상황] 5개 ───────────────────────────────────────────────────────────
    {
        "product_id": 1,
        "chunk_type": "situation",
        "text": "야식으로 먹어도 되는 매콤한 면"
    },
    {
        "product_id": 1,
        "chunk_type": "situation",
        "text": "혼밥할 때 간편하게 다이어트 식사"
    },
    {
        "product_id": 1,
        "chunk_type": "situation",
        "text": "운동하고 나서 먹어도 되는 면류"
    },
    {
        "product_id": 1,
        "chunk_type": "situation",
        "text": "밤에 매운 게 당길 때 부담 없이"
    },
    {
        "product_id": 1,
        "chunk_type": "situation",
        "text": "얼큰하고 개운한 국물이 먹고 싶을 때"
    },

    # ── [대체재] 5개 ─────────────────────────────────────────────────────────
    {
        "product_id": 1,
        "chunk_type": "substitute",
        "text": "김치사발면 저칼로리 버전"
    },
    {
        "product_id": 1,
        "chunk_type": "substitute",
        "text": "인스턴트 김치라면 다이어트 대체품"
    },
    {
        "product_id": 1,
        "chunk_type": "substitute",
        "text": "130칼로리 매콤한 컵라면"
    },
    {
        "product_id": 1,
        "chunk_type": "substitute",
        "text": "일반 김치라면의 절반 칼로리"
    },
    {
        "product_id": 1,
        "chunk_type": "substitute",
        "text": "식이섬유 함유 저칼로리 면류"
    },
{
        "brand": "농심",
        "product_name": "누들핏 마라탄탄",
        "category": "면류",
        "calories": 135,
        "price_range": "8개 9,890원(개당1,236원)",
        "retailers": ["쿠팡"],
    }
]

# ── 섹션별 임베딩 청크 ────────────────────────────────────────────────────────
# 같은 product_id에 대해 chunk_type별로 행을 나눠 저장
# → 유저 쿼리 성격에 따라 가장 관련 있는 청크가 매칭되고,
#   동일 제품이 여러 각도에서 검색에 걸림

embeddings_to_insert = [

    # ── [기본 정보] ─────────────────────────────────────────────────────────
    {
        "product_id": 1,
        "chunk_type": "basic_info",
        "text": "농심 누들핏 마라탄탄 / 면류 마라 비빔면 / 135kcal"
    },

    # ── [가상 질문] 5개 ──────────────────────────────────────────────────────
    {
        "product_id": 1,
        "chunk_type": "question",
        "text": "살 안 찌는 마라 컵라면 먹고 싶어"
    },
    {
        "product_id": 1,
        "chunk_type": "question",
        "text": "죄책감 없이 먹을 수 있는 마라탄탄면"
    },
    {
        "product_id": 1,
        "chunk_type": "question",
        "text": "다이어트 중인데 마라향 매콤한 면 당길 때"
    },
    {
        "product_id": 1,
        "chunk_type": "question",
        "text": "일반 마라탕 대신 먹을 수 있는 거 뭐야"
    },
    {
        "product_id": 1,
        "chunk_type": "question",
        "text": "135칼로리 비빔타입 컵면 추천"
    },

    # ── [상황] 5개 ───────────────────────────────────────────────────────────
    {
        "product_id": 1,
        "chunk_type": "situation",
        "text": "야식으로 먹어도 되는 마라면"
    },
    {
        "product_id": 1,
        "chunk_type": "situation",
        "text": "혼밥할 때 간편하게 다이어트 식사"
    },
    {
        "product_id": 1,
        "chunk_type": "situation",
        "text": "운동하고 나서 먹어도 되는 면류"
    },
    {
        "product_id": 1,
        "chunk_type": "situation",
        "text": "매콤하고 고소한 탄탄면이 먹고 싶을 때"
    },
    {
        "product_id": 1,
        "chunk_type": "situation",
        "text": "색다른 비빔타입 저칼로리 면 먹고 싶을 때"
    },

    # ── [대체재] 5개 ─────────────────────────────────────────────────────────
    {
        "product_id": 1,
        "chunk_type": "substitute",
        "text": "마라탕 저칼로리 버전"
    },
    {
        "product_id": 1,
        "chunk_type": "substitute",
        "text": "인스턴트 마라면 다이어트 대체품"
    },
    {
        "product_id": 1,
        "chunk_type": "substitute",
        "text": "135칼로리 마라 비빔면"
    },
    {
        "product_id": 1,
        "chunk_type": "substitute",
        "text": "일반 마라탄탄면의 절반 칼로리"
    },
    {
        "product_id": 1,
        "chunk_type": "substitute",
        "text": "식이섬유 함유 크리미한 소스 저칼로리 면류"
    },

]

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="mydb", user="myuser", password="mypassword"
)
register_vector(conn)
cur = conn.cursor()

for p in products:
    cur.execute("""
        INSERT INTO products
            (brand, product_name, category,
             calories, price_range, retailers)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        p["brand"],
        p["product_name"],
        p.get("category"),
        p["calories"],
        p["price_range"],
        p["retailers"],
    ))

# product_embeddings 테이블에 청크별 삽입
for chunk in embeddings_to_insert:]
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunk["text"]
    ).data[0].embedding

    cur.execute("""
        INSERT INTO product_embeddings (product_id, chunk_type, text, embedding)
        VALUES (%s, %s, %s, %s)
    """, [chunk["product_id"], chunk["chunk_type"], chunk["text"], embedding])

conn.commit()
print(f"✅ 제품 {len(products)}개 삽입 완료!")

cur.close()
conn.close()