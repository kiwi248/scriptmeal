"""
다이어트 레시피 AI – Streamlit 챗봇
실행: streamlit run frontend/app.py
"""

import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"

INTENT_LABELS = {
    "SPECIFIC_FOOD": "🍽️ 특정 음식",
    "GENERAL_RECIPE": "🌤️ 날씨/조건 기반",
    "OFF_TOPIC": "💬 주제 외",
}

st.set_page_config(
    page_title="다이어트 레시피 AI",
    page_icon="🥗",
    layout="centered",
)

st.title("🥗 다이어트 레시피 AI")
st.caption("먹고 싶은 음식이나 원하는 식단 조건을 입력하면 맞춤 레시피를 추천해드립니다!")

# ── 세션 초기화 ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages: list[dict] = []

if "intents" not in st.session_state:
    st.session_state.intents: list[str] = []

# ── 대화 히스토리 렌더링 ──────────────────────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and i // 2 < len(st.session_state.intents):
            intent = st.session_state.intents[i // 2]
            st.caption(INTENT_LABELS.get(intent, intent))
        st.markdown(msg["content"])

# ── 입력 처리 ────────────────────────────────────────────────────────────────
if user_input := st.chat_input("예: 떡볶이 레시피 알려줘 / 포만감 있는 저칼로리 식단 추천"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("레시피 생성 중..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/api/chat",
                    json={
                        "message": user_input,
                        "history": st.session_state.messages[:-1],
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                reply = data["reply"]
                intent = data["intent"]
            except requests.exceptions.ConnectionError:
                reply = "백엔드 서버에 연결할 수 없습니다. `uvicorn backend.main:app --reload` 명령으로 서버를 실행해주세요."
                intent = "OFF_TOPIC"
            except Exception as e:
                reply = f"오류가 발생했습니다: {e}"
                intent = "OFF_TOPIC"

        st.caption(INTENT_LABELS.get(intent, intent))
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.intents.append(intent)

# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("사용 예시")
    examples = [
        "떡볶이 다이어트 레시피 알려줘",
        "짜장면 저칼로리 버전 만들기",
        "포만감 오래가는 아침 식사 추천",
        "단백질 높은 저녁 메뉴 뭐가 좋을까?",
        "오늘 날씨에 맞는 다이어트 식단 추천",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state._example_input = ex
            st.rerun()

    st.divider()
    if st.button("대화 초기화", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.intents = []
        st.rerun()

    st.divider()
    st.caption(f"백엔드: `{BACKEND_URL}`")

# ── 사이드바 예시 버튼 처리 ──────────────────────────────────────────────────
if hasattr(st.session_state, "_example_input"):
    example = st.session_state._example_input
    del st.session_state._example_input

    st.session_state.messages.append({"role": "user", "content": example})

    with st.spinner("레시피 생성 중..."):
        try:
            resp = requests.post(
                f"{BACKEND_URL}/api/chat",
                json={
                    "message": example,
                    "history": st.session_state.messages[:-1],
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["reply"]
            intent = data["intent"]
        except Exception as e:
            reply = f"오류가 발생했습니다: {e}"
            intent = "OFF_TOPIC"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.intents.append(intent)
    st.rerun()
