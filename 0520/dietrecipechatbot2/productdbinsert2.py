import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 제품 + 청크를 함께 묶어서 관리
products = [
    # {
    #     "brand": "농심",
    #     "product_name": "누들핏 김치사발면맛",
    #     "category": "면류",
    #     "calories": 130,
    #     "price_range": "8개 9,890원(개당1,236원)",
    #     "retailers": ["쿠팡"],
    #     "chunks": [
    #         {"chunk_type": "basic_info", "text": "농심 누들핏 김치사발면맛 / 면류 김치 / 130kcal"},
    #         {"chunk_type": "question", "text": "살 안 찌는 김치라면 먹고 싶어"},
    #         {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 매콤한 컵라면"},
    #         {"chunk_type": "question", "text": "다이어트 중인데 칼칼한 국물 당길 때"},
    #         {"chunk_type": "question", "text": "일반 김치라면 대신 먹을 수 있는 거 뭐야"},
    #         {"chunk_type": "question", "text": "국물까지 다 먹어도 130칼로리인 라면"},
    #         {"chunk_type": "situation", "text": "야식으로 먹어도 되는 매콤한 면"},
    #         {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
    #         {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
    #         {"chunk_type": "situation", "text": "밤에 매운 게 당길 때 부담 없이"},
    #         {"chunk_type": "situation", "text": "얼큰하고 개운한 국물이 먹고 싶을 때"},
    #         {"chunk_type": "substitute", "text": "김치사발면 저칼로리 버전"},
    #         {"chunk_type": "substitute", "text": "인스턴트 김치라면 다이어트 대체품"},
    #         {"chunk_type": "substitute", "text": "130칼로리 매콤한 컵라면"},
    #         {"chunk_type": "substitute", "text": "일반 김치라면의 절반 칼로리"},
    #         {"chunk_type": "substitute", "text": "식이섬유 함유 저칼로리 면류"},
    #     ]
    # },
    {
        "brand": "농심",
        "product_name": "누들핏 육개장사발면맛",
        "category": "면류",
        "calories": 125,
        "price_range": "8개 12,200원(개당1,525원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "농심 누들핏 육개장사발면맛 / 면류 육개장 / 125kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 육개장사발면 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 얼큰한 컵라면"},
            {"chunk_type": "question", "text": "다이어트 중인데 칼칼한 육개장 국물 당길 때"},
            {"chunk_type": "question", "text": "일반 육개장사발면 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 125칼로리인 라면"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 얼큰한 면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "직장 점심시간에 가볍게 먹을 컵라면"},
            {"chunk_type": "situation", "text": "밤에 구수한 육개장 국물이 생각날 때"},
            {"chunk_type": "substitute", "text": "육개장사발면 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 육개장 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "125칼로리 얼큰한 컵라면"},
            {"chunk_type": "substitute", "text": "일반 육개장사발면의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "식이섬유 함유 저칼로리 면류"},
        ]
    },
    {
        "brand": "농심",
        "product_name": "누들핏 새우완탕",
        "category": "면류",
        "calories": 125,
        "price_range": "8개 11,840원(개당1,480원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "농심 누들핏 새우완탕 / 면류 완탕 / 125kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 완탕면 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 완탕"},
            {"chunk_type": "question", "text": "다이어트 중인데 든든한 국물 요리 당길 때"},
            {"chunk_type": "question", "text": "일반 완탕 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "125칼로리로 완탕 맛 즐기는 법"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 완탕면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "건더기 있는 국물 요리가 먹고 싶을 때"},
            {"chunk_type": "situation", "text": "해외 완탕 느낌 저칼로리로 즐기기"},
            {"chunk_type": "substitute", "text": "완탕면 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 완탕 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "125칼로리 완탕 컵라면"},
            {"chunk_type": "substitute", "text": "일반 완탕면의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "새우 건더기 있는 저칼로리 면류"},
        ]
    },
    {
        "brand": "농심",
        "product_name": "누들핏 새우탕맛",
        "category": "면류",
        "calories": 130,
        "price_range": "8개 9,750원(개당1,219원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "농심 누들핏 새우탕맛 / 면류 새우탕 / 130kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 새우탕 컵라면 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 시원한 해물 컵면"},
            {"chunk_type": "question", "text": "다이어트 중인데 개운한 새우 국물 당길 때"},
            {"chunk_type": "question", "text": "일반 새우탕면 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 130칼로리인 해물 라면"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 시원한 새우탕면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "개운한 해물 국물이 생각날 때"},
            {"chunk_type": "situation", "text": "해물 건더기 있는 저칼로리 면 먹고 싶을 때"},
            {"chunk_type": "substitute", "text": "새우탕면 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 해물라면 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "130칼로리 새우탕 컵라면"},
            {"chunk_type": "substitute", "text": "일반 새우탕면의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "식이섬유 함유 저칼로리 해물 면류"},
        ]
    },
    {
        "brand": "농심",
        "product_name": "누들핏 튀김우동맛",
        "category": "면류",
        "calories": 130,
        "price_range": "8개 10,010원(개당1,251원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "농심 누들핏 튀김우동맛 / 면류 우동 / 130kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 우동 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 컵우동"},
            {"chunk_type": "question", "text": "다이어트 중인데 우동 당길 때"},
            {"chunk_type": "question", "text": "일반 컵우동 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "130칼로리 우동 추천해줘"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 우동"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "밤에 출출할 때 부담 없이 먹는 컵라면"},
            {"chunk_type": "situation", "text": "국물이 생각날 때 저칼로리로 해결"},
            {"chunk_type": "substitute", "text": "튀김우동 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 우동 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "130칼로리 컵우동"},
            {"chunk_type": "substitute", "text": "일반 우동의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "탱글탱글한 면발 저칼로리 면류"},
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
    # products 삽입 후 실제 id 자동으로 가져오기
    cur.execute("""
        INSERT INTO products
            (brand, product_name, category, calories, price_range, retailers)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        p["brand"], p["product_name"], p.get("category"),
        p["calories"], p["price_range"], p["retailers"],
    ))

    product_id = cur.fetchone()[0]  # ← 실제 id 자동 반영
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