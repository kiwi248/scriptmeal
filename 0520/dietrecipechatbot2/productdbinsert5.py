import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 제품 + 청크를 함께 묶어서 관리
products = [
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 알룰로스",
        "category": "감미료류",
        "calories": 0,
        "price_range": "300g(15g×20개) 1박스 7,980원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 알룰로스 / 감미료류 설탕대체 / 0kcal(1개 15g 기준) / 당류 0g / 스틱형"},
            {"chunk_type": "question", "text": "살 안 찌는 설탕 대체품 뭐 있어"},
            {"chunk_type": "question", "text": "죄책감 없이 단맛 낼 수 있는 감미료"},
            {"chunk_type": "question", "text": "다이어트 중인데 단 게 당길 때 설탕 대신 쓸 것"},
            {"chunk_type": "question", "text": "칼로리 0인 설탕 대체 감미료 추천해줘"},
            {"chunk_type": "question", "text": "당류 없이 달콤하게 먹을 수 있는 방법"},
            {"chunk_type": "situation", "text": "커피나 차에 설탕 대신 넣을 때"},
            {"chunk_type": "situation", "text": "다이어트 중 요리나 베이킹에 설탕 대체로"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 조리에 활용"},
            {"chunk_type": "situation", "text": "운동 후 단백질 쉐이크에 달콤함 더할 때"},
            {"chunk_type": "situation", "text": "밤에 단 게 당길 때 칼로리 걱정 없이"},
            {"chunk_type": "substitute", "text": "설탕 0칼로리 대체품"},
            {"chunk_type": "substitute", "text": "인스턴트 감미료 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "0kcal 스틱형 알룰로스"},
            {"chunk_type": "substitute", "text": "일반 설탕의 칼로리 0 버전"},
            {"chunk_type": "substitute", "text": "알룰로스 스테비아 나한과 천연 감미료"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 알룰로스 액상",
        "category": "감미료류",
        "calories": 8,
        "price_range": "500g 1개 7,980원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 알룰로스 / 소스류 감미료 / 8kcal(100g 기준) / 당류 1g / 액상형 500g / 설탕 대체 감미료"},
            {"chunk_type": "question", "text": "설탕 대신 쓸 수 있는 저칼로리 액상 감미료 뭐야"},
            {"chunk_type": "question", "text": "요리할 때 설탕 대신 넣을 수 있는 거 추천해줘"},
            {"chunk_type": "question", "text": "다이어트 중인데 단맛 포기 못할 때"},
            {"chunk_type": "question", "text": "화한 맛 없이 달콤한 설탕 대체품 찾고 있어"},
            {"chunk_type": "question", "text": "베이킹이나 요리에 설탕 대신 쓰는 알룰로스 뭐가 좋아"},
            {"chunk_type": "situation", "text": "요리나 베이킹에 설탕 대신 넣을 때"},
            {"chunk_type": "situation", "text": "커피·차·에이드에 시럽 대신 넣고 싶을 때"},
            {"chunk_type": "situation", "text": "다이어트 중 단맛이 필요한 모든 음식에"},
            {"chunk_type": "situation", "text": "당류 줄이면서 디저트 맛 살리고 싶을 때"},
            {"chunk_type": "situation", "text": "밤에 단 게 당길 때 칼로리 부담 없이 활용"},
            {"chunk_type": "substitute", "text": "설탕 저칼로리 액상 대체품"},
            {"chunk_type": "substitute", "text": "요리용 설탕 다이어트 대체 감미료"},
            {"chunk_type": "substitute", "text": "8kcal 액상 알룰로스"},
            {"chunk_type": "substitute", "text": "일반 설탕의 저칼로리 액상 버전"},
            {"chunk_type": "substitute", "text": "알룰로스 스테비아 나한과 천연 감미료 액상"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 C8 MCT 오일",
        "category": "건강기름류",
        "calories": 810,
        "price_range": "500ml 1개 22,220원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 C8 MCT 오일 / 건강기름류 MCT오일 / 810kcal(100ml 기준) / 당류 0g / 코코넛 100%(필리핀산) / 500ml"},
            {"chunk_type": "question", "text": "방탄커피 만들 때 넣을 MCT오일 추천해줘"},
            {"chunk_type": "question", "text": "다이어트에 좋은 MCT오일 뭐 있어"},
            {"chunk_type": "question", "text": "코코넛에서 추출한 건강한 오일 뭐야"},
            {"chunk_type": "question", "text": "C8 지방산 함량 높은 MCT오일 찾고 있어"},
            {"chunk_type": "question", "text": "케토제닉 식단에 쓸 수 있는 오일 알려줘"},
            {"chunk_type": "situation", "text": "아침 방탄커피에 MCT오일 한 스푼 넣을 때"},
            {"chunk_type": "situation", "text": "케토·저탄수화물 다이어트 식단 중일 때"},
            {"chunk_type": "situation", "text": "운동 전 에너지 보충을 위해 섭취할 때"},
            {"chunk_type": "situation", "text": "샐러드나 요리에 건강한 오일 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "당류 없이 고지방 건강 오일이 필요할 때"},
            {"chunk_type": "substitute", "text": "일반 코코넛오일 C8 고순도 버전"},
            {"chunk_type": "substitute", "text": "방탄커피용 MCT오일 대체품"},
            {"chunk_type": "substitute", "text": "C8 지방산 특화 MCT오일"},
            {"chunk_type": "substitute", "text": "코코넛오일보다 C8 함량 높은 정제 오일"},
            {"chunk_type": "substitute", "text": "케토 다이어트용 고순도 중쇄지방산 오일"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 저당 고추장",
        "category": "소스류",
        "calories": 100,
        "price_range": "230g 1개 11,290원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 저당 고추장 / 소스류 고추장 / 100kcal(100g 기준) / 당류 2g / 국산 고춧가루 100% / 설탕 무첨가"},
            {"chunk_type": "question", "text": "당 적은 고추장 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 쓸 수 있는 저당 고추장"},
            {"chunk_type": "question", "text": "다이어트 중인데 비빔밥이나 떡볶이에 고추장 쓰고 싶어"},
            {"chunk_type": "question", "text": "일반 고추장 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "설탕 없이 만든 국산 고추장 추천해줘"},
            {"chunk_type": "situation", "text": "비빔밥·비빔면에 죄책감 없이 고추장 올릴 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 매콤한 양념 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 고추장 활용"},
            {"chunk_type": "situation", "text": "운동 후 단백질 식사에 매콤한 소스로 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 한식 양념 맛 제대로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "고추장 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 고추장 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 2g 저당 고추장"},
            {"chunk_type": "substitute", "text": "일반 고추장의 절반 이하 당류"},
            {"chunk_type": "substitute", "text": "국산 고춧가루 알룰로스 설탕 무첨가 고추장"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 저당 드레싱 시저",
        "category": "소스류",
        "calories": 320,
        "price_range": "240g 1개 8,900원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 저당 드레싱 시저 / 소스류 드레싱 / 320kcal(100g 기준) / 당류 0g"},
            {"chunk_type": "question", "text": "당 없는 시저 드레싱 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 시저 드레싱"},
            {"chunk_type": "question", "text": "다이어트 중인데 크리미한 시저 샐러드 드레싱 당길 때"},
            {"chunk_type": "question", "text": "일반 시저 드레싱 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "당류 0g 시저 드레싱 추천해줘"},
            {"chunk_type": "situation", "text": "시저 샐러드에 마음껏 뿌려도 되는 드레싱"},
            {"chunk_type": "situation", "text": "다이어트 식단에 고급스러운 드레싱 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 시저 드레싱 활용"},
            {"chunk_type": "situation", "text": "운동 후 샐러드에 곁들일 크리미한 드레싱"},
            {"chunk_type": "situation", "text": "당류 체크하는 분이 안심하고 먹을 시저 드레싱"},
            {"chunk_type": "substitute", "text": "시저 드레싱 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 시저 드레싱 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 0g 시저 드레싱"},
            {"chunk_type": "substitute", "text": "일반 시저 드레싱의 절반 당류"},
            {"chunk_type": "substitute", "text": "엑스트라버진 올리브오일 저당 시저 드레싱"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 저당 드레싱 유자",
        "category": "소스류",
        "calories": 10,
        "price_range": "280g 1개 7,900원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 저당 드레싱 유자 / 소스류 드레싱 / 10kcal(100g 기준) / 한 통 30kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 드레싱 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 샐러드 드레싱"},
            {"chunk_type": "question", "text": "다이어트 중인데 상큼한 드레싱 당길 때"},
            {"chunk_type": "question", "text": "한 통 다 써도 살 안 찌는 드레싱 뭐야"},
            {"chunk_type": "question", "text": "저당 유자 드레싱 추천해줘"},
            {"chunk_type": "situation", "text": "샐러드에 마음껏 뿌려도 되는 드레싱"},
            {"chunk_type": "situation", "text": "다이어트 식단에 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저칼로리 드레싱"},
            {"chunk_type": "situation", "text": "운동 후 샐러드에 뿌려 먹을 때"},
            {"chunk_type": "situation", "text": "밤에 채소 먹을 때 부담 없이 곁들이는 드레싱"},
            {"chunk_type": "substitute", "text": "유자 드레싱 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "일반 드레싱 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "한 통 30칼로리 드레싱"},
            {"chunk_type": "substitute", "text": "일반 드레싱의 절반 이하 칼로리"},
            {"chunk_type": "substitute", "text": "국산 유자 레몬제스트 저당 드레싱"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 저당 드레싱 오리엔탈",
        "category": "소스류",
        "calories": 65,
        "price_range": "270g 1개 7,700원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 저당 드레싱 오리엔탈 / 소스류 드레싱 / 65kcal(100g 기준) / 당류 1g 미만 / 한식간장·엑스트라버진 올리브오일·마늘 베이스"},
            {"chunk_type": "question", "text": "당 적은 오리엔탈 드레싱 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 뿌려 먹을 수 있는 간장 드레싱"},
            {"chunk_type": "question", "text": "다이어트 중인데 감칠맛 나는 드레싱 당길 때"},
            {"chunk_type": "question", "text": "일반 오리엔탈 드레싱 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "한식간장 베이스 저당 드레싱 추천해줘"},
            {"chunk_type": "situation", "text": "샐러드에 감칠맛 드레싱 뿌려 먹을 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 깊은 맛 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 오리엔탈 드레싱 활용"},
            {"chunk_type": "situation", "text": "운동 후 샐러드에 곁들일 담백한 간장 드레싱"},
            {"chunk_type": "situation", "text": "당류 신경 쓰면서도 한식 풍미 드레싱 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "오리엔탈 드레싱 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 간장 드레싱 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 1g 미만 오리엔탈 드레싱"},
            {"chunk_type": "substitute", "text": "일반 오리엔탈 드레싱의 저당 대체품"},
            {"chunk_type": "substitute", "text": "한식간장 올리브오일 베이스 저당 드레싱"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 저당 드레싱 참깨흑임자",
        "category": "소스류",
        "calories": 315,
        "price_range": "240g 1개 8,740원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 저당 드레싱 참깨흑임자 / 소스류 드레싱 / 315kcal(100g 기준) / 당류 0g"},
            {"chunk_type": "question", "text": "당 없는 참깨 드레싱 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 고소한 드레싱"},
            {"chunk_type": "question", "text": "다이어트 중인데 고소한 참깨흑임자 드레싱 당길 때"},
            {"chunk_type": "question", "text": "일반 참깨 드레싱 대신 먹을 수 있는 저당 드레싱 뭐야"},
            {"chunk_type": "question", "text": "당류 0g 고소한 드레싱 추천해줘"},
            {"chunk_type": "situation", "text": "샐러드에 고소하게 뿌려 먹을 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에 포만감 더하고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 드레싱 활용"},
            {"chunk_type": "situation", "text": "운동 후 샐러드에 곁들일 고소한 드레싱"},
            {"chunk_type": "situation", "text": "당류 체크하는 분이 안심하고 먹을 드레싱"},
            {"chunk_type": "substitute", "text": "참깨 드레싱 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 참깨 드레싱 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 0g 참깨흑임자 드레싱"},
            {"chunk_type": "substitute", "text": "일반 참깨 드레싱의 저당 버전"},
            {"chunk_type": "substitute", "text": "알룰로스 스테비아 감미료 참깨 드레싱"},
        ]
    },
    {
        "brand": "마이노멀",
        "product_name": "마이노멀 저당 마요네즈",
        "category": "소스류",
        "calories": 560,
        "price_range": "260g 1개 9,550원",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "마이노멀 저당 마요네즈 / 소스류 마요네즈 / 560kcal(100g 기준) / 당류 0g / 엑스트라버진 올리브오일 64%"},
            {"chunk_type": "question", "text": "당 없는 마요네즈 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 덜한 마요네즈 뭐 있어"},
            {"chunk_type": "question", "text": "다이어트 중인데 마요네즈 당길 때"},
            {"chunk_type": "question", "text": "일반 마요네즈 대신 먹을 수 있는 저당 버전 뭐야"},
            {"chunk_type": "question", "text": "올리브오일로 만든 건강한 마요네즈 추천해줘"},
            {"chunk_type": "situation", "text": "샐러드나 샌드위치에 마음껏 바를 때"},
            {"chunk_type": "situation", "text": "다이어트 식단에도 마요네즈 맛 즐기고 싶을 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 저당 마요네즈 활용"},
            {"chunk_type": "situation", "text": "운동 후 닭가슴살 요리에 곁들일 때"},
            {"chunk_type": "situation", "text": "당류 신경 쓰는 분이 안심하고 쓸 마요네즈"},
            {"chunk_type": "substitute", "text": "마요네즈 저당 버전"},
            {"chunk_type": "substitute", "text": "일반 마요네즈 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "당류 0g 올리브오일 마요네즈"},
            {"chunk_type": "substitute", "text": "일반 마요네즈의 저당 대체품"},
            {"chunk_type": "substitute", "text": "엑스트라버진 올리브오일 저당 마요네즈"},
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
    cur.execute("""
        INSERT INTO products
            (brand, product_name, category, calories, price_range, retailers)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        p["brand"], p["product_name"], p.get("category"),
        p["calories"], p["price_range"], p["retailers"],
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
