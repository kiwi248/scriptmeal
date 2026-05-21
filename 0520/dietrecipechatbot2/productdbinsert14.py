import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 제품 + 청크를 함께 묶어서 관리
# calories_per_100g: 액체류/소스류 + 소면류
# calories_per_unit: 고체류/과자류/곤약류 (1회 제공량 기준)
products = [
    {
        "brand": "샘표",
        "product_name": "샘표국시 현미소면 800g",
        "category": "면류",
        "calories_per_100g": 370,
        "price_range": "800g 1개 6,280원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "샘표국시 현미소면 / 면류 소면 / 370kcal(100g 기준) / 당류 1.6g / 밀가루 0% 글루텐프리 / 현미 60%·쌀 33% / 8인분 800g / 잔치국수·비빔국수·비빔밥 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "밀가루 없는 현미소면 먹고 싶어"},
            {"chunk_type": "question", "text": "글루텐프리 소면 추천해줘"},
            {"chunk_type": "question", "text": "현미로 만든 소면 뭐가 있어"},
            {"chunk_type": "question", "text": "밀가루 대신 현미로 만든 면 뭐야"},
            {"chunk_type": "question", "text": "다이어트 중인데 밀가루 없는 건강한 소면 당길 때"},
            {"chunk_type": "situation", "text": "잔치국수 만들 때 현미소면 활용"},
            {"chunk_type": "situation", "text": "비빔국수에 글루텐프리 현미소면 사용할 때"},
            {"chunk_type": "situation", "text": "밀가루 소면 대신 건강한 현미소면으로 요리"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 현미소면으로 한끼 해결"},
            {"chunk_type": "situation", "text": "글루텐 민감한 분이 소면 요리 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "일반 소면 현미 대체품"},
            {"chunk_type": "substitute", "text": "밀가루 소면 글루텐프리 대체"},
            {"chunk_type": "substitute", "text": "현미 60% 글루텐프리 소면"},
            {"chunk_type": "substitute", "text": "밀가루 0% 건강한 소면"},
            {"chunk_type": "substitute", "text": "현미쌀 글루텐프리 잔치국수 소면"},
        ]
    },
    {
        "brand": "샘표",
        "product_name": "샘표 고단백 소면 400g",
        "category": "면류",
        "calories_per_100g": 360,
        "price_range": "400g 1개 4,500원 (2개 세트 8,950원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "샘표 고단백 소면 / 면류 소면 / 360kcal(100g 기준) / 당류 2g / 단백질 16g(100g 기준) / 완두단백 함유 / 계란 2개 분량 단백질 / 진공성형 제조 쫄깃한 면발 / 잔치국수·비빔국수 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "고단백 소면 먹고 싶어"},
            {"chunk_type": "question", "text": "단백질 많은 소면 추천해줘"},
            {"chunk_type": "question", "text": "운동하면서 먹을 수 있는 고단백 면 뭐야"},
            {"chunk_type": "question", "text": "일반 소면보다 단백질 높은 소면 뭐가 있어"},
            {"chunk_type": "question", "text": "완두단백 들어간 고단백 소면 추천해줘"},
            {"chunk_type": "situation", "text": "운동 후 단백질 보충할 때 고단백 소면으로 식사"},
            {"chunk_type": "situation", "text": "잔치국수 만들 때 고단백 소면 활용"},
            {"chunk_type": "situation", "text": "비빔국수에 고단백 소면 사용할 때"},
            {"chunk_type": "situation", "text": "다이어트 중 단백질 챙기면서 면 요리 즐기고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 고단백 소면으로 한끼 해결"},
            {"chunk_type": "substitute", "text": "일반 소면 고단백 대체품"},
            {"chunk_type": "substitute", "text": "단백질 부족할 때 먹는 고단백 소면"},
            {"chunk_type": "substitute", "text": "단백질 16g 고단백 소면"},
            {"chunk_type": "substitute", "text": "완두단백 계란 2개분 단백질 소면"},
            {"chunk_type": "substitute", "text": "운동식단 고단백 쫄깃한 소면"},
        ]
    },
    {
        "brand": "이쁜이표",
        # 10개 세트 13,680원 → 1개당 1,368원
        "product_name": "이쁜이표 저칼로리 저당 바로먹는 곤약메밀면 180g",
        "category": "곤약류",
        "calories_per_unit": 17,   # 1개(180g) 기준 17kcal
        "price_range": "180g 1개 1,368원 (10개 세트 13,680원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "이쁜이표 저칼로리 저당 바로먹는 곤약메밀면 / 곤약류 / 17kcal(1개 180g 기준) / 당류 0g / 곤약분말 3%·볶은메밀가루 1% / 끓이지 않고 바로 먹는 면 / 비빔면·냉면·잔치국수·우동 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 메밀 곤약면 먹고 싶어"},
            {"chunk_type": "question", "text": "끓이지 않고 바로 먹는 저칼로리 면 뭐야"},
            {"chunk_type": "question", "text": "다이어트 중인데 메밀면 당길 때"},
            {"chunk_type": "question", "text": "살 안 찌는 곤약 메밀면 추천해줘"},
            {"chunk_type": "question", "text": "곤약으로 만든 메밀면 뭐가 있어"},
            {"chunk_type": "situation", "text": "비빔면 소스에 저칼로리 곤약메밀면 바로 넣을 때"},
            {"chunk_type": "situation", "text": "냉면처럼 시원하게 저칼로리 곤약면 즐길 때"},
            {"chunk_type": "situation", "text": "잔치국수나 우동처럼 따뜻하게 곤약면 활용"},
            {"chunk_type": "situation", "text": "다이어트 중 면 요리 대신 저칼로리 곤약메밀면"},
            {"chunk_type": "situation", "text": "혼밥할 때 끓이지 않고 간편하게 곤약면 먹을 때"},
            {"chunk_type": "substitute", "text": "메밀면 저칼로리 대체 식품"},
            {"chunk_type": "substitute", "text": "일반 메밀면 곤약 대체품"},
            {"chunk_type": "substitute", "text": "17kcal 바로먹는 곤약메밀면"},
            {"chunk_type": "substitute", "text": "다이어트 메밀면 재료"},
            {"chunk_type": "substitute", "text": "곤약분말 볶은메밀가루 저칼로리 바로먹는 면"},
        ]
    },
]

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="mydb", user="myuser", password="mypassword"
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
