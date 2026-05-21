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
        "brand": "고맙당",
        "product_name": "고맙당 저당 핫불닭소스 180g",
        "category": "소스류",
        "calories_per_100g": 147,
        "price_range": "180g 1개 9,700원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "고맙당 저당 핫불닭소스 / 소스류 핫불닭 / 147kcal(100g 기준) / 당류 2g / 알룰로스 35g / 치킨베이스(닭고기:국산) 0.07% / 국산 품 간장·국산 다진마늘 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 핫불닭소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 핫불닭소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 엄청 맵고 얼얼한 불닭 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 핫불닭소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 초매운 불닭소스 추천해줘"},
            {"chunk_type": "situation", "text": "매운 불닭 요리에 저당 소스로 활용할 때"},
            {"chunk_type": "situation", "text": "다이어트 중에 극강의 매운맛 당길 때"},
            {"chunk_type": "situation", "text": "닭가슴살 요리에 핫불닭소스로 매운맛 더할 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 핫불닭소스 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 극매운 불닭 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "핫불닭소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 핫불닭소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 저당 핫불닭소스"},
            {"chunk_type": "substitute", "text": "일반 핫불닭소스의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 국산닭 저당 초매운 핫불닭소스"},
        ]
    },
    {
        "brand": "고맙당",
        "product_name": "고맙당 저당 불닭소스 180g",
        "category": "소스류",
        "calories_per_100g": 147,
        "price_range": "180g 1개 9,700원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "고맙당 저당 불닭소스 / 소스류 불닭 / 147kcal(100g 기준) / 당류 2g / 알룰로스 36g / 치킨베이스(닭고기:국산) 0.07% / 국산 품 간장·국산 다진마늘 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 불닭소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 불닭소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤한 불닭 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 불닭소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 불닭소스 추천해줘"},
            {"chunk_type": "situation", "text": "불닭 요리에 저당 소스로 활용할 때"},
            {"chunk_type": "situation", "text": "다이어트 중에 매운맛 당길 때"},
            {"chunk_type": "situation", "text": "닭가슴살 요리에 불닭소스로 매운맛 더할 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 불닭소스 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 불닭 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "불닭소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 불닭소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 저당 불닭소스"},
            {"chunk_type": "substitute", "text": "일반 불닭소스의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 국산닭 저당 매콤 불닭소스"},
        ]
    },
    {
        "brand": "샘표",
        "product_name": "샘표 저당 제육볶음 양념 440g",
        "category": "양념류",
        "calories_per_100g": 85,
        "price_range": "440g 1개 5,070원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "샘표 저당 제육볶음 양념 / 양념류 제육볶음 / 85kcal(100g 기준) / 당류 1.7g / 알룰로스 11g / 당류 94% 감소 / 고춧가루·생강농축액·흑후추분말 함유 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 제육볶음 양념 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 제육볶음 양념"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤한 제육볶음 당길 때"},
            {"chunk_type": "question", "text": "일반 제육볶음 양념 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 제육볶음 양념 추천해줘"},
            {"chunk_type": "situation", "text": "집에서 간편하게 저당 제육볶음 만들 때"},
            {"chunk_type": "situation", "text": "돼지고기 볶음 요리에 저당 양념 활용"},
            {"chunk_type": "situation", "text": "다이어트 식단에 매콤한 제육볶음 즐기고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 제육볶음 양념으로 요리"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 제육볶음 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "제육볶음 양념 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 제육볶음 양념 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 1.7g 저당 제육볶음 양념"},
            {"chunk_type": "substitute", "text": "당류 94% 감소 저당 제육볶음 양념"},
            {"chunk_type": "substitute", "text": "알룰로스 고춧가루 저당 매콤 제육볶음 양념"},
        ]
    },
    {
        "brand": "샘표",
        "product_name": "샘표 저당 불고기 양념 430g",
        "category": "양념류",
        "calories_per_100g": 50,
        "price_range": "430g 1개 5,340원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "샘표 저당 불고기 양념 / 양념류 불고기 / 50kcal(100g 기준) / 당류 0.7g / 알룰로스 5.3g / 당류 97% 감소 / 진발효간장·다진마늘·다진생강·수크랄로스 함유 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 불고기 양념 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 불고기 양념"},
            {"chunk_type": "question", "text": "다이어트 중인데 달콤짭조름한 불고기 당길 때"},
            {"chunk_type": "question", "text": "일반 불고기 양념 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 불고기 양념 추천해줘"},
            {"chunk_type": "situation", "text": "집에서 간편하게 저당 불고기 만들 때"},
            {"chunk_type": "situation", "text": "소고기 볶음 요리에 저당 불고기 양념 활용"},
            {"chunk_type": "situation", "text": "다이어트 식단에 달콤짭조름한 불고기 즐기고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 불고기 양념으로 요리"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 불고기 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "불고기 양념 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 불고기 양념 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 0.7g 저당 불고기 양념"},
            {"chunk_type": "substitute", "text": "당류 97% 감소 저당 불고기 양념"},
            {"chunk_type": "substitute", "text": "알룰로스 진발효간장 저당 달콤짭조름 불고기 양념"},
        ]
    },
    {
        "brand": "곰곰",
        # 1세트 = 180g × 8개 / 가격 7,190원 → 1개당 약 899원
        "product_name": "곰곰 떡볶이모양 곤약 180g",
        "category": "곤약류",
        "calories_per_unit": 22,   # 1개(180g) 기준 22kcal
        "price_range": "180g 1개 899원 (8개 세트 7,190원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "곰곰 떡볶이모양 곤약 / 곤약류 / 22kcal(1개 180g 기준) / 당류 0g / 곤약분말 3.4% / 떡볶이 모양 곤약 / 저칼로리 다이어트 식품 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 떡볶이 대체 식품 찾고 있어"},
            {"chunk_type": "question", "text": "다이어트 중인데 떡볶이 먹고 싶어"},
            {"chunk_type": "question", "text": "살 안 찌는 떡볶이 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "칼로리 거의 없는 떡볶이 모양 식품 추천해줘"},
            {"chunk_type": "question", "text": "곤약으로 만든 떡볶이 대체 식품 뭐야"},
            {"chunk_type": "situation", "text": "저당 떡볶이양념과 함께 저칼로리 떡볶이 만들 때"},
            {"chunk_type": "situation", "text": "다이어트 중 떡볶이 대신 먹을 것 찾을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 곤약으로 요리"},
            {"chunk_type": "situation", "text": "운동 후 간식으로 저칼로리 떡볶이 모양 곤약"},
            {"chunk_type": "situation", "text": "칼로리 신경 쓰면서도 쫄깃한 식감 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "떡볶이 저칼로리 대체 식품"},
            {"chunk_type": "substitute", "text": "떡볶이떡 곤약 대체품"},
            {"chunk_type": "substitute", "text": "22kcal 떡볶이모양 곤약"},
            {"chunk_type": "substitute", "text": "다이어트 떡볶이 재료"},
            {"chunk_type": "substitute", "text": "곤약분말 떡볶이 모양 저칼로리 식품"},
        ]
    },
    {
        "brand": "곰곰",
        # 1박스 = 180g × 8개 / 가격 7,200원 → 1개당 900원
        "product_name": "곰곰 우동모양 곤약",
        "category": "곤약류",
        "calories_per_unit": 22,   # 1개(180g) 기준 22kcal
        "price_range": "180g 1개 900원 (8개 박스 7,200원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "곰곰 우동모양 곤약 / 곤약류 / 22kcal(1개 180g 기준) / 당류 0g / 곤약분말 3.4% / 우동 모양 곤약 / 저칼로리 다이어트 식품 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 우동 대체 식품 찾고 있어"},
            {"chunk_type": "question", "text": "다이어트 중인데 우동 먹고 싶어"},
            {"chunk_type": "question", "text": "살 안 찌는 우동면 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "칼로리 거의 없는 우동 모양 식품 추천해줘"},
            {"chunk_type": "question", "text": "곤약으로 만든 우동 대체 식품 뭐야"},
            {"chunk_type": "situation", "text": "우동 육수에 저칼로리 곤약 우동면 대신 넣을 때"},
            {"chunk_type": "situation", "text": "다이어트 중 우동 대신 먹을 것 찾을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 곤약으로 요리"},
            {"chunk_type": "situation", "text": "운동 후 간식으로 저칼로리 우동 모양 곤약"},
            {"chunk_type": "situation", "text": "칼로리 신경 쓰면서도 쫄깃한 우동 식감 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "우동면 저칼로리 대체 식품"},
            {"chunk_type": "substitute", "text": "우동면 곤약 대체품"},
            {"chunk_type": "substitute", "text": "22kcal 우동모양 곤약"},
            {"chunk_type": "substitute", "text": "다이어트 우동 재료"},
            {"chunk_type": "substitute", "text": "곤약분말 우동 모양 저칼로리 식품"},
        ]
    },
    {
        "brand": "곰곰",
        # 1개 = 200g × 10개 / 가격 11,610원 → 1개당 1,161원
        "product_name": "곰곰 밥알모양 곤약",
        "category": "곤약류",
        "calories_per_unit": 26,   # 1개(200g) 기준 26kcal
        "price_range": "200g 1개 1,161원 (10개 세트 11,610원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "곰곰 밥알모양 곤약 / 곤약류 / 26kcal(1개 200g 기준) / 당류 0g / 곤약분말 4.5% / 밥알 모양 곤약 / 흰쌀과 5:5 혼합 추천 / 저칼로리 다이어트 식품 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 밥 대체 식품 찾고 있어"},
            {"chunk_type": "question", "text": "다이어트 중인데 밥 먹고 싶어"},
            {"chunk_type": "question", "text": "살 안 찌는 밥 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "칼로리 줄이면서 밥 양 늘릴 수 있는 식품 추천해줘"},
            {"chunk_type": "question", "text": "곤약으로 만든 밥 대체 식품 뭐야"},
            {"chunk_type": "situation", "text": "흰쌀밥에 섞어 칼로리 줄이고 싶을 때"},
            {"chunk_type": "situation", "text": "다이어트 중 밥 대신 먹을 것 찾을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 곤약밥으로 요리"},
            {"chunk_type": "situation", "text": "운동 후 식사로 저칼로리 곤약밥 활용"},
            {"chunk_type": "situation", "text": "칼로리 신경 쓰면서도 밥 포만감 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "밥 저칼로리 대체 식품"},
            {"chunk_type": "substitute", "text": "쌀밥 곤약 대체품"},
            {"chunk_type": "substitute", "text": "26kcal 밥알모양 곤약"},
            {"chunk_type": "substitute", "text": "다이어트 밥 재료"},
            {"chunk_type": "substitute", "text": "곤약분말 밥알 모양 저칼로리 식품"},
        ]
    },
    {
        "brand": "곰곰",
        # 1개 = 150g × 8개 / 가격 6,600원 → 1개당 825원
        "product_name": "곰곰 병아리콩 곤약 누들",
        "category": "곤약류",
        "calories_per_unit": 20,   # 1개(150g) 기준 20kcal
        "price_range": "150g 1개 825원 (8개 세트 6,600원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "곰곰 병아리콩 곤약 누들 / 곤약류 / 20kcal(1개 150g 기준) / 당류 0g / 곤약분말 3.09%·병아리콩가루 1.69% / 고소한 맛·곤약 잡내 제거 / 저칼로리 다이어트 식품 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 면 대체 식품 찾고 있어"},
            {"chunk_type": "question", "text": "다이어트 중인데 국수나 면 먹고 싶어"},
            {"chunk_type": "question", "text": "살 안 찌는 면 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "칼로리 거의 없는 고소한 곤약 누들 추천해줘"},
            {"chunk_type": "question", "text": "병아리콩 넣은 저칼로리 곤약면 뭐야"},
            {"chunk_type": "situation", "text": "다이어트 중 면 요리 대신 저칼로리 곤약 누들 활용"},
            {"chunk_type": "situation", "text": "냉면이나 잔치국수 대신 곤약 누들로 요리할 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 곤약 누들로 요리"},
            {"chunk_type": "situation", "text": "운동 후 간식으로 저칼로리 곤약 누들"},
            {"chunk_type": "situation", "text": "칼로리 신경 쓰면서도 고소한 면 식감 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "면류 저칼로리 대체 식품"},
            {"chunk_type": "substitute", "text": "국수·라면 곤약 대체품"},
            {"chunk_type": "substitute", "text": "20kcal 병아리콩 곤약 누들"},
            {"chunk_type": "substitute", "text": "다이어트 면 재료"},
            {"chunk_type": "substitute", "text": "병아리콩가루 곤약분말 저칼로리 고소한 누들"},
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
