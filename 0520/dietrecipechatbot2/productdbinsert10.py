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
        "product_name": "비비드키친 저칼로리 머스터드소스 320g",
        "category": "소스류",
        "calories_per_100g": 35,
        "price_range": "320g 1개 3,910원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저칼로리 머스터드소스 / 소스류 머스터드 / 35kcal(100g 기준) / 당류 1g / 알룰로스 11.5g / 닭가슴살·튀김 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 머스터드소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저칼로리 머스터드"},
            {"chunk_type": "question", "text": "다이어트 중인데 머스터드소스 당길 때"},
            {"chunk_type": "question", "text": "일반 머스터드소스 대신 먹을 수 있는 저칼로리 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 머스터드소스 추천해줘"},
            {"chunk_type": "situation", "text": "닭가슴살 요리에 머스터드소스 곁들일 때"},
            {"chunk_type": "situation", "text": "튀김 디핑 소스로 저칼로리 머스터드 쓸 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 새콤한 머스터드 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 머스터드소스 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 머스터드 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "머스터드소스 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 머스터드소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "35kcal 저칼로리 머스터드소스"},
            {"chunk_type": "substitute", "text": "일반 머스터드소스의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 머스터드소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 볶음고추장 300g",
        "category": "소스류",
        "calories_per_100g": 105,
        "price_range": "300g 1개 6,850원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 볶음고추장 / 소스류 볶음고추장 / 105kcal(100g 기준) / 당류 2g / 알룰로스 5.5g / 쇠고기·마늘 함유 / 비빔밥·닭가슴살 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 볶음고추장 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 볶음고추장"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤한 볶음고추장 당길 때"},
            {"chunk_type": "question", "text": "일반 볶음고추장 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 깔끔하게 매운 볶음고추장 추천해줘"},
            {"chunk_type": "situation", "text": "비빔밥 양념으로 저당 볶음고추장 활용할 때"},
            {"chunk_type": "situation", "text": "닭가슴살에 곁들이는 매콤한 소스로 활용"},
            {"chunk_type": "situation", "text": "다이어트 식단에 매콤한 포인트 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 볶음고추장으로 비빔밥"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 볶음고추장 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "볶음고추장 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 볶음고추장 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 저당 볶음고추장"},
            {"chunk_type": "substitute", "text": "일반 볶음고추장의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 쇠고기마늘 저당 볶음고추장"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 갈릭디핑소스 250g",
        "category": "소스류",
        "calories_per_100g": 555,
        "price_range": "250g 1개 3,700원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 갈릭디핑소스 / 소스류 갈릭디핑 / 555kcal(100g 기준) / 당류 2.5g / 알룰로스 2.36g / 마요네즈 베이스 / 감자튀김·나초·피자 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 갈릭디핑소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 찍어 먹을 수 있는 저당 갈릭소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 고소한 갈릭소스 당길 때"},
            {"chunk_type": "question", "text": "일반 갈릭디핑소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 갈릭디핑소스 추천해줘"},
            {"chunk_type": "situation", "text": "감자튀김이나 나초에 곁들이는 디핑 소스로 활용"},
            {"chunk_type": "situation", "text": "피자 찍어 먹는 소스로 저당 갈릭소스 쓸 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 고소한 갈릭 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 갈릭소스 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 갈릭 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "갈릭디핑소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 갈릭디핑소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2.5g 저당 갈릭디핑소스"},
            {"chunk_type": "substitute", "text": "일반 갈릭소스의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 마요네즈 베이스 저당 갈릭디핑소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 마라소스 280g",
        "category": "소스류",
        "calories_per_100g": 100,
        "price_range": "280g 1개 3,780원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 마라소스 / 소스류 마라 / 100kcal(100g 기준) / 당류 2g / 액상알룰로스·마라유베이스 함유 / 마라탕·마라샹궈 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 마라소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 마라소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 얼얼한 마라 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 마라소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 깔끔한 저당 마라소스 추천해줘"},
            {"chunk_type": "situation", "text": "마라탕 끓일 때 저당 마라소스 활용"},
            {"chunk_type": "situation", "text": "마라샹궈 양념으로 저당 마라소스 쓸 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 얼얼한 마라 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "집에서 전문점 마라 요리 간편하게 만들 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 마라 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "마라소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 마라소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 저당 마라소스"},
            {"chunk_type": "substitute", "text": "일반 마라소스의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 마라유베이스 저당 마라소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저칼로리 비빔장 280g",
        "category": "소스류",
        "calories_per_100g": 35,
        "price_range": "280g 1개 3,910원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저칼로리 비빔장 / 소스류 비빔장 / 35kcal(100g 기준) / 당류 3g / 알룰로스 10.6g / 골뱅이무침·비빔국수·비빔밥 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 비빔장 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저칼로리 비빔장"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤달콤한 비빔장 당길 때"},
            {"chunk_type": "question", "text": "일반 비빔장 대신 먹을 수 있는 저칼로리 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 비빔장 추천해줘"},
            {"chunk_type": "situation", "text": "비빔밥 양념으로 저칼로리 비빔장 활용할 때"},
            {"chunk_type": "situation", "text": "비빔국수에 저칼로리 비빔장 쓸 때"},
            {"chunk_type": "situation", "text": "골뱅이무침에 매콤달콤 비빔장 활용"},
            {"chunk_type": "situation", "text": "다이어트 식단에 매콤달콤한 포인트 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 비빔장 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "비빔장 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 비빔장 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "35kcal 저칼로리 비빔장"},
            {"chunk_type": "substitute", "text": "일반 비빔장의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 매콤달콤 비빔장"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 초고추장소스 310g",
        "category": "소스류",
        "calories_per_100g": 65,
        "price_range": "310g 1개 3,980원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 초고추장소스 / 소스류 초고추장 / 65kcal(100g 기준) / 당류 2.6g / 알룰로스 20.9g / 알룰로스 31%·발효식초 10%·고추장 5%·사과식초 4.99% / 회·숙회·비빔밥 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 초고추장소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 찍어 먹을 수 있는 저당 초고추장"},
            {"chunk_type": "question", "text": "다이어트 중인데 새콤달콤 매콤한 초고추장 당길 때"},
            {"chunk_type": "question", "text": "일반 초고추장 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 초고추장소스 추천해줘"},
            {"chunk_type": "situation", "text": "숙회나 생선회 먹을 때 저당 초고추장 곁들일 때"},
            {"chunk_type": "situation", "text": "비빔밥 양념으로 새콤달콤 초고추장 활용"},
            {"chunk_type": "situation", "text": "미역무침 등 무침 요리에 저당 초고추장 활용"},
            {"chunk_type": "situation", "text": "다이어트 식단에 새콤달콤한 포인트 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 초고추장 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "초고추장 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 초고추장 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2.6g 저당 초고추장소스"},
            {"chunk_type": "substitute", "text": "일반 초고추장의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 발효식초 저당 새콤달콤 초고추장"},
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
