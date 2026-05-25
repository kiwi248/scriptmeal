"""
다이어트 레시피 AI – Streamlit 챗봇 프론트엔드

실행:
  streamlit run streamlit_app.py

  (FastAPI 백엔드가 http://localhost:8000 에서 실행 중이어야 함)
"""

import os
import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# ── 의도 뱃지 매핑 ────────────────────────────────────────────────────────────
INTENT_META = {
    "SPECIFIC_FOOD":  {"label": "특정 음식",  "icon": "🍖", "color": "#2563eb"},
    "GENERAL_RECIPE": {"label": "조건 기반",  "icon": "🥗", "color": "#16a34a"},
    "OFF_TOPIC":      {"label": "주제 외",    "icon": "💬", "color": "#9ca3af"},
}

EXAMPLE_PROMPTS = [
    "떡볶이 먹고 싶어",
    "다이어트 짜장면 레시피 알려줘",
    "포만감 오래가는 저칼로리 점심 추천해줘",
    "단백질 높은 아침 식사 추천해줘",
]


# ── 백엔드 호출 ───────────────────────────────────────────────────────────────
def call_backend(message: str, history: list[dict]) -> dict:
    print(f"🔴 백엔드 호출 시작 - 메시지: {message}")
    resp = requests.post(
        f"{BACKEND_URL}/api/chat",
        json={"message": message, "history": history},
        timeout=60,
    )
    resp.raise_for_status()
    print(f"🔴 백엔드 호출 완료 - 응답: {resp.json()}")
    return resp.json()


# ── 응답 텍스트 파싱: 레시피 / 제품정보 분리 ─────────────────────────────────
def split_reply(reply: str) -> tuple[str, str | None]:
    """'---' 구분선 기준으로 레시피 본문과 제품 정보를 분리."""
    print(f"🟠 split_reply 실행 - 입력: {reply[:30]}")
    if "\n---\n" in reply:
        recipe, products = reply.split("\n---\n", 1)
        print("🟠 레시피/제품정보 분리 완료")
        return recipe.strip(), products.strip()
    print("🟠 제품정보 없음 - 레시피만 반환")
    return reply.strip(), None


# ── 의도 뱃지 렌더링 ─────────────────────────────────────────────────────────
def render_intent_badge(intent: str):
    meta = INTENT_META.get(intent, {"label": intent, "icon": "🤖", "color": "#6b7280"})
    st.markdown(
        f"<span style='font-size:12px; color:{meta['color']}; "
        f"background:#f3f4f6; padding:2px 8px; border-radius:999px;'>"
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

    # 세션 상태 초기화
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
            st.session_state.messages = [
                {"role": "assistant", "content": WELCOME_MESSAGE}
            ]
            st.session_state.history = []
            st.rerun()
        st.caption(f"백엔드: `{BACKEND_URL}`")

    st.header("🥗 다이어트 레시피 AI 챗봇")
    st.caption("먹고 싶은 음식이나 식단 조건을 알려주세요!")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MESSAGE}
        ]
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

    # 사이드바 버튼으로 입력된 텍스트 처리
    user_input = st.chat_input("예: 떡볶이 먹고 싶어 / 저칼로리 단백질 레시피")
    if st.session_state.pending_input:
        user_input = st.session_state.pending_input
        st.session_state.pending_input = None

    if user_input:
        # 사용자 메시지 표시 및 저장
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 봇 응답
        with st.chat_message("assistant"):
            with st.spinner("레시피 생성 중... 🍳"):
                try:
                    result = call_backend(user_input, st.session_state.history)
                    reply: str = result["reply"]
                    intent: str = result["intent"]

                    recipe, products = split_reply(reply)
                    st.markdown(recipe)
                    if products:
                        with st.expander("🛒 사용된 제품 구매 정보", expanded=True):
                            for line in products.replace("🛒 사용된 제품 구매 정보\n", "").splitlines():
                                if line.strip():
                                    st.markdown(f"- {line.strip()}")
                    render_intent_badge(intent)

                except requests.exceptions.ConnectionError:
                    reply = "백엔드 서버에 연결할 수 없습니다. `uvicorn backend.main:app --reload` 를 먼저 실행해주세요."
                    intent = "ERROR"
                    st.error(reply)
                except Exception as e:
                    reply = f"오류가 발생했습니다: {e}"
                    intent = "ERROR"
                    st.error(reply)

        # 히스토리 저장
        # 1. messages → 화면에 보여주기 위한 저장
        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "intent": intent}
        )
        print("📌 messages → 화면에 보여주기 위한 저장:", reply[:50])
        # 2. history → 백엔드 LLM에게 보내기 위한 저장
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.history.append({"role": "assistant", "content": reply})
        print("📌 history 저장 완료:", st.session_state.history)
        st.rerun()


if __name__ == "__main__":
    main()
