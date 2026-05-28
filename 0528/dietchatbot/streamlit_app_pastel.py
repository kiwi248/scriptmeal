"""
다이어트 레시피 AI – Streamlit 챗봇 프론트엔드 (연두 파스텔 컬러)

실행:
  streamlit run streamlit_app_pastel.py

  (FastAPI 백엔드가 http://localhost:8000 에서 실행 중이어야 함)
"""

import os
import json
import uuid
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
    "두바이쫀득쿠키",
    "SNS 유행음식 밤티말빵",
    "SNS유행 홍콩식 디저트 망고 사고(Mango Sago)",
    "떡볶이 먹고 싶어",
    "다이어트 짜장면 레시피 알려줘",
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

WELCOME_MESSAGE = (
    "저는 다이어트 레시피 전문 챗봇입니다 🥗\n"
    "먹고 싶은 음식이나 원하는 식단 조건을 알려주시면 맞춤 레시피를 추천해드릴게요!\n\n"
    "예시: • 떡볶이가 먹고 싶어 • 포만감 오래가는 저칼로리 레시피 알려줘"
)


# ── 백엔드 API 헬퍼 ───────────────────────────────────────────────────────────

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


def _api_save_history(session_id: str, user_msg: str, recipe_reply: str, intent: str):
    try:
        print(f"💾 히스토리 저장 요청 - session: {session_id[:8]}, intent: {intent}, msg: {user_msg[:20]}")
        resp = requests.post(
            f"{BACKEND_URL}/api/history",
            json={"session_id": session_id, "user_message": user_msg,
                  "recipe_reply": recipe_reply, "intent": intent},
            timeout=5,
        )
        print(f"💾 히스토리 저장 응답 - status: {resp.status_code}")
    except Exception as e:
        print(f"❌ 히스토리 저장 실패: {e}")


def _api_save_favorite(session_id: str, user_msg: str, recipe_reply: str, intent: str) -> bool:
    try:
        print(f"⭐ 즐겨찾기 저장 요청 - session: {session_id[:8]}, msg: {user_msg[:20]}")
        resp = requests.post(
            f"{BACKEND_URL}/api/favorites",
            json={"session_id": session_id, "user_message": user_msg,
                  "recipe_reply": recipe_reply, "intent": intent},
            timeout=5,
        )
        print(f"⭐ 즐겨찾기 저장 응답 - status: {resp.status_code}, ok: {resp.ok}")
        return resp.ok
    except Exception as e:
        print(f"❌ 즐겨찾기 저장 실패: {e}")
        return False


def _api_load_history(session_id: str) -> list[dict]:
    try:
        resp = requests.get(
            f"{BACKEND_URL}/api/history",
            params={"session_id": session_id},
            timeout=5,
        )
        return resp.json() if resp.ok else []
        print(f"📋 히스토리 조회 - {len(result)}건 (status: {resp.status_code})")
        return result
    except Exception as e:
        print(f"❌ 히스토리 조회 실패: {e}")
        return []


def _api_load_favorites(session_id: str) -> list[dict]:
    try:
        resp = requests.get(
            f"{BACKEND_URL}/api/favorites",
            params={"session_id": session_id},
            timeout=5,
        )
        return resp.json() if resp.ok else []
        print(f"⭐ 즐겨찾기 조회 - {len(result)}건 (status: {resp.status_code})")
        return result
    except Exception as e:
        print(f"❌ 즐겨찾기 조회 실패: {e}")
        return []


def _api_delete_favorite(fav_id: int) -> bool:
    try:
        print(f"🗑️ 즐겨찾기 삭제 요청 - id: {fav_id}")
        resp = requests.delete(f"{BACKEND_URL}/api/favorites/{fav_id}", timeout=5)
        print(f"🗑️ 즐겨찾기 삭제 응답 - status: {resp.status_code}, ok: {resp.ok}")
        return resp.ok
    except Exception as e:
        print(f"❌ 즐겨찾기 삭제 실패: {e}")
        return False


# ── 공통 렌더링 유틸 ─────────────────────────────────────────────────────────

def split_reply(reply: str) -> tuple[str, str | None]:
    """'---' 구분선 기준으로 레시피 본문과 제품 정보를 분리."""
    if "\n---\n" in reply:
        recipe, products = reply.split("\n---\n", 1)
        return recipe.strip(), products.strip()
    return reply.strip(), None


