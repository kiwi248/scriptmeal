import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 제품 + 청크를 함께 묶어서 관리
# calories_per_100g: 분말류/액체류/소스류
# calories_per_unit: 고체류/과자류/곤약류 (1회 제공량 기준)
products = [
    {
        "brand": "알티스트",
        "product_name": "알티스트 밀가루대신 글루텐프리 아몬드 파우더 250g",
        "category": "베이킹재료",
        "calories_per_100g": 573,
        "price_range": "250g 1개 7,980원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "알티스트 밀가루대신 아몬드 파우더 / 베이킹재료 / 573kcal(100g 기준) / 당류 4g / 아몬드 100%(미국산) / 글루텐프리 / 단백질 28g(100g 기준) / 베이킹·쿠킹·마카롱·쿠키 활용"},
            {"chunk_type": "question", "text": "밀가루 대신 쓸 수 있는 아몬드 파우더 추천해줘"},
            {"chunk_type": "question", "text": "글루텐프리 베이킹 재료 뭐가 좋아"},
            {"chunk_type": "question", "text": "저탄고지 베이킹할 때 밀가루 대체품 뭐야"},
            {"chunk_type": "question", "text": "아몬드 파우더로 만드는 다이어트 빵 재료 추천"},
            {"chunk_type": "question", "text": "단백질 높은 밀가루 대체 가루 뭐가 있어"},
            {"chunk_type": "situation", "text": "마카롱 만들 때 아몬드 파우더 사용"},
            {"chunk_type": "situation", "text": "글루텐프리 쿠키 베이킹에 아몬드 파우더 활용"},
            {"chunk_type": "situation", "text": "다이어트 케이크 만들 때 밀가루 대신 아몬드 파우더"},
            {"chunk_type": "situation", "text": "저탄수화물 빵 레시피에 아몬드 파우더 활용"},
            {"chunk_type": "situation", "text": "아이 간식으로 글루텐프리 쿠키 만들 때"},
            {"chunk_type": "substitute", "text": "밀가루 글루텐프리 대체 가루"},
            {"chunk_type": "substitute", "text": "아몬드 100% 글루텐프리 베이킹 파우더"},
            {"chunk_type": "substitute", "text": "저탄고지 밀가루 대체품 아몬드 파우더"},
            {"chunk_type": "substitute", "text": "단백질 28g 고단백 베이킹 가루"},
            {"chunk_type": "substitute", "text": "밀가루 0% 아몬드 베이킹 재료"},
        ]
    },
    {
        "brand": "알티스트",
        "product_name": "알티스트 밀가루대신 글루텐프리 타피오카 전분 1.2kg",
        "category": "베이킹재료",
        "calories_per_100g": 365,
        "price_range": "1.2kg 1개 6,310원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "알티스트 밀가루대신 글루텐프리 타피오카 전분 / 베이킹재료 / 365kcal(100g 기준) / 당류 0g / 타피오카전분 99.9%(미국산) / 글루텐프리 / 쫄깃하고 바삭한 식감 / 다양한 요리 활용 가능 / Plant Based"},
            {"chunk_type": "question", "text": "글루텐프리 타피오카 전분 추천해줘"},
            {"chunk_type": "question", "text": "밀가루 대신 쓸 수 있는 전분 뭐가 있어"},
            {"chunk_type": "question", "text": "쫄깃한 식감 내는 글루텐프리 가루 뭐야"},
            {"chunk_type": "question", "text": "저탄고지 베이킹용 타피오카 전분 추천"},
            {"chunk_type": "question", "text": "두바이쫀득쿠키 재료 뭐야"},
            {"chunk_type": "situation", "text": "쫀득한 쿠키 만들 때 타피오카 전분 활용"},
            {"chunk_type": "situation", "text": "글루텐프리 떡 만들 때 타피오카 전분 사용"},
            {"chunk_type": "situation", "text": "튀김옷에 바삭함 더할 때 타피오카 전분 활용"},
            {"chunk_type": "situation", "text": "브라우니나 케이크 반죽에 타피오카 전분 활용"},
            {"chunk_type": "situation", "text": "다이어트 베이킹 시 밀가루 대체 전분으로 활용"},
            {"chunk_type": "substitute", "text": "밀가루 글루텐프리 전분 대체"},
            {"chunk_type": "substitute", "text": "타피오카 전분 쫄깃한 식감"},
            {"chunk_type": "substitute", "text": "글루텐프리 바삭한 튀김 전분"},
            {"chunk_type": "substitute", "text": "당류 0g 밀가루 대체 전분"},
            {"chunk_type": "substitute", "text": "식물성 글루텐프리 타피오카 베이킹 재료"},
        ]
    },
    {
        "brand": "마녀의부엌",
        "product_name": "마녀의부엌 100% 네덜란드산 무가당 코코아 파우더 200g",
        "category": "베이킹재료",
        "calories_per_100g": 313,
        "price_range": "200g 1개 9,500원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마녀의부엌 무가당 코코아 파우더 / 베이킹재료 / 313kcal(100g 기준) / 당류 1g / 코코아 파우더(네덜란드) 100% / 무가당 / 보존료·첨가물 없음 / 단백질 22g / 지방 11g / 파베초콜릿·티라미수·초코스프레드·쿠키 활용"},
            {"chunk_type": "question", "text": "무가당 코코아 파우더 추천해줘"},
            {"chunk_type": "question", "text": "다이어트 초콜릿 베이킹 재료 뭐가 좋아"},
            {"chunk_type": "question", "text": "설탕 없는 코코아 파우더 어디 있어"},
            {"chunk_type": "question", "text": "저당 티라미수 만들 때 코코아 파우더 추천"},
            {"chunk_type": "question", "text": "첨가물 없는 순수 코코아 파우더 뭐야"},
            {"chunk_type": "situation", "text": "다이어트 초코 케이크 만들 때 무가당 코코아 파우더 활용"},
            {"chunk_type": "situation", "text": "저당 티라미수 만들 때 코코아 파우더 사용"},
            {"chunk_type": "situation", "text": "초코 스프레드 만들 때 무가당 코코아 파우더 활용"},
            {"chunk_type": "situation", "text": "파베초콜릿 만들 때 무가당 코코아 파우더 사용"},
            {"chunk_type": "situation", "text": "다이어트 초코 쿠키 베이킹에 코코아 파우더 활용"},
            {"chunk_type": "substitute", "text": "설탕 든 코코아 파우더 무가당 대체"},
            {"chunk_type": "substitute", "text": "당류 1g 무가당 코코아 파우더"},
            {"chunk_type": "substitute", "text": "100% 순수 네덜란드산 코코아 분말"},
            {"chunk_type": "substitute", "text": "보존료 첨가물 없는 코코아 파우더"},
            {"chunk_type": "substitute", "text": "다이어트 베이킹용 무가당 초코 가루"},
        ]
    },
    {
        "brand": "키토라푸드",
        "product_name": "키토라프레시 프로틴 저당식빵 350g",
        "category": "빵류",
        "calories_per_unit": 818,   # 1개(350g) 기준 818kcal
        "price_range": "350g 1개 8,100원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "키토라푸드 키토라프레시 프로틴 저당식빵 / 빵류 / 234kcal(100g 기준) / 당류 1g 미만 / 단백질 24g(100g 기준) / 발효밀단백질 20.53%·아몬드분말 5.95% / 나한과스위터너 5.9% / 냉동 보관 / HACCP 인증 / 샌드위치·그릭요거트 곁들임 활용"},
            {"chunk_type": "question", "text": "저당 고단백 식빵 추천해줘"},
            {"chunk_type": "question", "text": "다이어트 중에 먹을 수 있는 식빵 뭐야"},
            {"chunk_type": "question", "text": "당 낮은 단백질 빵 어떤 게 있어"},
            {"chunk_type": "question", "text": "키토 식단에 맞는 식빵 추천"},
            {"chunk_type": "question", "text": "냉동 보관 저당 식빵 뭐가 좋아"},
            {"chunk_type": "situation", "text": "다이어트 중 샌드위치 만들 때 저당식빵 활용"},
            {"chunk_type": "situation", "text": "아침 식사로 저당 고단백 식빵 먹을 때"},
            {"chunk_type": "situation", "text": "그릭요거트에 저당식빵 곁들여 먹을 때"},
            {"chunk_type": "situation", "text": "운동 후 단백질 보충 식사로 저당식빵 활용"},
            {"chunk_type": "situation", "text": "키토 식단 중 빵이 당길 때 저당식빵으로 대체"},
            {"chunk_type": "substitute", "text": "일반 식빵 저당 고단백 대체"},
            {"chunk_type": "substitute", "text": "당류 1g 미만 단백질 24g 식빵"},
            {"chunk_type": "substitute", "text": "키토 식단 밀가루 빵 대체품"},
            {"chunk_type": "substitute", "text": "발효밀단백질 아몬드분말 저당식빵"},
            {"chunk_type": "substitute", "text": "냉동 보관 다이어트 고단백 식빵"},
        ]
    },
    {
        "brand": "배대감",
        "product_name": "배대감 저당 저칼로리 알룰로스 오리지널 530g",
        "category": "당류대체",
        "calories_per_100g": 20,
        "price_range": "530g 1개 5,290원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "배대감 저당 저칼로리 알룰로스 오리지널 / 당류대체 / 20kcal(100g 기준) / 당류 0.7g / 알룰로스 99.9% / 설탕 대체 감미료 / 음료·요리·베이킹 활용 / 저당 다이어트 식단 적합"},
            {"chunk_type": "question", "text": "설탕 대신 쓸 수 있는 저칼로리 감미료 추천"},
            {"chunk_type": "question", "text": "다이어트 중 단 맛 내는 재료 뭐가 있어"},
            {"chunk_type": "question", "text": "칼로리 낮은 설탕 대체품 뭐야"},
            {"chunk_type": "question", "text": "알룰로스 어떤 제품이 좋아"},
            {"chunk_type": "question", "text": "당류 걱정 없는 베이킹 감미료 추천해줘"},
            {"chunk_type": "situation", "text": "다이어트 베이킹할 때 설탕 대신 알룰로스 사용"},
            {"chunk_type": "situation", "text": "커피나 음료에 설탕 대신 알룰로스 넣을 때"},
            {"chunk_type": "situation", "text": "저당 디저트 만들 때 알룰로스로 단맛 내기"},
            {"chunk_type": "situation", "text": "요리에 윤기 더할 때 알룰로스 활용"},
            {"chunk_type": "situation", "text": "당 제한 식단 중 단맛이 당길 때 알룰로스 사용"},
            {"chunk_type": "substitute", "text": "설탕 저칼로리 알룰로스 대체"},
            {"chunk_type": "substitute", "text": "20kcal 저당 설탕 대체 감미료"},
            {"chunk_type": "substitute", "text": "알룰로스 99.9% 순수 감미료"},
            {"chunk_type": "substitute", "text": "다이어트 베이킹 설탕 대신 재료"},
            {"chunk_type": "substitute", "text": "당류 0.7g 저칼로리 액상 감미료"},
        ]
    },
    {
        "brand": "알티스트",
        "product_name": "알티스트 설탕대신 알룰로스 400g",
        "category": "당류대체",
        "calories_per_100g": 0,
        "price_range": "400g 1개 6,820원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "알티스트 설탕대신 알룰로스 / 당류대체 / 0kcal(100g 기준) / 당류 0g / 알룰로스 파우더 99.99% / 설탕 대체 0칼로리 감미료 / 커피·베이킹·요리 활용 / 소화되지 않고 배출되는 Okcal 설탕대체재"},
            {"chunk_type": "question", "text": "0칼로리 설탕 대체품 추천해줘"},
            {"chunk_type": "question", "text": "칼로리 없는 베이킹용 감미료 뭐야"},
            {"chunk_type": "question", "text": "당류 0g 설탕 대신 쓸 수 있는 가루 뭐가 있어"},
            {"chunk_type": "question", "text": "다이어트 쿠키 만들 때 설탕 대체재 추천"},
            {"chunk_type": "question", "text": "아이 간식에 설탕 대신 넣을 수 있는 감미료 추천"},
            {"chunk_type": "situation", "text": "다이어트 베이킹할 때 설탕 대신 알룰로스 파우더 사용"},
            {"chunk_type": "situation", "text": "커피에 설탕 대신 알룰로스 넣을 때"},
            {"chunk_type": "situation", "text": "저당 케이크 만들 때 0칼로리 알룰로스 활용"},
            {"chunk_type": "situation", "text": "요리에 단맛 더할 때 0칼로리 알룰로스 사용"},
            {"chunk_type": "situation", "text": "당 걱정 없이 디저트 만들 때 알룰로스 파우더 활용"},
            {"chunk_type": "substitute", "text": "설탕 0kcal 알룰로스 파우더 대체"},
            {"chunk_type": "substitute", "text": "당류 0g 0칼로리 설탕 대체 가루"},
            {"chunk_type": "substitute", "text": "알룰로스 99.99% 순수 파우더 감미료"},
            {"chunk_type": "substitute", "text": "다이어트 베이킹 칼로리 없는 설탕"},
            {"chunk_type": "substitute", "text": "소화 안 되는 0칼로리 설탕 대체재"},
        ]
    },
]

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
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
