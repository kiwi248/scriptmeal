import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 제품 + 청크를 함께 묶어서 관리
# calories_per_100g: 소스류, 스프레드류, 음료베이스류
# calories_per_unit: 과자류 (1회 제공량 기준)
products = [
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 저당 쌈장",
        "category": "소스류",
        "calories_per_100g": 95,
        "price_range": "230g 1개 11,740원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 저당 쌈장 / 소스류 쌈장 / 95kcal(100g 기준) / 당류 1g 미만 / 국산콩 100% / 설탕·물엿·밀가루 무첨가 / 글루텐프리"},
            {"chunk_type": "question", "text": "당 적은 쌈장 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 쌈장"},
            {"chunk_type": "question", "text": "다이어트 중인데 고기 쌈 먹을 때 쌈장 쓰고 싶어"},
            {"chunk_type": "question", "text": "일반 쌈장 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "설탕 없이 만든 국산콩 쌈장 추천해줘"},
            {"chunk_type": "situation", "text": "삼겹살·보쌈에 죄책감 없이 쌈장 올릴 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 깊고 진한 된장 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 쌈장 활용"},
            {"chunk_type": "situation", "text": "운동 후 단백질 식사에 쌈장 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 한식 쌈 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "쌈장 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 쌈장 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 1g 미만 저당 쌈장"},
            {"chunk_type": "substitute", "text": "일반 쌈장의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "국산콩 알룰로스 설탕 무첨가 쌈장"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 무가당 땅콩버터 크런치",
        "category": "스프레드류",
        "calories_per_100g": 620,
        "price_range": "250g 1개 9,480원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 무가당 땅콩버터 크런치 / 스프레드류 땅콩버터 / 620kcal(100g 기준) / 당류 6g / 땅콩 100%(아르헨티나산) / 설탕 무첨가"},
            {"chunk_type": "question", "text": "설탕 없는 땅콩버터 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 덜한 땅콩버터 뭐 있어"},
            {"chunk_type": "question", "text": "다이어트 중인데 고소한 땅콩버터 당길 때"},
            {"chunk_type": "question", "text": "일반 땅콩버터 대신 무가당 버전 뭐야"},
            {"chunk_type": "question", "text": "단백질 높은 무가당 땅콩버터 추천해줘"},
            {"chunk_type": "situation", "text": "빵이나 크래커에 죄책감 없이 발라 먹을 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 고소한 지방 보충하고 싶을 때"},
            {"chunk_type": "situation", "text": "운동 후 단백질 보충 간식으로 먹을 때"},
            {"chunk_type": "situation", "text": "오트밀이나 요거트에 토핑으로 올릴 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 고소한 땅콩버터 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "땅콩버터 무가당 버전"},
            {"chunk_type": "substitute", "text": "일반 땅콩버터 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "설탕 없는 크런치 땅콩버터"},
            {"chunk_type": "substitute", "text": "일반 땅콩버터의 무가당 대체품"},
            {"chunk_type": "substitute", "text": "땅콩 100% 설탕 무첨가 스프레드"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 딸기잼",
        "category": "스프레드류",
        "calories_per_100g": 30,
        "price_range": "320g 1개 11,290원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 딸기잼 / 스프레드류 잼 / 30kcal(100g 기준) / 당류 3g / 딸기 50%(국산) / 알룰로스 / 설탕 대신 알룰로스 사용"},
            {"chunk_type": "question", "text": "살 안 찌는 딸기잼 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 발라 먹을 수 있는 저당 잼"},
            {"chunk_type": "question", "text": "다이어트 중인데 달콤한 딸기잼 당길 때"},
            {"chunk_type": "question", "text": "일반 딸기잼 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "설탕 없이 만든 국산 딸기잼 추천해줘"},
            {"chunk_type": "situation", "text": "빵에 죄책감 없이 잼 발라 먹을 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 달콤함 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "요거트나 오트밀 토핑으로 올릴 때"},
            {"chunk_type": "situation", "text": "아침 식사에 가볍게 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 딸기잼 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "딸기잼 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 딸기잼 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "30kcal 저당 딸기잼"},
            {"chunk_type": "substitute", "text": "일반 딸기잼의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "국산 딸기 알룰로스 설탕 무첨가 잼"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 저당 케찹",
        "category": "소스류",
        "calories_per_100g": 39,
        "price_range": "310g 1개 4,870원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 저당 케찹 / 소스류 케찹 / 38.68kcal(100g 기준) / 당류 4.55g / 토마토페이스트 29.5%(토마토 100%) / 알룰로스·스테비아 사용"},
            {"chunk_type": "question", "text": "당 적은 케찹 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저당 케찹"},
            {"chunk_type": "question", "text": "다이어트 중인데 케찹 당길 때"},
            {"chunk_type": "question", "text": "일반 케찹 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "토마토 7개 분량 영양 담긴 저당 케찹 추천해줘"},
            {"chunk_type": "situation", "text": "계란후라이나 감자요리에 케찹 뿌릴 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살 요리에 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 케찹 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 케찹 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "케찹 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 케찹 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "38kcal 저당 케찹"},
            {"chunk_type": "substitute", "text": "일반 케찹의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "토마토 알룰로스 스테비아 설탕 최소화 케찹"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 저당 유자청",
        "category": "소스류",
        "calories_per_100g": 40,
        "price_range": "350g 1개 12,970원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 저당 유자청 / 소스류 유자청 / 40kcal(100g 기준) / 당류 2g / 유자(국산) / 알룰로스·나한과·스테비아 사용 / 한 잔 당 1g"},
            {"chunk_type": "question", "text": "당 적은 유자청 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 마실 수 있는 저당 유자차"},
            {"chunk_type": "question", "text": "다이어트 중인데 따뜻한 유자차 당길 때"},
            {"chunk_type": "question", "text": "일반 유자청 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "설탕 없이 만든 국산 유자청 추천해줘"},
            {"chunk_type": "situation", "text": "따뜻한 유자차 한 잔 마시고 싶을 때"},
            {"chunk_type": "situation", "text": "다이어트 중 달콤한 음료 마시고 싶을 때"},
            {"chunk_type": "situation", "text": "운동 후 상큼하게 마실 음료가 필요할 때"},
            {"chunk_type": "situation", "text": "밤에 따뜻한 차 한 잔 마실 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 유자차 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "유자청 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 유자청 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 저당 유자청"},
            {"chunk_type": "substitute", "text": "일반 유자청의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "국산 유자 알룰로스 나한과 스테비아 유자청"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 밀크초코볼 헤이즐넛",
        "category": "과자류",
        "calories_per_unit": 163,
        "price_range": "150g(30g×5봉) 1개 12,500원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 밀크초코볼 헤이즐넛 / 과자류 초콜릿 / 163kcal(30g 1봉 기준) / 당류 2g / 밀크초코볼 45.8% 헤이즐넛 22.7% / 알룰로스 사용"},
            {"chunk_type": "question", "text": "당 적은 초콜릿 과자 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 초코볼"},
            {"chunk_type": "question", "text": "다이어트 중인데 달콤한 초콜릿 당길 때"},
            {"chunk_type": "question", "text": "일반 초코볼 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 초콜릿 간식 추천해줘"},
            {"chunk_type": "situation", "text": "간식으로 죄책감 없이 초콜릿 먹고 싶을 때"},
            {"chunk_type": "situation", "text": "다이어트 중 달콤한 간식이 필요할 때"},
            {"chunk_type": "situation", "text": "운동 후 작은 초콜릿 간식으로 보상할 때"},
            {"chunk_type": "situation", "text": "야식으로 가볍게 초콜릿 한 봉 먹고 싶을 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 프리미엄 초콜릿 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "초코볼 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 초콜릿 과자 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 밀크초코볼"},
            {"chunk_type": "substitute", "text": "일반 초코볼의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 헤이즐넛 저당 초콜릿 간식"},
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
