"""
다이어트 레시피 AI – Streamlit 챗봇 프론트엔드 (연두 파스텔 컬러)

실행:
  streamlit run streamlit_app_pastel.py

  (FastAPI 백엔드가 http://localhost:8000 에서 실행 중이어야 함)
"""

import os
import json
import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# ── 의도 뱃지 매핑 ────────────────────────────────────────────────────────────
INTENT_META = {
    "SPECIFIC_FOOD":  {"label": "특정 음식",  "icon": "🍖", "color": "#3d7a4f", "bg": "#d4edda"},
    "GENERAL_RECIPE": {"label": "조건 기반",  "icon": "🌿", "color": "#2d6a3f", "bg": "#c3e6cb"},
    "OFF_TOPIC":      {"label": "주제 외",    "icon": "💬", "color": "#6c757d", "bg": "#e9ecef"},
}

EXAMPLE_PROMPTS = [
    "떡볶이 먹고 싶어",
    "다이어트 짜장면 레시피 알려줘",
    "두바이쫀득쿠키",
    "포만감 오래가는 저칼로리 메뉴 추천해줘",
    "단백질 높은 식단 추천해줘",
]

PASTEL_CSS = """
<style>
/* 앱 배경 */
.stApp {
    background-color: #f4fdf6;
}

/* 사이드바 배경 */
[data-testid="stSidebar"] {
    background-color: #e8f5eb !important;
}

/* 채팅 입력창 테두리·포커스 */
[data-testid="stChatInput"] {
    border: 1.5px solid #a8d5b5 !important;
    border-radius: 12px !important;
    background-color: #ffffff !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #6dbf85 !important;
    box-shadow: 0 0 0 3px rgba(109,191,133,0.2) !important;
}

/* 전송 버튼 */
[data-testid="stChatInput"] button {
    background-color: #6dbf85 !important;
    border-radius: 8px !important;
}
[data-testid="stChatInput"] button:hover {
    background-color: #52b06e !important;
}

/* 어시스턴트 아바타 */
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
    background-color: #a8d5b5 !important;
}

/* expander 헤더 */
[data-testid="stExpander"] summary {
    background-color: #e8f5eb !important;
    color: #2d6a3f !important;
    border-radius: 8px !important;
}

/* 사이드바 버튼 */
[data-testid="stSidebar"] .stButton > button {
    border: 1px solid #a8d5b5 !important;
    border-radius: 10px !important;
    color: #2d6a3f !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #c3e6cb !important;
    border-color: #6dbf85 !important;
}

/* 메인 헤더 색상 */
h1, h2 {
    color: #2d6a3f !important;
}
</style>
"""


# ── 백엔드 스트리밍 호출 ──────────────────────────────────────────────────────
def call_backend_stream(message: str, history: list[dict]):
    """스트리밍 응답 수신 - (intent, value, is_done) yield"""
    with requests.post(
        f"{BACKEND_URL}/api/chat/stream",
        json={"message": message, "history": history},
        stream=True,
        timeout=60,
    ) as resp:
        resp.raise_for_status()
        intent = "GENERAL_RECIPE"
        full_reply = ""

        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if not line.startswith("data: "):
                continue
            data = json.loads(line[6:])

            if data["type"] == "intent":
                intent = data["value"]
                print(f"🔴 intent 수신: {intent}")
                yield intent, "", False
            elif data["type"] == "chunk":
                full_reply += data["value"]
                yield intent, data["value"], False
            elif data["type"] == "done":
                print(f"🟠 done 수신 - full_reply 길이: {len(full_reply)}자")
                if data["value"]:
                    full_reply = data["value"]
                yield intent, full_reply, True
                return


# ── 응답 텍스트 파싱: 레시피 / 제품정보 분리 ─────────────────────────────────
def split_reply(reply: str) -> tuple[str, str | None]:
    """'---' 구분선 기준으로 레시피 본문과 제품 정보를 분리."""
    if "\n---\n" in reply:
        recipe, products = reply.split("\n---\n", 1)
        return recipe.strip(), products.strip()
    return reply.strip(), None


# ── 의도 뱃지 렌더링 ─────────────────────────────────────────────────────────
def render_intent_badge(intent: str):
    meta = INTENT_META.get(intent, {"label": intent, "icon": "🤖", "color": "#6c757d", "bg": "#e9ecef"})
    st.markdown(
        f"<span style='font-size:12px; color:{meta['color']}; "
        f"background:{meta['bg']}; padding:2px 8px; border-radius:999px;'>"
        f"{meta['icon']} {meta['label']}</span>",
        unsafe_allow_html=True,
    )


# ── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="🥗 다이어트 레시피 AI",
        page_icon="🥗",
        layout="centered",
    )

    st.markdown(PASTEL_CSS, unsafe_allow_html=True)

    WELCOME_MESSAGE = (
        "저는 다이어트 레시피 전문 챗봇입니다 🥗\n"
        "먹고 싶은 음식이나 원하는 식단 조건을 알려주시면 맞춤 레시피를 추천해드릴게요!\n\n"
        "예시: • 떡볶이가 먹고 싶어 • 포만감 오래가는 저칼로리 레시피 알려줘"
    )

    # 사이드바
    with st.sidebar:
        st.title("🥗 다이어트 레시피 AI")
        st.caption("멀티에이전트 기반 맞춤 레시피 추천")
        st.divider()
        st.markdown("**예시 질문**")
        for ex in EXAMPLE_PROMPTS:
            if st.button(ex, use_container_width=True):
                st.session_state.pending_input = ex
        st.divider()
        if st.button("대화 초기화", use_container_width=True):
            st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
            st.session_state.history = []
            st.rerun()
        st.caption(f"백엔드: `{BACKEND_URL}`")

    st.header("🥗 다이어트 레시피 AI 챗봇")
    st.caption("먹고 싶은 음식이나 식단 조건을 알려주세요!")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
    if "history" not in st.session_state:
        st.session_state.history = []
    if "pending_input" not in st.session_state:
        st.session_state.pending_input = None

    # 이전 대화 렌더링
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                recipe, products = split_reply(msg["content"])
                st.markdown(recipe)
                if products:
                    with st.expander("🛒 사용된 제품 구매 정보", expanded=True):
                        for line in products.replace("🛒 사용된 제품 구매 정보\n", "").splitlines():
                            if line.strip():
                                st.markdown(f"- {line.strip()}")
                if msg.get("intent"):
                    render_intent_badge(msg["intent"])
            else:
                st.markdown(msg["content"])

    # 입력 처리
    user_input = st.chat_input("예: 떡볶이 먹고 싶어 / 저칼로리 단백질 레시피")
    if st.session_state.pending_input:
        user_input = st.session_state.pending_input
        st.session_state.pending_input = None

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        reply = ""
        intent = "GENERAL_RECIPE"

        with st.chat_message("assistant"):
            reply_placeholder = st.empty()
            status_placeholder = st.empty()
            full_reply = ""

            try:
                for _intent, value, is_done in call_backend_stream(
                    user_input, st.session_state.history
                ):
                    intent = _intent

                    if intent == "SPECIFIC_FOOD" and not full_reply and not is_done:
                        print("🍖 SPECIFIC_FOOD 로딩 메시지 표시")
                        status_placeholder.markdown("🍖 재료 검색 및 레시피 생성 중...")

                    if not is_done:
                        full_reply += value
                        reply_placeholder.markdown(full_reply + "▌")
                    else:
                        print(f"✅ 스트리밍 완료 - intent: {intent}, reply: {full_reply[:50]}")
                        status_placeholder.empty()
                        if not full_reply:
                            full_reply = value

                recipe, products = split_reply(full_reply)
                reply_placeholder.markdown(recipe)
                if products:
                    with st.expander("🛒 사용된 제품 구매 정보", expanded=True):
                        for line in products.replace("🛒 사용된 제품 구매 정보\n", "").splitlines():
                            if line.strip():
                                st.markdown(f"- {line.strip()}")
                render_intent_badge(intent)
                reply = full_reply

            except requests.exceptions.ConnectionError:
                reply = "백엔드 서버에 연결할 수 없습니다. `uvicorn backend.main:app --reload` 를 먼저 실행해주세요."
                intent = "ERROR"
                st.error(reply)
            except Exception as e:
                reply = f"오류가 발생했습니다: {e}"
                intent = "ERROR"
                st.error(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply, "intent": intent})
        print(f"📌 messages 저장 - intent: {intent}, reply: {reply[:50]}")
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.history.append({"role": "assistant", "content": reply})
        print(f"📌 history 누적 - 총 {len(st.session_state.history)}개")
        st.rerun()


if __name__ == "__main__":
    main()
