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
        "brand": "오뚜기",
        "product_name": "고단백 컵누들 마라샹궈맛",
        "category": "면류",
        "calories": 150,
        "price_range": "6개 7,970원(개당1,328원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 고단백 컵누들 마라샹궈맛 / 면류 마라 고단백 / 150kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 마라샹궈 먹고 싶어"},
            {"chunk_type": "question", "text": "단백질 높은 저칼로리 컵라면 뭐 있어"},
            {"chunk_type": "question", "text": "다이어트 중인데 마라향 매콤한 면 당길 때"},
            {"chunk_type": "question", "text": "고단백 저칼로리 컵면 추천해줘"},
            {"chunk_type": "question", "text": "운동 후 먹어도 되는 매콤한 면류"},
            {"chunk_type": "situation", "text": "운동하고 나서 단백질 보충할 때"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 고단백 다이어트 식사"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 마라맛 면"},
            {"chunk_type": "situation", "text": "헬스 식단 중 매콤한 게 당길 때"},
            {"chunk_type": "situation", "text": "저칼로리이면서 포만감 있는 식사 필요할 때"},
            {"chunk_type": "substitute", "text": "마라탕 저칼로리 고단백 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 마라면 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "150칼로리 고단백 마라 컵면"},
            {"chunk_type": "substitute", "text": "일반 마라탕의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "두부 건더기 포함 고단백 저칼로리 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 똠얌꿍 쌀국수",
        "category": "면류",
        "calories": 145,
        "price_range": "6개 9,000원(개당1,500원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 똠얌꿍 쌀국수 / 면류 쌀국수 태국 / 145kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 똠얌꿍 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 태국 쌀국수"},
            {"chunk_type": "question", "text": "다이어트 중인데 매콤새콤 이국적인 국물 당길 때"},
            {"chunk_type": "question", "text": "태국 식당 똠얌꿍 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 145칼로리인 똠얌 쌀국수"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 태국풍 쌀국수"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "매콤새콤 멈출 수 없는 똠얌 국물이 생각날 때"},
            {"chunk_type": "situation", "text": "세계 3대 스프 태국 대표음식 간편하게 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "똠얌꿍 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 태국쌀국수 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "145칼로리 매콤새콤 쌀국수"},
            {"chunk_type": "substitute", "text": "일반 똠얌꿍의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "기름 없는 저칼로리 이국적인 쌀국수"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 로제맛",
        "category": "면류",
        "calories": 165,
        "price_range": "6개 7,360원(개당1,227원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 로제맛 / 면류 로제 / 165kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 로제 떡볶이 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 로제맛 면"},
            {"chunk_type": "question", "text": "다이어트 중인데 크리미하고 매콤한 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 로제 파스타 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "소스까지 다 먹어도 165칼로리인 로제면"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 로제 당면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "크림과 치즈 풍미 저칼로리로 즐기고 싶을 때"},
            {"chunk_type": "situation", "text": "매콤꾸덕한 로제 떡볶이가 생각날 때"},
            {"chunk_type": "substitute", "text": "로제 파스타 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 로제면 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "165칼로리 로제맛 컵면"},
            {"chunk_type": "substitute", "text": "일반 로제 파스타의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "쫄깃한 당면 크리미 소스 저칼로리 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 마라탕",
        "category": "면류",
        "calories": 150,
        "price_range": "6개 6,800원(개당1,133원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 마라탕 / 면류 마라탕 / 150kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 마라탕 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 마라탕"},
            {"chunk_type": "question", "text": "다이어트 중인데 얼얼하고 진한 마라 국물 당길 때"},
            {"chunk_type": "question", "text": "마라탕 전문점 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "한 컵 다 먹어도 150칼로리인 마라탕"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 마라탕 당면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "진한 마라탕 국물이 생각날 때"},
            {"chunk_type": "situation", "text": "15단계 맵기 호불호 없는 마라탕 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "마라탕 전문점 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 마라탕 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "150칼로리 마라탕 컵면"},
            {"chunk_type": "substitute", "text": "일반 마라탕의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "두부피 건더기 포함 저칼로리 마라 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 매콤찜닭맛",
        "category": "면류",
        "calories": 150,
        "price_range": "6개 6,940원(개당1,157원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 매콤찜닭맛 / 면류 찜닭 / 150kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 찜닭 맛 면 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 매콤찜닭"},
            {"chunk_type": "question", "text": "다이어트 중인데 달콤매콤한 찜닭 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 찜닭 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "한 컵 다 먹어도 150칼로리인 찜닭 당면"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 찜닭 당면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "매콤달콤한 찜닭 양념이 생각날 때"},
            {"chunk_type": "situation", "text": "쫄깃한 당면으로 찜닭 맛 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "찜닭 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 찜닭 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "150칼로리 매콤찜닭 컵면"},
            {"chunk_type": "substitute", "text": "일반 찜닭의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "건강한 닭고기 맛 저칼로리 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 매콤한맛",
        "category": "면류",
        "calories": 120,
        "price_range": "6개 6,740원(개당1,123원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 매콤한맛 / 면류 매콤 / 120kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 매콤한 컵면 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 칼칼한 면"},
            {"chunk_type": "question", "text": "다이어트 중인데 쇠고기 육수 매콤한 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 매운 라면 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 120칼로리인 매콤한 면"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 매콤한 당면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "칼칼하고 탱글한 당면이 당길 때"},
            {"chunk_type": "situation", "text": "김치와 청양초 깔끔한 매운맛이 생각날 때"},
            {"chunk_type": "substitute", "text": "매운 라면 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 매콤면 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "120칼로리 매콤한 컵면"},
            {"chunk_type": "substitute", "text": "일반 매운 라면의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "기름 없는 저칼로리 매운맛 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 베트남쌀국수",
        "category": "면류",
        "calories": 140,
        "price_range": "6개 6,940원(개당1,157원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 베트남쌀국수 / 면류 쌀국수 베트남 / 140kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 베트남 쌀국수 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 쌀국수"},
            {"chunk_type": "question", "text": "다이어트 중인데 진한 쇠고기 육수 쌀국수 당길 때"},
            {"chunk_type": "question", "text": "베트남 식당 쌀국수 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 140칼로리인 베트남 쌀국수"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 베트남풍 쌀국수"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "진한 쇠고기 육수와 향신료 쌀국수가 생각날 때"},
            {"chunk_type": "situation", "text": "스리라차 소스로 매운맛 조절하며 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "베트남 쌀국수 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 쌀국수 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "140칼로리 베트남 쌀국수"},
            {"chunk_type": "substitute", "text": "일반 베트남 쌀국수의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "기름 없는 저칼로리 쇠고기 육수 쌀국수"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 얼큰쌀국수",
        "category": "면류",
        "calories": 130,
        "price_range": "6개 6,990원(개당1,165원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 얼큰쌀국수 / 면류 쌀국수 / 130kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 얼큰한 쌀국수 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 매콤 쌀국수"},
            {"chunk_type": "question", "text": "다이어트 중인데 칼칼하고 감칠맛 나는 국수 당길 때"},
            {"chunk_type": "question", "text": "일반 쌀국수 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 130칼로리인 얼큰 쌀국수"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 얼큰한 쌀국수"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "해장이 필요할 때 부담 없이"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "알싸한 마늘 다대기 국물이 생각날 때"},
            {"chunk_type": "substitute", "text": "얼큰쌀국수 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 매콤쌀국수 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "130칼로리 얼큰한 국물 쌀국수"},
            {"chunk_type": "substitute", "text": "일반 얼큰라면의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "기름 없는 저칼로리 매콤 국물 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 열라면",
        "category": "면류",
        "calories": 120,
        "price_range": "6개 7,590원(개당1,265원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 열라면 / 면류 열라면 / 120kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 열라면 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 매운 라면"},
            {"chunk_type": "question", "text": "다이어트 중인데 화끈하고 칼칼한 열라면 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 열라면 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 120칼로리인 매운 면"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 매운 당면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 스트레스 풀고 싶을 때"},
            {"chunk_type": "situation", "text": "열라면 특유의 칼칼하고 깔끔한 매운맛이 생각날 때"},
            {"chunk_type": "situation", "text": "컵누들 국물류 중 가장 매운맛 원할 때"},
            {"chunk_type": "substitute", "text": "열라면 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 매운라면 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "120칼로리 매운 컵면"},
            {"chunk_type": "substitute", "text": "일반 열라면의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "지방 0.7g 초저지방 매운 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 우동맛",
        "category": "면류",
        "calories": 120,
        "price_range": "6개 6,830원(개당1,138원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 우동맛 / 면류 우동 / 120kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 우동 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 컵우동"},
            {"chunk_type": "question", "text": "다이어트 중인데 진한 가쓰오 우동 국물 당길 때"},
            {"chunk_type": "question", "text": "일반 우동 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 120칼로리인 우동"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 담백한 우동"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "깔끔한 가쓰오 국물이 생각날 때"},
            {"chunk_type": "situation", "text": "뜨겁지 않게 녹두당면으로 가볍게 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "우동 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 우동 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "120칼로리 컵우동"},
            {"chunk_type": "substitute", "text": "일반 우동의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "기름 없는 저칼로리 국물 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 잔치쌀국수",
        "category": "면류",
        "calories": 120,
        "price_range": "6개 6,990원(개당1,165원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 잔치쌀국수 / 면류 쌀국수 / 120kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 쌀국수 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 국수"},
            {"chunk_type": "question", "text": "다이어트 중인데 따뜻한 국물 국수 당길 때"},
            {"chunk_type": "question", "text": "일반 쌀국수 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 120칼로리인 면 요리"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 담백한 국수"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "직장 점심시간에 가볍게 먹을 컵면"},
            {"chunk_type": "situation", "text": "멸치 국물 깔끔한 맛이 생각날 때"},
            {"chunk_type": "substitute", "text": "잔치국수 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 쌀국수 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "120칼로리 담백한 컵국수"},
            {"chunk_type": "substitute", "text": "일반 쌀국수의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "기름 없는 저칼로리 국물 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 짜슐랭",
        "category": "면류",
        "calories": 165,
        "price_range": "6개 9,480원(개당1,580원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 짜슐랭 / 면류 짜장 / 165kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 짜장면 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 진한 짜장맛 면"},
            {"chunk_type": "question", "text": "다이어트 중인데 고온에 볶은 짜장 풍미 당길 때"},
            {"chunk_type": "question", "text": "짜슐랭 대신 먹을 수 있는 저칼로리 짜장면 뭐야"},
            {"chunk_type": "question", "text": "소스까지 다 먹어도 165칼로리인 짜장 당면"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 짜장 당면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "파와 양파기름 진한 짜장 풍미가 생각날 때"},
            {"chunk_type": "situation", "text": "프리미엄 짜장라면 맛 저칼로리로 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "짜장라면 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 짜장면 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "165칼로리 짜장맛 컵면"},
            {"chunk_type": "substitute", "text": "일반 짜장면의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "뜨겁지 않은 저칼로리 짜장 당면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 짜장맛",
        "category": "면류",
        "calories": 170,
        "price_range": "6개 10,400원(개당1,733원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 짜장맛 / 면류 짜장 / 170kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 짜장면 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 짜장맛 당면"},
            {"chunk_type": "question", "text": "다이어트 중인데 춘장 야채베이스 짜장 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 짜장면 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "소스까지 다 먹어도 170칼로리인 짜장 컵면"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 짜장 당면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "잘 볶은 춘장과 야채베이스 진한 짜장이 생각날 때"},
            {"chunk_type": "situation", "text": "닭가슴살 소시지와 함께 곁들여 먹고 싶을 때"},
            {"chunk_type": "substitute", "text": "짜장면 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 짜장 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "170칼로리 짜장맛 컵면"},
            {"chunk_type": "substitute", "text": "일반 짜장면의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "기름 없는 저칼로리 짜장 당면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 짬뽕맛",
        "category": "면류",
        "calories": 140,
        "price_range": "6개 7,510원(개당1,252원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 짬뽕맛 / 면류 짬뽕 / 140kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 짬뽕 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 짬뽕맛 면"},
            {"chunk_type": "question", "text": "다이어트 중인데 불향 진한 짬뽕 국물 당길 때"},
            {"chunk_type": "question", "text": "일반 짬뽕 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 140칼로리인 짬뽕"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 짬뽕 당면"},
            {"chunk_type": "situation", "text": "해장이 필요할 때 부담 없이"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "불향 가득한 진한 짬뽕 국물이 생각날 때"},
            {"chunk_type": "substitute", "text": "짬뽕 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 짬뽕 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "140칼로리 짬뽕맛 컵면"},
            {"chunk_type": "substitute", "text": "일반 짬뽕의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "기름 없는 저칼로리 해물 짬뽕 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 참깨라면",
        "category": "면류",
        "calories": 140,
        "price_range": "6개 7,390원(개당1,232원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 참깨라면 / 면류 참깨라면 / 140kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 참깨라면 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 참깨 국물 면"},
            {"chunk_type": "question", "text": "다이어트 중인데 고소한 참깨 라면 맛 당길 때"},
            {"chunk_type": "question", "text": "일반 참깨라면 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "국물까지 다 먹어도 140칼로리인 참깨라면"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 고소한 참깨 당면"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "사무실 책상에 쌓아두고 간식으로 먹을 때"},
            {"chunk_type": "situation", "text": "고소하고 칼칼한 참깨라면 맛이 그리울 때"},
            {"chunk_type": "substitute", "text": "참깨라면 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 참깨라면 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "140칼로리 참깨 국물 컵면"},
            {"chunk_type": "substitute", "text": "일반 참깨라면의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "기름 없는 저칼로리 고소한 국물 면류"},
        ]
    },
    {
        "brand": "오뚜기",
        "product_name": "컵누들 팟타이쌀국수",
        "category": "면류",
        "calories": 175,
        "price_range": "6개 7,360원(개당1,227원)",
        "retailers": ["쿠팡"],
        "chunks": [
            {"chunk_type": "basic_info", "text": "오뚜기 컵누들 팟타이쌀국수 / 면류 쌀국수 태국 / 175kcal"},
            {"chunk_type": "question", "text": "살 안 찌는 팟타이 먹고 싶어"},
            {"chunk_type": "question", "text": "죄책감 없이 먹을 수 있는 태국 볶음쌀국수"},
            {"chunk_type": "question", "text": "다이어트 중인데 단짠단짠 감칠맛 팟타이 당길 때"},
            {"chunk_type": "question", "text": "태국 식당 팟타이 대신 먹을 수 있는 거 뭐야"},
            {"chunk_type": "question", "text": "소스까지 다 먹어도 175칼로리인 팟타이"},
            {"chunk_type": "situation", "text": "야식으로 먹어도 되는 태국풍 볶음쌀국수"},
            {"chunk_type": "situation", "text": "혼밥할 때 간편하게 다이어트 식사"},
            {"chunk_type": "situation", "text": "운동하고 나서 먹어도 되는 면류"},
            {"chunk_type": "situation", "text": "피시소스 감칠맛과 새콤달콤한 팟타이가 생각날 때"},
            {"chunk_type": "situation", "text": "태국 대표 볶음쌀국수 간편하게 즐기고 싶을 때"},
            {"chunk_type": "substitute", "text": "팟타이 저칼로리 버전"},
            {"chunk_type": "substitute", "text": "인스턴트 태국 볶음쌀국수 다이어트 대체품"},
            {"chunk_type": "substitute", "text": "175칼로리 팟타이 쌀국수"},
            {"chunk_type": "substitute", "text": "일반 팟타이의 절반 칼로리"},
            {"chunk_type": "substitute", "text": "기름 없는 저칼로리 이국적인 볶음쌀국수"},
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
