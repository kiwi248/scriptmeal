import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 제품 + 청크를 함께 묶어서 관리
# calories_per_100g: 분말류/액체류/소스류
# calories_per_unit: 고체류/과자류 (1회 제공량 기준)
products = [
    {
        "brand": "담다",
        "product_name": "담다 화이트 마시멜로우",
        "category": "베이킹재료",
        "calories_per_100g": 344,
        "price_range": "1kg 1개 5,100원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "담다 화이트 마시멜로우 두쫀쿠 / 베이킹재료 캔디류 / 344kcal(100g 기준) / 당류 45g / 탄수화물 82g / 단백질 3.7g / 1kg 대용량 / 두바이쫀득쿠키·라이스크리스피·핫초코 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "두바이쫀득쿠키 만들 때 마시멜로우 추천해줘"},
            {"chunk_type": "question", "text": "베이킹용 마시멜로우 어떤 거 사야 해"},
            {"chunk_type": "question", "text": "두바이쫀득쿠키 재료 마시멜로우 뭐가 좋아"},
            {"chunk_type": "question", "text": "대용량 마시멜로우 추천해줘"},
            {"chunk_type": "question", "text": "두바이쫀득쿠키 만들 때 마시멜로우 추천"},
            {"chunk_type": "situation", "text": "두바이쫀득쿠키 만들 때 마시멜로우 녹여 사용"},
            {"chunk_type": "situation", "text": "라이스크리스피 바 만들 때 마시멜로우 활용"},
            {"chunk_type": "situation", "text": "핫초코에 마시멜로우 띄워 먹을 때"},
            {"chunk_type": "situation", "text": "다이어트 디저트 베이킹 재료로 마시멜로우 사용"},
            {"chunk_type": "situation", "text": "쫀득한 식감 내는 베이킹에 마시멜로우 녹여 활용"},
            {"chunk_type": "substitute", "text": "두바이쫀득쿠키 마시멜로우 재료"},
            {"chunk_type": "substitute", "text": "베이킹용 대용량 화이트 마시멜로우"},
            {"chunk_type": "substitute", "text": "쫀득한 디저트 재료 마시멜로우"},
            {"chunk_type": "substitute", "text": "두쫀쿠 마시멜로우 1kg 베이킹"},
            {"chunk_type": "substitute", "text": "라이스크리스피 쫀득쿠키 마시멜로우 재료"},
        ]
    },
    {
        "brand": "오넛티",
        "product_name": "오넛티 피스타치오 오리지널 80g",
        "category": "스프레드",
        "calories_per_unit": 510,   # 1개(80g) 기준 510kcal
        "price_range": "80g 1개 11,000원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오넛티 피스타치오 오리지널 / 스프레드 / 510kcal(1개 80g 기준) / 당류 1g 미만 / 지방 40.7g / 단백질 18.4g / 피스타치오 89%(미국산)·마카다미아 11%(호주산) / 첨가물 없음 / HACCP 인증 / 빵·크래커·두바이초콜릿 활용"},
            {"chunk_type": "question", "text": "피스타치오 스프레드 추천해줘"},
            {"chunk_type": "question", "text": "두바이쫀득쿠키 피스타치오 크림 뭐가 좋아"},
            {"chunk_type": "question", "text": "첨가물 없는 피스타치오 버터 추천"},
            {"chunk_type": "question", "text": "카다이프 면이랑 피스타치오 스프레드는?"},
            {"chunk_type": "question", "text": "두바이초콜릿 만들 때 피스타치오 크림 뭐 써"},
            {"chunk_type": "situation", "text": "두바이쫀득쿠키 만들 때 피스타치오 스프레드 활용"},
            {"chunk_type": "situation", "text": "빵이나 크래커에 피스타치오 스프레드 발라 먹을 때"},
            {"chunk_type": "situation", "text": "두바이초콜릿 속 재료로 피스타치오 크림 사용"},
            {"chunk_type": "situation", "text": "다이어트 간식으로 피스타치오 스프레드 활용"},
            {"chunk_type": "situation", "text": "카다이프 면 요리에 피스타치오 스프레드 곁들일 때"},
            {"chunk_type": "substitute", "text": "피스타치오 버터 스프레드 첨가물 없음"},
            {"chunk_type": "substitute", "text": "두바이쫀득쿠키 피스타치오 크림 재료"},
            {"chunk_type": "substitute", "text": "피스타치오 89% 마카다미아 11% 스프레드"},
            {"chunk_type": "substitute", "text": "당류 1g 미만 건강한 피스타치오 버터"},
            {"chunk_type": "substitute", "text": "두바이초콜릿 카다이프 피스타치오 스프레드 재료"},
        ]
    },
]

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

register_vector(conn)
cur = conn.cursor()

for p in products:
    calories_per_unit = p.get("calories_per_unit")
    calories_per_100g = p.get("calories_per_100g")

    cur.execute("""
        INSERT INTO products
            (brand, product_name, category, calories_per_unit, calories_per_100g, price_range, retailers)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        p["brand"], p["product_name"], p.get("category"),
        calories_per_unit, calories_per_100g,
        p["price_range"], p["retailers"],
    ))

    product_id = cur.fetchone()[0]
    print(f"제품 삽입: {p['product_name']} (id={product_id})")

    for chunk in p["chunks"]:
        embedding = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk["text"]
        ).data[0].embedding

        cur.execute("""
            INSERT INTO product_embeddings (product_id, chunk_type, text, embedding)
            VALUES (%s, %s, %s, %s)
        """, (product_id, chunk["chunk_type"], chunk["text"], embedding))

conn.commit()
print(f"✅ 제품 {len(products)}개 삽입 완료!")

cur.close()
conn.close()