def render_intent_badge(intent: str):
    meta = INTENT_META.get(intent, {"label": intent, "icon": "🤖", "color": "#6c757d", "bg": "#e9ecef"})
    st.markdown(
        f"<span style='font-size:12px; color:{meta['color']}; "
        f"background:{meta['bg']}; padding:2px 8px; border-radius:999px;'>"
        f"{meta['icon']} {meta['label']}</span>",
        unsafe_allow_html=True,
    )


def render_recipe_card(user_message: str, recipe_reply: str, intent: str):
    """히스토리/즐겨찾기에서 레시피 전체를 표시."""
    st.caption(f"**질문:** {user_message}")
    recipe, products = split_reply(recipe_reply)
    st.markdown(recipe)
    if products:
        st.divider()
        st.markdown("**🛒 사용된 제품**")
        for line in products.replace("🛒 사용된 제품 구매 정보\n", "").splitlines():
            if line.strip():
                st.markdown(f"- {line.strip()}")


def _created_label(iso_str: str) -> str:
    return iso_str[:16].replace("T", " ") if iso_str else ""


# ── 히스토리 뷰 ──────────────────────────────────────────────────────────────

def render_history_view(session_id: str):
    st.header("📋 레시피 히스토리")
    st.caption("이번 세션에서 받은 레시피 목록입니다.")

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 새로고침", key="refresh_history"):
            st.session_state.pop("history_cache", None)

    if "history_cache" not in st.session_state:
        with st.spinner("불러오는 중..."):
            st.session_state.history_cache = _api_load_history(session_id)

    items: list[dict] = st.session_state.history_cache

    if not items:
        st.info("아직 레시피 히스토리가 없습니다. 채팅에서 레시피를 요청해보세요!")
        return

    for item in items:
        meta = INTENT_META.get(item["intent"], {"icon": "🤖"})
        label = f"{meta['icon']} {item['user_message'][:28]}  ·  {_created_label(item.get('created_at', ''))}"

        with st.expander(label, expanded=False):
            render_recipe_card(item["user_message"], item["recipe_reply"], item["intent"])
            st.divider()
            if st.button("⭐ 즐겨찾기에 추가", key=f"hist_fav_{item['id']}"):
                ok = _api_save_favorite(
                    session_id, item["user_message"], item["recipe_reply"], item["intent"]
                )
                st.session_state.pop("favorites_cache", None)
                if ok:
                    st.toast("⭐ 즐겨찾기에 추가했습니다!")
                else:
                    st.toast("저장에 실패했습니다. 다시 시도해주세요.")


# ── 즐겨찾기 뷰 ──────────────────────────────────────────────────────────────

