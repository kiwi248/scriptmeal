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
        "product_name": "비비드키친 저당 돈까스소스 285g",
        "category": "소스류",
        "calories_per_100g": 30,
        "price_range": "285g 1개 3,320원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 돈까스소스 / 소스류 돈까스소스 / 30kcal(100g 기준) / 당류 4g / 알룰로스 11.18g / 액상알룰로스·사과농축과즙액 함유 / 돈까스·튀김 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 돈까스소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저당 돈까스소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 달콤한 돈까스소스 당길 때"},
            {"chunk_type": "question", "text": "일반 돈까스소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 돈까스소스 추천해줘"},
            {"chunk_type": "situation", "text": "돈까스에 저당 소스 곁들일 때"},
            {"chunk_type": "situation", "text": "튀김 요리에 새콤달콤한 저당 소스 활용"},
            {"chunk_type": "situation", "text": "다이어트 식단에 돈까스 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 돈까스소스 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 돈까스소스 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "돈까스소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 돈까스소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "30kcal 저당 돈까스소스"},
            {"chunk_type": "substitute", "text": "일반 돈까스소스의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 사과농축과즙 저당 새콤달콤 돈까스소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 홀스래디쉬소스 265g",
        "category": "소스류",
        "calories_per_100g": 300,
        "price_range": "265g 1개 4,230원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 홀스래디쉬소스 / 소스류 홀스래디쉬 / 300kcal(100g 기준) / 당류 2g / 알룰로스 8.09g / 마요네즈 베이스 / 연어·튀김 요리 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 홀스래디쉬소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 찍어 먹을 수 있는 저당 홀스래디쉬"},
            {"chunk_type": "question", "text": "다이어트 중인데 알싸한 홀스래디쉬 소스 당길 때"},
            {"chunk_type": "question", "text": "일반 홀스래디쉬소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 홀스래디쉬소스 추천해줘"},
            {"chunk_type": "situation", "text": "연어에 곁들이는 드레싱으로 저당 홀스래디쉬 활용"},
            {"chunk_type": "situation", "text": "튀김 요리에 디핑 소스로 저당 홀스래디쉬 쓸 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 알싸한 홀스래디쉬 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 홀스래디쉬소스 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 홀스래디쉬 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "홀스래디쉬소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 홀스래디쉬소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 저당 홀스래디쉬소스"},
            {"chunk_type": "substitute", "text": "일반 홀스래디쉬소스의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 마요네즈 베이스 저당 홀스래디쉬소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 발사믹 드레싱 210g",
        "category": "드레싱류",
        "calories_per_100g": 45,
        "price_range": "210g 1개 3,500원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 발사믹 드레싱 / 드레싱류 발사믹 / 45kcal(100g 기준) / 당류 4g / 알룰로스 3.1g / 발효식초 20%·액상알룰로스 함유 / 오레가노·바질·마늘후레이크 사용 / 샐러드 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 발사믹 드레싱 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저당 발사믹"},
            {"chunk_type": "question", "text": "다이어트 중인데 새콤한 발사믹 드레싱 당길 때"},
            {"chunk_type": "question", "text": "일반 발사믹 드레싱 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 발사믹 드레싱 추천해줘"},
            {"chunk_type": "situation", "text": "샐러드에 저당 발사믹 드레싱 뿌릴 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 산뜻한 발사믹 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 발사믹 드레싱 활용"},
            {"chunk_type": "situation", "text": "운동 후 샐러드에 저당 드레싱으로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 발사믹 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "발사믹 드레싱 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 발사믹 드레싱 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "45kcal 저당 발사믹 드레싱"},
            {"chunk_type": "substitute", "text": "일반 발사믹 드레싱의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 발효식초 오레가노 바질 저당 발사믹 드레싱"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 시저드레싱 205g",
        "category": "드레싱류",
        "calories_per_100g": 240,
        "price_range": "205g 1개 3,500원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 시저드레싱 / 드레싱류 시저 / 240kcal(100g 기준) / 당류 2g / 알룰로스 4.2g / 마요네즈·그레이티드 파마산치즈 함유 / 샐러드·샌드위치·랩 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 시저드레싱 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저당 시저드레싱"},
            {"chunk_type": "question", "text": "다이어트 중인데 고소한 시저드레싱 당길 때"},
            {"chunk_type": "question", "text": "일반 시저드레싱 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 파마산치즈 저당 시저드레싱 추천해줘"},
            {"chunk_type": "situation", "text": "샐러드에 고소한 저당 시저드레싱 뿌릴 때"},
            {"chunk_type": "situation", "text": "샌드위치나 랩 소스로 저당 시저드레싱 쓸 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 고소한 파마산 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 시저드레싱 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 시저드레싱 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "시저드레싱 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 시저드레싱 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 저당 시저드레싱"},
            {"chunk_type": "substitute", "text": "일반 시저드레싱의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 마요네즈 파마산치즈 저당 시저드레싱"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 어니언크림 드레싱 205g",
        "category": "드레싱류",
        "calories_per_100g": 230,
        "price_range": "205g 1개 3,420원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 어니언크림 드레싱 / 드레싱류 어니언크림 / 230kcal(100g 기준) / 당류 3g / 알룰로스 39g / 양파분말·사과퓨레·레몬착즙액 함유 / 샐러드·샤부샤부 디핑소스 활용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저당 어니언크림 드레싱 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저당 어니언크림"},
            {"chunk_type": "question", "text": "다이어트 중인데 달짝지근한 어니언 드레싱 당길 때"},
            {"chunk_type": "question", "text": "일반 어니언크림 드레싱 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 어니언크림 드레싱 추천해줘"},
            {"chunk_type": "situation", "text": "샐러드에 달짝지근한 저당 어니언크림 드레싱 뿌릴 때"},
            {"chunk_type": "situation", "text": "샤부샤부 디핑소스로 저당 어니언크림 활용"},
            {"chunk_type": "situation", "text": "다이어트 식단에 크리미한 어니언 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 어니언크림 드레싱 활용"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 어니언크림 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "어니언크림 드레싱 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 어니언크림 드레싱 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 3g 저당 어니언크림 드레싱"},
            {"chunk_type": "substitute", "text": "일반 어니언드레싱의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 양파분말 사과퓨레 저당 어니언크림 드레싱"},
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
