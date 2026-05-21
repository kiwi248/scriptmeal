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
        "product_name": "비비드키친 저당 양파절임소스 220g",
        "category": "소스류",
        "calories_per_100g": 11,
        "price_range": "220g 1개 2,290원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 양파절임소스 / 소스류 절임소스 / 11kcal(100g 기준) / 당류 0.5g / 액상알룰로스 함유 / 양파절임·장아찌·파채무침 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 양파절임소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 양파절임소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 짭조름한 양파절임 당길 때"},
            {"chunk_type": "question", "text": "일반 양파절임소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 양파절임소스 추천해줘"},
            {"chunk_type": "situation", "text": "양파절임이나 장아찌 만들 때 저당 소스 활용"},
            {"chunk_type": "situation", "text": "파채무침에 저당 양파절임소스 쓸 때"},
            {"chunk_type": "situation", "text": "기름진 음식 먹을 때 양파절임 곁들일 때"},
            {"chunk_type": "situation", "text": "다이어트 반찬으로 저당 양파절임 만들 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 짭조름한 절임 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "양파절임소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 양파절임소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "11kcal 저당 양파절임소스"},
            {"chunk_type": "substitute", "text": "일반 양파절임소스의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 사과농축과즙 저당 양파절임소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 짜장소스 300g",
        "category": "소스류",
        "calories_per_100g": 90,
        "price_range": "300g 1개 3,910원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 짜장소스 / 소스류 짜장 / 90kcal(100g 기준) / 당류 3g / 액상알룰로스·춘장 함유 / 짜장면·짜장떡볶이 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 짜장소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 짜장소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 달콤한 짜장 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 짜장소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 짜장소스 추천해줘"},
            {"chunk_type": "situation", "text": "짜장면 만들 때 저당 짜장소스 활용"},
            {"chunk_type": "situation", "text": "짜장떡볶이 양념으로 저당 짜장소스 쓸 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 진한 짜장 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 짜장소스로 요리"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 짜장 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "짜장소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 짜장소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 3g 저당 짜장소스"},
            {"chunk_type": "substitute", "text": "일반 짜장소스의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 춘장 저당 달콤한 짜장소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 떡볶이양념 100g",
        "category": "양념류",
        "calories_per_unit": 55,
        "price_range": "100g 2개 4,560원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 떡볶이양념 / 양념류 떡볶이 / 55kcal(1회 제공량 100g 기준) / 당류 2.3g / 알룰로스 20.2g / 파우치 1회분 / 멸치육수·떡·어묵 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 떡볶이양념 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 떡볶이양념"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤달콤한 떡볶이 당길 때"},
            {"chunk_type": "question", "text": "일반 떡볶이양념 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 떡볶이양념 추천해줘"},
            {"chunk_type": "situation", "text": "집에서 간편하게 저당 떡볶이 만들 때"},
            {"chunk_type": "situation", "text": "1회분 파우치로 혼밥 떡볶이 요리할 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 매콤달콤한 떡볶이 즐기고 싶을 때"},
            {"chunk_type": "situation", "text": "멸치육수에 떡·어묵 넣고 저당 양념으로 조리할 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 떡볶이 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "떡볶이양념 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 떡볶이양념 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2.3g 저당 떡볶이양념"},
            {"chunk_type": "substitute", "text": "일반 떡볶이양념의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 저당 매콤달콤 떡볶이양념 파우치"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 참깨드레싱 235g",
        "category": "드레싱류",
        "calories_per_100g": 235,
        "price_range": "235g 1개 4,890원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 참깨드레싱 / 드레싱류 참깨 / 235kcal(100g 기준) / 당류 0.5g / 알룰로스 121g / 새콤달콤 짭잘한 맛 / 샐러드 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 참깨드레싱 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저당 참깨드레싱"},
            {"chunk_type": "question", "text": "다이어트 중인데 고소한 참깨드레싱 당길 때"},
            {"chunk_type": "question", "text": "일반 참깨드레싱 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 참깨드레싱 추천해줘"},
            {"chunk_type": "situation", "text": "샐러드에 고소한 저당 참깨드레싱 뿌릴 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 새콤달콤 짭잘한 참깨 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 참깨드레싱 활용"},
            {"chunk_type": "situation", "text": "운동 후 샐러드에 저당 참깨드레싱 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 참깨드레싱 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "참깨드레싱 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 참깨드레싱 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 0.5g 저당 참깨드레싱"},
            {"chunk_type": "substitute", "text": "일반 참깨드레싱의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 저당 새콤달콤 짭잘한 참깨드레싱"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 초코시럽 380g",
        "category": "시럽류",
        "calories_per_100g": 55,
        "price_range": "380g 1개 6,210원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 초코시럽 / 시럽류 초코 / 55kcal(100g 기준) / 당류 2g / 알룰로스 51g·에리스리톨 5g / 코코아파우더·코코아버터 함유 / 아이스크림·디저트 토핑 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 초코시럽 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저당 초코시럽"},
            {"chunk_type": "question", "text": "다이어트 중인데 진한 초콜릿 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 초코시럽 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 초코시럽 추천해줘"},
            {"chunk_type": "situation", "text": "아이스크림에 저당 초코시럽 뿌릴 때"},
            {"chunk_type": "situation", "text": "디저트 토핑으로 저당 초코시럽 활용"},
            {"chunk_type": "situation", "text": "다이어트 중에 달콤한 초콜릿 맛 죄책감 없이 즐기고 싶을 때"},
            {"chunk_type": "situation", "text": "커피나 음료에 저당 초코시럽 첨가할 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 진한 초콜릿 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "초코시럽 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 초코시럽 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 저당 초코시럽"},
            {"chunk_type": "substitute", "text": "일반 초코시럽의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 에리스리톨 코코아 저당 초코시럽"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 제육볶음양념 250g",
        "category": "양념류",
        "calories_per_100g": 55,
        "price_range": "250g 2개 8,010원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 제육볶음양념 / 양념류 제육볶음 / 55kcal(100g 기준) / 당류 3g / 알룰로스 26.9g·액상알룰로스 40% 함유 / 사과퓨레·양파 자연 단맛 / 제육볶음·돼지고기 볶음 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 제육볶음양념 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 제육볶음양념"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤한 제육볶음 당길 때"},
            {"chunk_type": "question", "text": "일반 제육볶음양념 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 제육볶음양념 추천해줘"},
            {"chunk_type": "situation", "text": "집에서 간편하게 저당 제육볶음 만들 때"},
            {"chunk_type": "situation", "text": "돼지고기 볶음 요리에 저당 양념 활용"},
            {"chunk_type": "situation", "text": "다이어트 식단에 매콤한 제육볶음 즐기고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 제육볶음양념으로 요리"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 제육볶음 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "제육볶음양념 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 제육볶음양념 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 3g 저당 제육볶음양념"},
            {"chunk_type": "substitute", "text": "일반 제육볶음양념의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 사과퓨레 양파 저당 매콤 제육볶음양념"},
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