def render_favorites_view(session_id: str):
    st.header("⭐ 즐겨찾기")
    st.caption("저장한 레시피 목록입니다.")

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 새로고침", key="refresh_favorites"):
            st.session_state.pop("favorites_cache", None)

    if "favorites_cache" not in st.session_state:
        with st.spinner("불러오는 중..."):
            st.session_state.favorites_cache = _api_load_favorites(session_id)

    items: list[dict] = st.session_state.favorites_cache

    if not items:
        st.info("아직 즐겨찾기가 없습니다. 채팅에서 마음에 드는 레시피를 ⭐로 저장해보세요!")
        return

    for item in items:
        meta = INTENT_META.get(item["intent"], {"icon": "🤖"})
        label = f"{meta['icon']} {item['user_message'][:28]}  ·  {_created_label(item.get('created_at', ''))}"

        with st.expander(label, expanded=False):
            render_recipe_card(item["user_message"], item["recipe_reply"], item["intent"])
            st.divider()
            if st.button("🗑️ 즐겨찾기 삭제", key=f"del_fav_{item['id']}", type="secondary"):
                ok = _api_delete_favorite(item["id"])
                st.session_state.pop("favorites_cache", None)
                if ok:
                    st.toast("즐겨찾기에서 삭제했습니다.")
                    st.rerun()
                else:
                    st.toast("삭제에 실패했습니다.")


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="🥗 다이어트 레시피 AI",
        page_icon="🥗",
        layout="centered",
    )
    st.markdown(PASTEL_CSS, unsafe_allow_html=True)

    # ── 세션 초기화 ─────────────────────────────────────────────────────────
    FIXED_SESSION_ID = "my-session"  # 고정 ID

    if "session_id" not in st.session_state:
        params = st.query_params
        if "session_id" in params:
            st.session_state.session_id = params["session_id"]
        else:
            st.session_state.session_id = FIXED_SESSION_ID
            st.query_params["session_id"] = FIXED_SESSION_ID
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
    if "history" not in st.session_state:
        st.session_state.history = []
    if "pending_input" not in st.session_state:
        st.session_state.pending_input = None
    if "view" not in st.session_state:
        st.session_state.view = "chat"
    if "favorited_indices" not in st.session_state:
        st.session_state.favorited_indices = set()

    session_id = st.session_state.session_id
    view = st.session_state.view

    # ── 사이드바 ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🥗 다이어트 레시피 AI")
        st.caption("멀티에이전트 기반 맞춤 레시피 추천")
        st.divider()

        # 내비게이션
        if st.button(
            "💬 채팅",
            use_container_width=True,
            type="primary" if view == "chat" else "secondary",
        ):
            st.session_state.view = "chat"
            st.rerun()

        if st.button(
            "📋 레시피 히스토리",
            use_container_width=True,
            type="primary" if view == "history" else "secondary",
        ):
            st.session_state.view = "history"
            st.session_state.pop("history_cache", None)
            st.rerun()

        if st.button(
            "⭐ 즐겨찾기",
            use_container_width=True,
            type="primary" if view == "favorites" else "secondary",
        ):
            st.session_state.view = "favorites"
            st.session_state.pop("favorites_cache", None)
            st.rerun()

        st.divider()

        if view == "chat":
            st.markdown("**예시 질문**")
            for ex in EXAMPLE_PROMPTS:
                if st.button(ex, use_container_width=True):
                    st.session_state.pending_input = ex
            st.divider()

        if st.button("대화 초기화", use_container_width=True):
            st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
            st.session_state.history = []
            st.session_state.favorited_indices = set()
            st.session_state.view = "chat"
            st.rerun()

        st.caption(f"백엔드: `{BACKEND_URL}`")

    # ── 메인 콘텐츠 ──────────────────────────────────────────────────────────

    if view == "history":
        render_history_view(session_id)
        return

    if view == "favorites":
        render_favorites_view(session_id)
        return

    # ── 채팅 뷰 ──────────────────────────────────────────────────────────────

    st.header("🥗 다이어트 레시피 AI 챗봇")
    st.caption("먹고 싶은 음식이나 식단 조건을 알려주세요!")

    # 이전 대화 렌더링
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                recipe, products = split_reply(msg["content"])
                st.markdown(recipe)
                if products:
                    with st.expander("🛒 사용된 제품 구매 정보", expanded=True):
                        for line in products.replace("🛒 사용된 제품 구매 정보\n", "").splitlines():
                            if line.strip():
                                st.markdown(f"- {line.strip()}")

                intent = msg.get("intent", "")
                if intent and intent not in ("ERROR",):
                    badge_col, fav_col = st.columns([5, 2])
                    with badge_col:
                        render_intent_badge(intent)
                    with fav_col:
                        if intent not in ("OFF_TOPIC",):
                            is_faved = i in st.session_state.favorited_indices
                            if is_faved:
                                st.markdown(
                                    "<span style='font-size:12px; color:#2d6a3f;'>✅ 저장됨</span>",
                                    unsafe_allow_html=True,
                                )
                            else:
                                if st.button("⭐ 저장", key=f"fav_{i}", help="즐겨찾기에 추가"):
                                    # 직전 유저 메시지 찾기
                                    user_msg = ""
                                    for j in range(i - 1, -1, -1):
                                        if st.session_state.messages[j]["role"] == "user":
                                            user_msg = st.session_state.messages[j]["content"]
                                            break
                                    ok = _api_save_favorite(session_id, user_msg, msg["content"], intent)
                                    if ok:
                                        st.session_state.favorited_indices.add(i)
                                        st.session_state.pop("favorites_cache", None)
                                        st.toast("⭐ 즐겨찾기에 추가했습니다!")
                                    else:
                                        st.toast("저장에 실패했습니다. 다시 시도해주세요.")
                elif intent:
                    render_intent_badge(intent)
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

        # 레시피 응답만 히스토리 DB에 저장
        if intent not in ("ERROR", "OFF_TOPIC"):
            _api_save_history(session_id, user_input, reply, intent)
            st.session_state.pop("history_cache", None)

        st.rerun()


if __name__ == "__main__":
    main()
