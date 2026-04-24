########################
#사용자 질문
#    ↓
#create_openai_tools_agent (GPT가 판단)
#    ├─ "일반 레시피 질문이다" → recipe_database 툴 (ChromaDB 검색)
#    └─ "최신/트렌드 질문이다" → tavily_search_results_json 툴 (웹 검색)
#    ↓
#AgentExecutor가 선택된 툴 실행 후 답변 종합
################

import pandas as pd
import os
from dotenv import load_dotenv

# ✅ .env 파일에서 API 키 로드
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")  # .env의 OPENAI_API_KEY 값을 변수에 담기

# ─────────────────────────────────────────
# 1. CSV 로드
# ─────────────────────────────────────────
CSV_PATH = r"C:\0421\kaggle_data\RAW_recipes.csv"

df = pd.read_csv(CSV_PATH)
print(f"총 레시피 수: {len(df):,}개")
print(f"컬럼 목록: {df.columns.tolist()}")

# ─────────────────────────────────────────
# 2. Document 변환
# ─────────────────────────────────────────
from langchain.schema import Document

MAX_ROWS = 2000
df_clean = df.dropna(subset=["name", "ingredients", "steps"]).head(MAX_ROWS).copy()
print(f"사용할 레시피 수: {len(df_clean):,}개")

documents = []
for _, row in df_clean.iterrows():
    parts = [
        f"[요리 이름] {row['name']}",
        f"[조리 시간] {int(row['minutes'])}분" if pd.notna(row.get('minutes')) else "",
        f"[재료 ({int(row['n_ingredients'])}가지)] {row['ingredients']}" if pd.notna(row.get('n_ingredients')) else f"[재료] {row['ingredients']}",
        f"[조리 방법 ({int(row['n_steps'])}단계)] {row['steps']}" if pd.notna(row.get('n_steps')) else f"[조리 방법] {row['steps']}",
        f"[설명] {row['description']}" if pd.notna(row.get('description')) else "",
        f"[태그] {row['tags']}" if pd.notna(row.get('tags')) else "",
        f"[영양 정보] {row['nutrition']}" if pd.notna(row.get('nutrition')) else "",
    ]
    content = "\n".join(p for p in parts if p)
    doc = Document(
        page_content=content,
        metadata={
            "recipe_name": row["name"],
            "minutes": int(row["minutes"]) if pd.notna(row.get("minutes")) else None,
            "n_ingredients": int(row["n_ingredients"]) if pd.notna(row.get("n_ingredients")) else None,
        }
    )
    documents.append(doc)

print(f"변환된 Document 수: {len(documents):,}개")
print("\n--- 첫 번째 Document 예시 ---")
print(documents[0].page_content[:600])

# ─────────────────────────────────────────
# 3. 텍스트 청킹
# ─────────────────────────────────────────
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
split_docs = text_splitter.split_documents(documents)
print(f"청킹 후 총 청크 수: {len(split_docs):,}개")

# ─────────────────────────────────────────
# 4. 임베딩 & 벡터 DB
# ─────────────────────────────────────────
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=API_KEY)

CHROMA_DIR = "./chroma_cooking_db"

# ✅ 처음 실행할 때만 사용 (DB 생성)
#print("⏳ 벡터 DB 생성 중... (수 분 소요)")
#db = Chroma.from_documents(split_docs, embeddings, persist_directory=CHROMA_DIR)
print(f"✅ 벡터 DB 저장 완료 → {CHROMA_DIR}")

# ──────────────────────────────────────────────────────
# ※ 두 번째 실행부터는 위 두 줄을 주석 처리하고
#   아래 줄의 주석을 해제하세요 (DB 재생성 방지)
db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
print("✅ 기존 벡터 DB 불러오기 완료")
 

# ─────────────────────────────────────────
# 5. RAG 체인 구성
# ─────────────────────────────────────────
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0.3,
    api_key=API_KEY
)

COOKING_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
당신은 친절하고 전문적인 요리 챗봇입니다.
아래에 제공된 Food.com 레시피 정보를 바탕으로 사용자의 질문에 한국어로 답변하세요.

답변 규칙:
- 제공된 레시피 정보에 근거해서만 레시피 하나만 답변하세요.
- 레시피 이름을 알려주세요. 한국어로 알려주세요.
- 재료 목록을 알려주세요. 모두 한국어로 알려주세요.
- 상세 조리 순서를 번호를 붙여 설명하세요. 모두 한국어로 알려주세요.
- 데이터에 없는 내용은 "해당 정보가 데이터에 없습니다"라고 솔직히 답하세요.

[참고 레시피 정보]
{context}

[질문]
{question}

[답변]
"""
)

retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})

cooking_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": COOKING_PROMPT}
)
print("✅ 요리 RAG 체인 구성 완료!")

# ─────────────────────────────────────────
# 6. 질문 함수
# ─────────────────────────────────────────
def ask_cooking_bot(question: str):
    print(f"\n🙋 질문: {question}")
    print("=" * 60)
    result = cooking_chain.invoke({"query": question})
    print(f"🍳 답변:\n{result['result']}")
    print("-" * 60)
    print("📚 참고된 레시피:")
    for i, doc in enumerate(result["source_documents"], 1):
        name    = doc.metadata.get("recipe_name", "알 수 없음")
        minutes = doc.metadata.get("minutes")
        n_ing   = doc.metadata.get("n_ingredients")
        info  = f" | ⏱ {minutes}분" if minutes else ""
        info += f" | 🥕 재료 {n_ing}가지" if n_ing else ""
        print(f"  {i}. {name}{info}")
    return result["result"]


#########################################

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os

# ✅ .env에 TAVILY_API_KEY 추가 필요 (무료: tavily.com에서 발급)

# 1. 웹 검색 툴
web_search_tool = TavilySearchResults(max_results=3)

# 2. 기존 RAG를 툴로 감싸기
from langchain.tools import Tool

rag_tool = Tool(
    name="recipe_database",
    description="Food.com의 레시피 DB를 검색합니다. 일반적인 요리 레시피 질문에 사용하세요.",
    func=lambda q: cooking_chain.invoke({"query": q})["result"]
)

# 3. Agent용 프롬프트
prompt = ChatPromptTemplate.from_messages([
    ("system", """당신은 친절한 요리 챗봇입니다.
- 일반 레시피 질문 → recipe_database 툴 사용
- 최신 트렌드/SNS 유행 레시피 → tavily_search_results_json 툴로 웹 검색
- 한국어로 답변하세요."""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 4. Agent 생성
tools = [rag_tool, web_search_tool]

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 5. 실행 함수
def ask_bot(question: str):
    print(f"\n🙋 질문: {question}")
    print("=" * 60)
    result = agent_executor.invoke({"input": question})
    print(f"🍳 답변:\n{result['output']}")
    return result['output']

# 테스트
#ask_bot("최근 SNS에서 유행한 두바이 초콜릿 레시피 알려줘")
#ask_bot("Tell me a recipe using Pringles potato chips")
#ask_bot("안녕? 오늘 날씨가 좋지?")
#ask_bot("버터떡 레시피 알려줘")
#ask_bot("두바이쫀득쿠키 레시피 알려줘")
#ask_bot("초코블럭 프링글스 레시피 알려줘")
ask_bot("환단고기")