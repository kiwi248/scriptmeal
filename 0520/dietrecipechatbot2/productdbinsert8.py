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
        "product_name": "비비드키친 저칼로리 스위트칠리소스",
        "category": "소스류",
        "calories_per_100g": 30,
        "price_range": "280g 1개 3,210원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저칼로리 스위트칠리소스 / 소스류 스위트칠리 / 30kcal(100g 기준) / 당류 2g / 액상알룰로스 10.7g / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 스위트칠리소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 스위트칠리소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤달콤한 칠리소스 당길 때"},
            {"chunk_type": "question", "text": "일반 스위트칠리소스 대신 먹을 수 있는 저칼로리 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 스위트칠리소스 추천해줘"},
            {"chunk_type": "situation", "text": "튀김 요리에 곁들일 매콤달콤한 소스"},
            {"chunk_type": "situation", "text": "다이어트 식단에 포인트 소스 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "치킨이나 새우튀김에 디핑 소스로 활용할 때"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살에 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 칠리소스 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "스위트칠리소스 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 스위트칠리소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "30kcal 저칼로리 스위트칠리소스"},
            {"chunk_type": "substitute", "text": "일반 스위트칠리소스의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 매콤달콤 소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 굴소스",
        "category": "소스류",
        "calories_per_100g": 35,
        "price_range": "310g 1개 5,090원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 굴소스 / 소스류 굴소스 / 35kcal(100g 기준) / 당류 0.5g / 굴농축액·굴추출액 함유 / 액상알룰로스 사용 / HACCP 인증"},
            {"chunk_type": "question", "text": "당 적은 굴소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 굴소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 볶음 요리에 굴소스 쓰고 싶어"},
            {"chunk_type": "question", "text": "일반 굴소스 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "감칠맛 살아있는 저당 굴소스 추천해줘"},
            {"chunk_type": "situation", "text": "볶음 요리에 감칠맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 깊은 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 굴소스 활용"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살 볶음에 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 굴소스 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "굴소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 굴소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 0.5g 저당 굴소스"},
            {"chunk_type": "substitute", "text": "일반 굴소스의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 굴농축액 저당 굴소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 참깨소이 드레싱",
        "category": "소스류",
        "calories_per_100g": 200,
        "price_range": "200g 1개 3,500원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 참깨소이 드레싱 / 소스류 드레싱 / 200kcal(100g 기준) / 당류 1g 미만 / 액상알룰로스 13% / 참깨 3%(참깨100%) / HACCP 인증"},
            {"chunk_type": "question", "text": "당 적은 참깨 드레싱 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저당 참깨소이 드레싱"},
            {"chunk_type": "question", "text": "다이어트 중인데 고소한 참깨 드레싱 당길 때"},
            {"chunk_type": "question", "text": "일반 참깨소이 드레싱 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 참깨소이 드레싱 추천해줘"},
            {"chunk_type": "situation", "text": "샐러드에 고소하게 뿌려 먹을 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 깊은 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 드레싱 활용"},
            {"chunk_type": "situation", "text": "운동 후 샐러드에 곁들일 고소한 드레싱"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 참깨소이 풍미 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "참깨소이 드레싱 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 참깨 드레싱 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 1g 미만 참깨소이 드레싱"},
            {"chunk_type": "substitute", "text": "일반 참깨 드레싱의 저당 대체품"},
            {"chunk_type": "substitute", "text": "알룰로스 참깨 저당 소이 드레싱"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저칼로리 숯불매콤소스",
        "category": "소스류",
        "calories_per_100g": 35,
        "price_range": "290g 1개 3,880원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저칼로리 숯불매콤소스 / 소스류 매콤소스 / 35kcal(100g 기준) / 당류 1g 미만 / 액상알룰로스 11.8g / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 숯불매콤소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 매콤한 소스"},
            {"chunk_type": "question", "text": "다이어트 중인데 그윽한 숯불 향 매콤소스 당길 때"},
            {"chunk_type": "question", "text": "일반 매콤소스 대신 먹을 수 있는 저칼로리 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 숯불매콤소스 추천해줘"},
            {"chunk_type": "situation", "text": "치킨이나 불고기 요리에 활용할 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 매콤한 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 소스 활용"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살에 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 숯불 매콤한 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "숯불매콤소스 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 매콤소스 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "35kcal 저칼로리 숯불매콤소스"},
            {"chunk_type": "substitute", "text": "일반 매콤소스의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 숯불 매콤 소스"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저칼로리 토마토 케첩",
        "category": "소스류",
        "calories_per_100g": 35,
        "price_range": "280g 1개 3,510원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저칼로리 토마토 케첩 / 소스류 케첩 / 35kcal(100g 기준) / 당류 5g / 정제수 토마토페이스트(중국산) / 알룰로스 사용 / HACCP 인증"},
            {"chunk_type": "question", "text": "저칼로리 토마토 케첩 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 저칼로리 케첩"},
            {"chunk_type": "question", "text": "다이어트 중인데 케첩 당길 때"},
            {"chunk_type": "question", "text": "일반 케첩 대신 먹을 수 있는 저칼로리 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저칼로리 토마토 케첩 추천해줘"},
            {"chunk_type": "situation", "text": "튀김이나 오므라이스에 케첩 뿌릴 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 새콤한 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 케첩 활용"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살 요리에 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 케첩 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "토마토 케첩 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 케첩 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "35kcal 저칼로리 토마토 케첩"},
            {"chunk_type": "substitute", "text": "일반 케첩의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "알룰로스 액상 저당 토마토 케첩"},
        ]
    },
    {
        "brand": "비비드키친",
        "product_name": "비비드키친 저당 쌈장소스",
        "category": "소스류",
        "calories_per_100g": 75,
        "price_range": "300g 1개 4,380원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "비비드키친 저당 쌈장소스 / 소스류 쌈장 / 75kcal(100g 기준) / 당류 2g / 액상알룰로스 12.78g / 된장 함유 / HACCP 인증"},
            {"chunk_type": "question", "text": "당 적은 쌈장소스 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 쓸 수 있는 저당 쌈장"},
            {"chunk_type": "question", "text": "다이어트 중인데 고기 쌈 먹을 때 쌈장 쓰고 싶어"},
            {"chunk_type": "question", "text": "일반 쌈장 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "알룰로스로 만든 저당 쌈장소스 추천해줘"},
            {"chunk_type": "situation", "text": "삼겹살·보쌈에 죄책감 없이 쌈장 올릴 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 깊고 진한 된장 풍미 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 쌈장 활용"},
            {"chunk_type": "situation", "text": "운동 후 단백질 식사에 쌈장 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 한식 쌈 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "쌈장소스 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 쌈장 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 저당 쌈장소스"},
            {"chunk_type": "substitute", "text": "일반 쌈장의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "알룰로스 된장 저당 쌈장소스"},
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
