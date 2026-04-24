"""
레시피 RAG 시스템 v2.2
- 카글 API로 CSV 직접 다운로드
- OpenAI 임베딩 (text-embedding-3-small)
- 검색기 활용 (gpt-3.5-turbo)
- [v2.2 변경사항]
  1. 15분 이하 레시피로 필터링 변경
  2. LLM 답변 한국어 출력
  3. 상세 조리 과정 포함 출력

사전 설치:
pip install langchain langchain-community langchain-openai
pip install faiss-cpu tiktoken openai kaggle pandas
"""

import os
import pandas as pd
from dotenv import load_dotenv  # pip install python-dotenv

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain


# ─────────────────────────────────────────────
# API 키 설정 (.env 파일에서 자동 로드)
# ─────────────────────────────────────────────
load_dotenv()  # .env → os.environ 자동 주입


# ─────────────────────────────────────────────
# 1. 카글 API로 CSV 불러오기
# ─────────────────────────────────────────────
print("=" * 50)
print("[1단계] 카글 API로 데이터셋 다운로드")
print("=" * 50)

import kaggle  # kaggle 패키지 (pip install kaggle)

DATASET    = "shuyangli94/food-com-recipes-and-user-interactions"
TARGET_CSV = "RAW_recipes.csv"
SAVE_DIR   = "./kaggle_data"

# 카글 API로 데이터셋 다운로드 (이미 있으면 스킵)
if not os.path.exists(f"{SAVE_DIR}/{TARGET_CSV}"):
    print(f"다운로드 중: {DATASET}")
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(
        DATASET,
        path=SAVE_DIR,
        unzip=True
    )
    print("다운로드 완료!")
else:
    print("이미 다운로드된 파일 사용")

# CSV 로드
df = pd.read_csv(f"{SAVE_DIR}/{TARGET_CSV}")
print(f"전체 레시피 수: {len(df):,}개")
print(f"컬럼: {list(df.columns)}\n")

# ✅ [수정 1] 조리 15분 이하 필터링 + 샘플 300개
df_simple = (
    df[df["minutes"] <= 15]
    .dropna(subset=["name", "description", "steps"])
    .head(300)
)
print(f"15분 이하 레시피 샘플: {len(df_simple)}개")


# ─────────────────────────────────────────────
# CSV → LangChain Document 변환
# ─────────────────────────────────────────────
def row_to_document(row):
    content = f"""레시피 이름: {row.get('name', '알 수 없음')}
조리 시간: {row.get('minutes', '알 수 없음')}분
설명: {row.get('description', '설명 없음')}
재료: {row.get('ingredients', '재료 정보 없음')}
조리 순서: {row.get('steps', '조리 순서 없음')}"""
    return Document(
        page_content=content,
        metadata={
            "name": str(row.get("name", "")),
            "minutes": str(row.get("minutes", "")),
            "steps": str(row.get("steps", "조리 순서 없음"))  # ✅ [수정 3] steps 메타데이터 추가
        }
    )

documents = [row_to_document(row) for _, row in df_simple.iterrows()]
print(f"Document 변환 완료: {len(documents)}개")


# ─────────────────────────────────────────────
# 2. OpenAI 임베딩 처리
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("[2단계] OpenAI 임베딩 처리 (text-embedding-3-small)")
print("=" * 50)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

print("FAISS 벡터 저장소 생성 중...")
db = FAISS.from_documents(documents, embeddings)
print("FAISS 벡터 저장소 생성 완료!")

sample_text = "간단하게 요리해먹을 수 있는 레시피"
sample_vector = embeddings.embed_query(sample_text)
print(f"\n샘플 임베딩 벡터 (앞 5개): {sample_vector[:5]}")
print(f"벡터 차원: {len(sample_vector)}")


# ─────────────────────────────────────────────
# 3. 검색기 활용 (create_retrieval_chain)
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("[3단계] 검색기 활용 (gpt-3.5-turbo)")
print("=" * 50)

llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-3.5-turbo"
)

# 상위 3개 유사 문서 검색
retriever = db.as_retriever(search_kwargs={"k": 3})

# ✅ [수정 2] 한국어 응답 강제 + [수정 3] 상세 조리 과정 포함 요청
prompt = ChatPromptTemplate.from_template("""
당신은 친절한 요리 도우미입니다.
아래 레시피 정보를 참고해서 질문에 대한 대답을 반드시 한국어로 답해주세요.
각 레시피마다 아래 항목을 빠짐없이 포함해서 알려주세요:
- 레시피 이름:한국어로 번역해주세요
- 조리 시간
- 재료 목록:한국어로 번역해주세요
- 단계별 상세 조리 과정: 한국어로 답해주세요. 조리과정을 요약하지 말고 있는 그대로 한국어로 번역해주세요

{context}

질문: {input}
""")

# 체인 구성
document_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(retriever, document_chain)

# 쿼리 실행
query = "15분 이내로 간단하게 요리해먹을 수 있는 레시피 3개 알려줘."
print(f"\n쿼리: {query}\n")

result = retrieval_chain.invoke({"input": query})

print("=" * 50)
print("[ LLM 답변 ]")
print("=" * 50)
print(result["answer"])

# ✅ [수정 3] 참고 문서에 상세 조리 과정 포함 출력
print("\n" + "=" * 50)
print("[ 참고한 레시피 문서 ]")
print("=" * 50)
for i, doc in enumerate(result["context"], 1):
    name    = doc.metadata.get("name", "알 수 없음")
    minutes = doc.metadata.get("minutes", "알 수 없음")
    steps   = doc.metadata.get("steps", "조리 순서 없음")
    print(f"\n{i}. {name} (조리 시간: {minutes}분)")
    print(f"   [조리 과정]\n   {steps}")
