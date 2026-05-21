import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 제품 + 청크를 함께 묶어서 관리
# calories_per_100g: 액체류/소스류/스프레드류(잼류 포함)
# calories_per_unit: 고체류/과자류 (1회 제공량 기준)
products = [
    # ── 마이노멀 ──────────────────────────────────────────────────────────────
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 초코잼",
        "category": "스프레드류",
        "calories_per_100g": 210,
        "price_range": "280g 1개 10,350원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 초코잼 / 스프레드류 초코잼 / 210kcal(100g 기준) / 당류 3.3g / 1회 제공량 20g당 42kcal / 알룰로스·나한과·스테비아 사용 / 코코아분말 9.3%"},
            {"chunk_type": "question", "text": "당 적은 초코잼 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 발라 먹을 수 있는 초콜릿 스프레드"},
            {"chunk_type": "question", "text": "다이어트 중인데 진한 초코 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 초코잼 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "설탕 없이 만든 프리미엄 초코잼 추천해줘"},
            {"chunk_type": "situation", "text": "빵에 죄책감 없이 초코잼 발라 먹을 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 달콤한 초콜릿 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "요거트나 오트밀 토핑으로 올릴 때"},
            {"chunk_type": "situation", "text": "운동 후 달콤한 간식 대신 초코잼 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 초콜릿 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "초코잼 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 초코잼 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "42kcal 저당 초코 스프레드"},
            {"chunk_type": "substitute", "text": "일반 초코잼의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 헤이즐넛 코코아 저당 초코잼"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 블루베리잼",
        "category": "스프레드류",
        "calories_per_100g": 30,
        "price_range": "320g 1개 11,680원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 블루베리잼 / 스프레드류 잼 / 30kcal(100g 기준) / 당류 4.8g / 야생블루베리(캐나다산) 55% / 알룰로스 사용 / 설탕 무첨가"},
            {"chunk_type": "question", "text": "살 안 찌는 블루베리잼 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 발라 먹을 수 있는 저당 잼"},
            {"chunk_type": "question", "text": "다이어트 중인데 달콤한 블루베리잼 당길 때"},
            {"chunk_type": "question", "text": "일반 블루베리잼 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "설탕 없이 만든 야생 블루베리잼 추천해줘"},
            {"chunk_type": "situation", "text": "빵에 죄책감 없이 잼 발라 먹을 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 달콤함 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "요거트나 오트밀 토핑으로 올릴 때"},
            {"chunk_type": "situation", "text": "아침 식사에 가볍게 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 블루베리잼 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "블루베리잼 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 블루베리잼 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "30kcal 저당 블루베리잼"},
            {"chunk_type": "substitute", "text": "일반 블루베리잼의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "야생 블루베리 알룰로스 설탕 무첨가 잼"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 다크초코볼 아몬드",
        "category": "과자류",
        "calories_per_unit": 141,
        "price_range": "150g(30g×5봉) 1개 12,500원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 다크초코볼 아몬드 / 과자류 초콜릿 / 141kcal(30g 1봉 기준) / 당류 1g / 초콜릿 65.5% 아몬드 32.7% / 알룰로스 사용"},
            {"chunk_type": "question", "text": "당 적은 다크초콜릿 과자 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 아몬드 초코볼"},
            {"chunk_type": "question", "text": "다이어트 중인데 쌉싸름한 다크초콜릿 당길 때"},
            {"chunk_type": "question", "text": "일반 초코볼 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 다크초콜릿 간식 추천해줘"},
            {"chunk_type": "situation", "text": "간식으로 죄책감 없이 다크초콜릿 먹고 싶을 때"},
            {"chunk_type": "situation", "text": "다이어트 중 달콤 쌉싸름한 간식이 필요할 때"},
            {"chunk_type": "situation", "text": "운동 후 작은 초콜릿 간식으로 보상할 때"},
            {"chunk_type": "situation", "text": "야식으로 가볍게 초콜릿 한 봉 먹고 싶을 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 프리미엄 다크초콜릿 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "다크초코볼 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 다크초콜릿 과자 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 1g 다크초코볼 아몬드"},
            {"chunk_type": "substitute", "text": "일반 다크초코볼의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 아몬드 저당 다크초콜릿 간식"},
        ]
    },

    # ── 비비드키친 ────────────────────────────────────────────────────────────
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 치폴레소스",
        "category": "소스류",
        "calories_per_100g": 300,
        "price_range": "265g 1개 4,490원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 치폴레소스 / 소스류 치폴레소스 / 300kcal(100g 기준) / 당류 3g / 액상알룰로스 11% / 치폴레페퍼 2.25% / HACCP 인증"},
            {"chunk_type": "question", "text": "당 적은 치폴레소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저당 치폴레소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤하고 고소한 소스 당길 때"},
            {"chunk_type": "question", "text": "일반 치폴레소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 치폴레소스 추천해줘"},
            {"chunk_type": "situation", "text": "샌드위치에 매콤한 소스로 활용할 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 디핑 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살 요리에 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 소스 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 치폴레 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "치폴레소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 치폴레소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 3g 저당 치폴레소스"},
            {"chunk_type": "substitute", "text": "일반 치폴레소스의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 매콤 소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저칼로리 머스타드 소스",
        "category": "소스류",
        "calories_per_100g": 33,
        "price_range": "280g 1개 3,210원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저칼로리 머스타드 소스 / 소스류 머스타드 / 33kcal(100g 기준) / 당류 0.6g / 겨자씨 4.7% / 액상알룰로스 사용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 머스타드 소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 머스타드"},
            {"chunk_type": "question", "text": "다이어트 중인데 새콤달콤한 머스타드 당길 때"},
            {"chunk_type": "question", "text": "일반 머스타드 대신 먹을 수 있는 저칼로리 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 머스타드 소스 추천해줘"},
            {"chunk_type": "situation", "text": "튀김 요리에 곁들일 머스타드 소스"},
            {"chunk_type": "situation", "text": "다이어트 식단에 깔끔한 소스 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "샌드위치나 핫도그에 저칼로리 머스타드"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살에 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 머스타드 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "머스타드 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 머스타드 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "33kcal 저칼로리 머스타드 소스"},
            {"chunk_type": "substitute", "text": "일반 머스타드의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 머스타드"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 오리엔탈 드레싱",
        "category": "소스류",
        "calories_per_100g": 180,
        "price_range": "210g 1개 3,500원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 오리엔탈 드레싱 / 소스류 드레싱 / 180kcal(100g 기준) / 당류 3g / 액상알룰로스 10% / 올리브유 함유 / HACCP 인증"},
            {"chunk_type": "question", "text": "당 적은 오리엔탈 드레싱 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저당 드레싱"},
            {"chunk_type": "question", "text": "다이어트 중인데 새콤달콤한 오리엔탈 드레싱 당길 때"},
            {"chunk_type": "question", "text": "일반 오리엔탈 드레싱 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 오리엔탈 드레싱 추천해줘"},
            {"chunk_type": "situation", "text": "샐러드에 감칠맛 드레싱 뿌려 먹을 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 깊은 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 오리엔탈 드레싱 활용"},
            {"chunk_type": "situation", "text": "운동 후 샐러드에 곁들일 담백한 드레싱"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 오리엔탈 풍미 드레싱 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "오리엔탈 드레싱 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 오리엔탈 드레싱 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 3g 저당 오리엔탈 드레싱"},
            {"chunk_type": "substitute", "text": "일반 오리엔탈 드레싱의 저당 대체품"},
            {"chunk_type": "substitute", "text": "알룰로스 올리브유 저당 오리엔탈 드레싱"},
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
