#!/usr/bin/env python
# coding: utf-8

# ============================================================
# 🍳 RAG + Tavily 웹서치 에이전트 기반 대화형 레시피 챗봇
# ============================================================
# 실행 방법: streamlit run InteractiveChatbot.py
# 필요 패키지:
#   pip install streamlit streamlit-chat langchain langchain-openai
#              langchain-community chromadb tavily-python python-dotenv
#              pandas faiss-cpu
# ============================================================

import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ── API 키 로드 ──────────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY  = os.getenv("TAVILY_API_KEY")

# ── 경로 설정 ────────────────────────────────────────────────
CSV_PATH        = r"D:\0421\kaggle_data\RAW_recipes.csv"
CHROMA_DIR      = r"D:\0421\chroma_cooking_db"
PROGRESS_FILE   = r"D:\0421\chroma_progress.json"  # 누적 진행상황 저장

# ── 임베딩할 레시피 수 설정 (이 숫자만 바꾸면 누적 추가됨) ──
TARGET_RECIPES  = 2000

# ============================================================
# Streamlit 페이지 설정
# ============================================================
st.set_page_config(
    page_title="🍳 AI 레시피 챗봇",
    page_icon="🍳",
    layout="wide",
)

st.markdown("""
<style>
/* 전체 배경 */
.stApp { background-color: #f8f9fa; color: #1a1a1a; }

/* 사이드바 */
section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e0e0e0;
}
section[data-testid="stSidebar"] * {
    color: #1a1a1a !important;
}
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div {
    color: #1a1a1a !important;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] h5 {
    color: #111111 !important;
    font-weight: 700;
}
/* 사이드바 예시 질문 코드블록 */
section[data-testid="stSidebar"] code {
    background-color: #f0f0f0 !important;
    color: #e94560 !important;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 0.85rem;
}

/* 입력창 */
.stTextInput > div > div > input {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1.5px solid #e94560;
    border-radius: 8px;
}
.stTextInput > div > div > input::placeholder {
    color: #aaaaaa;
}

/* 버튼 */
.stButton > button {
    background-color: #e94560;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: bold;
}
.stButton > button:hover { background-color: #c73652; }

/* 챗 말풍선 공통 */
.chat-bubble {
    padding: 12px 16px;
    border-radius: 12px;
    margin-bottom: 8px;
    max-width: 80%;
    line-height: 1.6;
    font-size: 0.95rem;
}
.user-bubble {
    background-color: #e94560;
    color: white;
    margin-left: auto;
    border-bottom-right-radius: 2px;
}
.bot-bubble {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #e0e0e0;
    border-bottom-left-radius: 2px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.bubble-row { display: flex; margin-bottom: 10px; }
.bubble-row.user { justify-content: flex-end; }
.bubble-row.bot  { justify-content: flex-start; }

/* 출처 뱃지 */
.source-badge {
    display: inline-block;
    background: #fff0f3;
    border: 1px solid #e94560;
    color: #e94560;
    font-size: 0.75rem;
    border-radius: 4px;
    padding: 2px 8px;
    margin: 2px;
}

/* 구분선 */
hr { border-color: #e0e0e0; }

/* 메인 제목 */
h1, h2, h3 { color: #111111; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 세션 상태 초기화
# ============================================================
def init_session():
    defaults = {
        "history":   [],        # [(user_msg, bot_msg), ...]  — ConversationalRetrievalChain용
        "messages":  [],        # [{"role": "user"/"bot", "content": "..."}, ...]  — 화면 렌더링용
        "chain":     None,
        "agent":     None,
        "db_ready":  False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ============================================================
# 벡터 DB & 체인 초기화 (최초 1회, 캐시)
# ============================================================
@st.cache_resource(show_spinner="🔧 AI 엔진 초기화 중...")
def build_agent():
    """RAG 체인 + Tavily 웹서치 에이전트를 빌드하고 반환"""

    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.vectorstores import Chroma
    from langchain.chains import RetrievalQA, ConversationalRetrievalChain
    from langchain.prompts import PromptTemplate
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.tools import Tool
    from langchain_community.tools.tavily_search import TavilySearchResults
    from langchain.agents import AgentExecutor, create_openai_tools_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.memory import ConversationBufferMemory

    # ── LLM ────────────────────────────────────────────────
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.3,
        api_key=OPENAI_API_KEY,
    )
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        api_key=OPENAI_API_KEY,
    )

    # ── 공통: Document 생성 함수 ────────────────────────────
    def make_documents(df_slice):
        documents = []
        for _, row in df_slice.iterrows():
            parts = [
                f"[요리 이름] {row['name']}",
                f"[조리 시간] {int(row['minutes'])}분" if pd.notna(row.get("minutes")) else "",
                f"[재료 ({int(row['n_ingredients'])}가지)] {row['ingredients']}" if pd.notna(row.get("n_ingredients")) else f"[재료] {row['ingredients']}",
                f"[조리 방법 ({int(row['n_steps'])}단계)] {row['steps']}" if pd.notna(row.get("n_steps")) else f"[조리 방법] {row['steps']}",
                f"[설명] {row['description']}" if pd.notna(row.get("description")) else "",
                f"[태그] {row['tags']}" if pd.notna(row.get("tags")) else "",
                f"[영양 정보] {row['nutrition']}" if pd.notna(row.get("nutrition")) else "",
            ]
            content = "\n".join(p for p in parts if p)
            documents.append(Document(
                page_content=content,
                metadata={
                    "recipe_name": row["name"],
                    "minutes": int(row["minutes"]) if pd.notna(row.get("minutes")) else None,
                    "n_ingredients": int(row["n_ingredients"]) if pd.notna(row.get("n_ingredients")) else None,
                }
            ))
        return documents

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    # ── 진행상황 로드 ────────────────────────────────────────
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            progress = json.load(f)
        last_index = progress.get("last_index", 0)
    else:
        last_index = 0

    # ── 벡터 DB 로드 또는 생성 ──────────────────────────────
    BATCH_SIZE = 500  # 한 번에 임베딩할 단위 (로그 출력 간격)

    def embed_in_batches(db, docs, label="임베딩"):
        total = len(docs)
        for i in range(0, total, BATCH_SIZE):
            batch = docs[i:i + BATCH_SIZE]
            db.add_documents(batch)
            done = min(i + BATCH_SIZE, total)
            pct = done / total * 100
            print(f"[{label}] {done}/{total} 청크 완료 ({pct:.1f}%)", flush=True)
        print(f"[{label}] 전체 완료!", flush=True)

    if os.path.exists(CHROMA_DIR):
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

        if TARGET_RECIPES > last_index:
            print(f"\n📂 CSV 읽는 중...", flush=True)
            df = pd.read_csv(CSV_PATH)
            df_clean = df.dropna(subset=["name", "ingredients", "steps"]).reset_index(drop=True)
            df_new = df_clean.iloc[last_index:TARGET_RECIPES]
            print(f"새로 추가할 레시피: {len(df_new)}개 ({last_index+1}번 ~ {last_index+len(df_new)}번)", flush=True)

            if len(df_new) > 0:
                print(f"📄 Document 생성 중...", flush=True)
                new_docs = make_documents(df_new)
                print(f"✂️  청킹 중...", flush=True)
                split_docs = splitter.split_documents(new_docs)
                print(f"총 {len(split_docs)}개 청크 생성됨. 임베딩 시작...", flush=True)

                embed_in_batches(db, split_docs, label="누적 추가")

                with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                    json.dump({
                        "last_index": last_index + len(df_new),
                        "total_recipes": last_index + len(df_new),
                    }, f, ensure_ascii=False, indent=2)
                print(f"💾 완료: 총 {last_index + len(df_new)}개 레시피 저장됨", flush=True)
        else:
            print(f"DB 로드 완료. 현재 {last_index}개 레시피 임베딩됨 (추가 없음)", flush=True)
    else:
        print(f"\n🆕 DB 없음. 최초 생성 시작...", flush=True)
        print(f"📂 CSV 읽는 중...", flush=True)
        df = pd.read_csv(CSV_PATH)
        df_clean = df.dropna(subset=["name", "ingredients", "steps"]).reset_index(drop=True)
        df_init = df_clean.iloc[0:TARGET_RECIPES]
        print(f"레시피 {len(df_init)}개 로드됨. Document 생성 중...", flush=True)

        documents = make_documents(df_init)
        print(f"✂️  청킹 중...", flush=True)
        split_docs = splitter.split_documents(documents)
        print(f"총 {len(split_docs)}개 청크 생성됨. 임베딩 시작...", flush=True)

        first_batch = split_docs[:BATCH_SIZE]
        db = Chroma.from_documents(first_batch, embeddings, persist_directory=CHROMA_DIR)
        print(f"[최초 생성] {len(first_batch)}/{len(split_docs)} 청크 완료 ({len(first_batch)/len(split_docs)*100:.1f}%)", flush=True)

        if len(split_docs) > BATCH_SIZE:
            embed_in_batches(db, split_docs[BATCH_SIZE:], label="최초 생성")

        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "last_index": len(df_init),
                "total_recipes": len(df_init),
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 DB 생성 완료: 총 {len(df_init)}개 레시피", flush=True)

    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

    # ── RAG 프롬프트 ────────────────────────────────────────
    RAG_PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template="""당신은 친절하고 전문적인 요리 챗봇입니다.
아래 Food.com 레시피 정보를 바탕으로 한국어로 답변하세요.

답변 규칙:
- 제공된 레시피 정보에 근거해서 레시피 하나만 답변하세요.
- 레시피 이름(한국어), 재료 목록(한국어), 상세 조리 순서(번호 포함, 한국어)를 알려주세요.
- 데이터에 없는 내용은 "해당 정보가 데이터에 없습니다"라고 답하세요.

[참고 레시피 정보]
{context}

[질문]
{question}

[답변]""",
    )

    # ── RetrievalQA (단순 RAG 조회용) ───────────────────────
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": RAG_PROMPT},
    )

    # ── ConversationalRetrievalChain (대화 이력 유지용) ─────
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )
    conv_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        verbose=False,
    )

    # ── Tavily 웹서치 툴 ────────────────────────────────────
    web_search_tool = TavilySearchResults(
        max_results=3,
        tavily_api_key=TAVILY_API_KEY,
    )

    # ── RAG를 에이전트 툴로 래핑 ────────────────────────────
    rag_tool = Tool(
        name="recipe_database",
        description=(
            "Food.com 레시피 DB를 검색합니다. "
            "일반적인 요리 레시피 질문(재료, 조리법, 영양정보 등)에 사용하세요."
        ),
        func=lambda q: rag_chain.invoke({"query": q})["result"],
    )

    # ── Agent 프롬프트 ───────────────────────────────────────
    agent_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 친절한 요리 전문 AI 챗봇입니다.
사용자의 질문 유형에 따라 아래 도구를 선택하세요:
- 일반 레시피 질문 (재료, 조리법, 영양 등) → recipe_database 툴
- 최신 트렌드/SNS 유행 레시피/최근 뉴스 → tavily_search_results_json 툴 (웹 검색)
- 레시피와 무관한 일상 대화 → 도구 없이 직접 한국어로 친절하게 답변

반드시 한국어로 답변하세요."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # ── 에이전트 생성 ────────────────────────────────────────
    agent_memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
    )
    agent = create_openai_tools_agent(llm, [rag_tool, web_search_tool], agent_prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[rag_tool, web_search_tool],
        memory=agent_memory,
        verbose=False,
        handle_parsing_errors=True,
    )

    return conv_chain, agent_executor


# ============================================================
# 사이드바 UI
# ============================================================
with st.sidebar:
    st.markdown("## 🍳 레시피 챗봇 설정")
    st.markdown("---")

    mode = st.radio(
        "응답 모드 선택",
        ["🤖 에이전트 (RAG + 웹서치)", "📚 RAG 전용 (대화 이력 유지)"],
        index=0,
    )

    st.markdown("---")
    st.markdown("### 사용 방법")
    st.markdown("""
- **에이전트 모드**: 질문 유형에 따라 DB 검색 또는 웹서치 자동 선택
- **RAG 전용 모드**: 이전 대화 문맥을 기억하며 DB에서 레시피 검색
- 예시 질문:
  - `파스타 레시피 알려줘`
  - `최근 SNS에서 유행한 두바이 초콜릿 레시피`
  - `달걀 없이 만드는 케이크`
""")

    st.markdown("---")
    if st.button("🗑️ 대화 초기화"):
        st.session_state["messages"] = []
        st.session_state["history"]  = []
        st.rerun()

    st.markdown("---")
    st.markdown("##### API 연결 상태")
    st.markdown(f"OpenAI : {'✅ 연결됨' if OPENAI_API_KEY else '❌ 키 없음'}")
    st.markdown(f"Tavily  : {'✅ 연결됨' if TAVILY_API_KEY else '❌ 키 없음'}")


# ============================================================
# 메인 UI
# ============================================================
st.markdown("# 🍳 AI 레시피 챗봇")
st.markdown("Food.com 레시피 DB + 실시간 웹서치로 최고의 레시피를 찾아드립니다.")
st.markdown("---")

# 엔진 초기화
try:
    conv_chain, agent_executor = build_agent()
    engine_ok = True
except Exception as e:
    st.error(f"❌ 엔진 초기화 실패: {e}")
    engine_ok = False


# ── 대화 렌더링 ────────────────────────────────────────────
chat_area = st.container()

with chat_area:
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="bubble-row user"><div class="chat-bubble user-bubble">🙋 {msg["content"]}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            content = msg["content"]
            sources_html = ""
            if msg.get("sources"):
                badges = "".join(
                    f'<span class="source-badge">📄 {s}</span>'
                    for s in msg["sources"]
                )
                sources_html = f"<br><br><small>📚 참고 레시피: {badges}</small>"
            tool_html = ""
            if msg.get("tool"):
                tool_html = f'<br><small style="color:#aaa;">🔧 사용 도구: {msg["tool"]}</small>'
            st.markdown(
                f'<div class="bubble-row bot"><div class="chat-bubble bot-bubble">🍳 {content}{sources_html}{tool_html}</div></div>',
                unsafe_allow_html=True,
            )


# ── 입력창 ─────────────────────────────────────────────────
st.markdown("---")
col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.text_input(
        "질문을 입력하세요",
        placeholder="예: 파스타 레시피 알려줘 / 최근 유행하는 레시피는?",
        key="user_input",
        label_visibility="collapsed",
    )
with col2:
    send = st.button("전송 ➤", use_container_width=True)


# ── 응답 처리 ──────────────────────────────────────────────
if send and user_input.strip() and engine_ok:
    query = user_input.strip()

    # 사용자 메시지 추가
    st.session_state["messages"].append({"role": "user", "content": query})

    with st.spinner("🍳 레시피를 찾고 있습니다..."):
        try:
            if "에이전트" in mode:
                # ── 에이전트 모드 ──────────────────────────────
                result = agent_executor.invoke({"input": query})
                answer = result["output"]

                # 어떤 툴을 사용했는지 파악 (intermediate_steps)
                tool_used = None
                steps = result.get("intermediate_steps", [])
                if steps:
                    tool_used = steps[0][0].tool if steps else None

                tool_label = {
                    "recipe_database": "Food.com DB 검색",
                    "tavily_search_results_json": "웹 실시간 검색",
                }.get(tool_used, "직접 답변")

                st.session_state["messages"].append({
                    "role": "bot",
                    "content": answer,
                    "tool": tool_label,
                    "sources": [],
                })

            else:
                # ── RAG 전용 모드 (대화 이력 유지) ────────────
                result = conv_chain.invoke({
                    "question": query,
                    "chat_history": st.session_state["history"],
                })
                answer = result["answer"]
                source_docs = result.get("source_documents", [])
                sources = list({
                    doc.metadata.get("recipe_name", "알 수 없음")
                    for doc in source_docs
                })

                # 대화 이력 갱신
                st.session_state["history"].append((query, answer))

                st.session_state["messages"].append({
                    "role": "bot",
                    "content": answer,
                    "tool": "Food.com DB 검색",
                    "sources": sources,
                })

        except Exception as e:
            st.session_state["messages"].append({
                "role": "bot",
                "content": f"⚠️ 오류가 발생했습니다: {str(e)}",
                "sources": [],
            })

    st.rerun()
