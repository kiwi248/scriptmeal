import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 제품 + 청크를 함께 묶어서 관리
# calories_per_100g: 액체류/소스류
# calories_per_unit: 고체류/과자류 (1회 제공량 기준)
products = [
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 조리용 저당 굴소스",
        "category": "소스류",
        "calories_per_100g": 35,
        "price_range": "340g 1개 4,480원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 조리용 저당 굴소스 / 소스류 굴소스 / 35kcal(100g 기준) / 당류 0.5g / 알룰로스 13.4g / HACCP 인증 / 조리용"},
            {"chunk_type": "question", "text": "당 적은 조리용 굴소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 굴소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 볶음 요리에 굴소스 쓰고 싶어"},
            {"chunk_type": "question", "text": "일반 굴소스 대신 먹을 수 있는 저당 조리용 버전 뭐야"},
            {"chunk_type": "question", "text": "감칠맛 살아있는 저당 조리용 굴소스 추천해줘"},
            {"chunk_type": "situation", "text": "볶음 요리에 감칠맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "다이어트 식단 조리에 저당 굴소스 활용"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 굴소스로 요리"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살 볶음에 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 굴소스 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "조리용 굴소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 조리용 굴소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 0.5g 저당 조리용 굴소스"},
            {"chunk_type": "substitute", "text": "일반 굴소스의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 굴농축액 저당 조리용 굴소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저칼로리 스윗칠리소스 320g",
        "category": "소스류",
        "calories_per_100g": 30,
        "price_range": "320g 1개 3,980원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저칼로리 스윗칠리소스 / 소스류 스위트칠리 / 30kcal(100g 기준) / 당류 2g / 알룰로스 10.7g / 닭가슴살·월남쌈·새우요리 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 스윗칠리소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저칼로리 칠리소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤달콤한 칠리소스 당길 때"},
            {"chunk_type": "question", "text": "일반 스윗칠리소스 대신 먹을 수 있는 저칼로리 버전 뭐야"},
            {"chunk_type": "question", "text": "닭가슴살에 곁들일 저칼로리 칠리소스 추천해줘"},
            {"chunk_type": "situation", "text": "닭가슴살 요리에 매콤달콤한 소스로 활용할 때"},
            {"chunk_type": "situation", "text": "월남쌈 소스로 저칼로리 칠리소스 쓸 때"},
            {"chunk_type": "situation", "text": "새우요리에 디핑 소스로 활용할 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 포인트 소스 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 칠리소스 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "스윗칠리소스 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 스윗칠리소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "30kcal 저칼로리 스윗칠리소스"},
            {"chunk_type": "substitute", "text": "일반 스윗칠리소스의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 매콤달콤 칠리소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저칼로리 치킨양념소스",
        "category": "소스류",
        "calories_per_100g": 35,
        "price_range": "320g 1개 3,500원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저칼로리 치킨양념소스 / 소스류 치킨양념 / 35kcal(100g 기준) / 당류 2g / 알룰로스 함유 / 닭가슴살·월남쌈·새우요리 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 치킨양념소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저칼로리 치킨소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤달콤한 치킨양념 당길 때"},
            {"chunk_type": "question", "text": "일반 치킨양념소스 대신 먹을 수 있는 저칼로리 버전 뭐야"},
            {"chunk_type": "question", "text": "닭가슴살에 곁들일 저칼로리 치킨양념 추천해줘"},
            {"chunk_type": "situation", "text": "닭가슴살 요리에 매콤달콤한 양념으로 활용할 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 치킨양념 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 소스 활용"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살에 양념소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 치킨양념 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "치킨양념소스 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 치킨양념소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "35kcal 저칼로리 치킨양념소스"},
            {"chunk_type": "substitute", "text": "일반 치킨양념의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 저당 매콤달콤 치킨소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저칼로리 토마토케찹 320g",
        "category": "소스류",
        "calories_per_100g": 35,
        "price_range": "320g 1개 3,790원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저칼로리 토마토케찹 / 소스류 케찹 / 35kcal(100g 기준) / 당류 4g / 알룰로스 8.8g / 닭가슴살·오므라이스 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 토마토케찹 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저칼로리 케찹"},
            {"chunk_type": "question", "text": "다이어트 중인데 케찹 당길 때"},
            {"chunk_type": "question", "text": "일반 케찹 대신 먹을 수 있는 저칼로리 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저칼로리 토마토케찹 추천해줘"},
            {"chunk_type": "situation", "text": "오므라이스나 튀김에 케찹 뿌릴 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 새콤달콤한 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 케찹 활용"},
            {"chunk_type": "situation", "text": "닭가슴살 요리에 케찹 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 케찹 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "토마토케찹 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 케찹 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "35kcal 저칼로리 토마토케찹"},
            {"chunk_type": "substitute", "text": "일반 케찹의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 토마토케찹"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저칼로리 데리야끼소스",
        "category": "소스류",
        "calories_per_100g": 35,
        "price_range": "285g 1개 3,380원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저칼로리 데리야끼소스 / 소스류 데리야끼 / 35kcal(100g 기준) / 당류 4g / 알룰로스 94g / 구이·볶음·조림 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 데리야끼소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저칼로리 데리야끼"},
            {"chunk_type": "question", "text": "다이어트 중인데 달콤짭조름한 데리야끼 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 데리야끼소스 대신 먹을 수 있는 저칼로리 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 데리야끼소스 추천해줘"},
            {"chunk_type": "situation", "text": "구이 요리에 달콤짭조름한 데리야끼 소스 활용"},
            {"chunk_type": "situation", "text": "다이어트 식단에 데리야끼 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 데리야끼소스 활용"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살 구이에 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 데리야끼 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "데리야끼소스 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 데리야끼소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "35kcal 저칼로리 데리야끼소스"},
            {"chunk_type": "substitute", "text": "일반 데리야끼소스의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 달콤짭조름 데리야끼"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 데리야끼소스",
        "category": "소스류",
        "calories_per_100g": 40,
        "price_range": "340g 1개 4,300원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 데리야끼소스 / 소스류 데리야끼 / 40kcal(100g 기준) / 당류 3g / 액상알룰로스 18.89g / HACCP 인증 / 100g당 40kcal 미만 진짜 저당"},
            {"chunk_type": "question", "text": "당 적은 데리야끼소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 데리야끼"},
            {"chunk_type": "question", "text": "다이어트 중인데 달콤짭조름한 데리야끼 당길 때"},
            {"chunk_type": "question", "text": "일반 데리야끼소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 진짜 저당 데리야끼소스 추천해줘"},
            {"chunk_type": "situation", "text": "구이·볶음·조림 요리에 저당 데리야끼 소스 활용"},
            {"chunk_type": "situation", "text": "다이어트 식단에 깊은 데리야끼 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 데리야끼소스 활용"},
            {"chunk_type": "situation", "text": "운동 후 단백질 요리에 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 데리야끼 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "데리야끼소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 데리야끼소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 3g 저당 데리야끼소스"},
            {"chunk_type": "substitute", "text": "일반 데리야끼소스의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 달콤짭조름 데리야끼 소스"},
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
