/* ── 상태 ────────────────────────────────────────────────── */
const API_BASE   = "http://localhost:8000";
let currentMode  = "agent";
let sessionId    = crypto.randomUUID();
let isLoading    = false;

/* ── 초기화 ──────────────────────────────────────────────── */
window.addEventListener("DOMContentLoaded", () => {
  checkApiStatus();
  document.getElementById("userInput").focus();
});

/* ── 모드 전환 ───────────────────────────────────────────── */
function setMode(mode, btn) {
  currentMode = mode;
  document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  console.log("[UI] 모드 전환:", mode);
}

/* ── 예시 질문 클릭 ──────────────────────────────────────── */
function fillExample(el) {
  const input = document.getElementById("userInput");
  input.value = el.textContent.trim();
  autoResize(input);
  input.focus();
}

/* ── 대화 초기화 ─────────────────────────────────────────── */
function clearChat() {
  sessionId = crypto.randomUUID();
  const area = document.getElementById("chatArea");
  area.innerHTML = `
    <div class="empty-state" id="emptyState">
      <div class="icon">🍽️</div>
      <p>궁금한 레시피나 요리 방법을 질문해 보세요!</p>
    </div>`;
  console.log("[UI] 대화 초기화 — 새 sessionId:", sessionId);
}

/* ── textarea 자동 높이 ──────────────────────────────────── */
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

/* ── Enter 키 처리 (Shift+Enter = 줄바꿈) ───────────────── */
function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

/* ── API 상태 확인 ───────────────────────────────────────── */
async function checkApiStatus() {
  const el = document.getElementById("apiStatus");
  try {
    const res  = await fetch(`${API_BASE}/api/recipes/status`);
    const data = await res.json();
    el.innerHTML = `
      <span class="dot-ok">●</span> 서버 연결됨<br>
      임베딩: ${data.last_index.toLocaleString()} / ${data.target_recipes.toLocaleString()} 레시피<br>
      컬렉션: ${data.collection_count.toLocaleString()} 문서`;
    console.log("[Status] DB 상태:", data);
  } catch {
    el.innerHTML = `<span class="dot-err">●</span> 서버 연결 실패`;
    console.warn("[Status] 서버 연결 실패");
  }
}

/* ── 메시지 전송 ─────────────────────────────────────────── */
async function sendMessage() {
  if (isLoading) return;

  const input = document.getElementById("userInput");
  const query = input.value.trim();
  if (!query) return;

  // 빈 상태 제거
  const emptyState = document.getElementById("emptyState");
  if (emptyState) emptyState.remove();

  // 사용자 버블 추가
  appendBubble("user", query);

  input.value = "";
  autoResize(input);

  // 로딩 상태
  setLoading(true);
  const typingId = showTyping();

  console.log("[Chat] 전송 — mode:", currentMode, "| session:", sessionId, "| query:", query);

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        message:    query,
        mode:       currentMode,
        session_id: sessionId,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    console.log("[Chat] 응답 수신:", data);

    removeTyping(typingId);
    appendBotBubble(data);

  } catch (err) {
    console.error("[Chat] 오류:", err);
    removeTyping(typingId);
    appendBubble("bot", `⚠️ 오류: ${err.message}`, null, null, null);
  } finally {
    setLoading(false);
  }
}

/* ── 로딩 상태 토글 ──────────────────────────────────────── */
function setLoading(state) {
  isLoading = state;
  const btn = document.getElementById("sendBtn");
  btn.disabled = state;
  btn.textContent = state ? "⏳" : "전송 ➤";
}

/* ── 타이핑 인디케이터 ───────────────────────────────────── */
function showTyping() {
  const id  = "typing-" + Date.now();
  const row = document.createElement("div");
  row.className = "bubble-row bot";
  row.id = id;
  row.innerHTML = `
    <div class="typing-indicator">
      <span></span><span></span><span></span>
    </div>`;
  document.getElementById("chatArea").appendChild(row);
  scrollToBottom();
  return id;
}
function removeTyping(id) {
  document.getElementById(id)?.remove();
}

/* ── 사용자 버블 추가 ────────────────────────────────────── */
function appendBubble(role, text) {
  const area = document.getElementById("chatArea");
  const row  = document.createElement("div");
  row.className = `bubble-row ${role}`;
  row.innerHTML = `<div class="bubble ${role}">${escapeHtml(text)}</div>`;
  area.appendChild(row);
  scrollToBottom();
}

/* ── 봇 버블 추가 (메타 + 디버그 패널) ──────────────────── */
function appendBotBubble(data) {
  const area      = document.getElementById("chatArea");
  const row       = document.createElement("div");
  row.className   = "bubble-row bot";

  // 소스 배지
  const badges = (data.sources || [])
    .map(s => `<span class="badge">📄 ${escapeHtml(s)}</span>`)
    .join("");

  // 툴 레이블
  const toolHtml = data.tool_used
    ? `<span class="badge">🔧 ${escapeHtml(data.tool_used)}</span>`
    : "";

  // 디버그 패널
  const debugId  = "debug-" + Date.now();
  const debugHtml = buildDebugHtml(data.debug_info, debugId);

  row.innerHTML = `
    <div>
      <div class="bubble bot">${escapeHtml(data.answer)}</div>
      <div class="bubble-meta">
        ${toolHtml}
        ${badges}
        ${data.debug_info ? `<span class="debug-toggle" onclick="toggleDebug('${debugId}')">🔍 디버그 정보 보기</span>` : ""}
      </div>
      ${debugHtml}
    </div>`;

  area.appendChild(row);
  scrollToBottom();
}

/* ── 디버그 패널 HTML 생성 ───────────────────────────────── */
function buildDebugHtml(info, id) {
  if (!info) return "";

  let html = `<div class="debug-panel" id="${id}">`;

  // 검색 쿼리
  if (info.query_used) {
    html += `<h4>🔎 검색 쿼리</h4><pre>${escapeHtml(info.query_used)}</pre>`;
  }

  // 검색된 문서
  if (info.retrieved_docs && info.retrieved_docs.length > 0) {
    html += `<h4>📚 ChromaDB TOP-${info.retrieved_docs.length} 검색 결과</h4>`;
    info.retrieved_docs.forEach((doc, i) => {
      const score = doc.score !== null ? ` (유사도: ${doc.score})` : "";
      html += `<pre>Rank ${i + 1}: ${escapeHtml(doc.recipe_name)}${escapeHtml(score)}\n${escapeHtml(doc.excerpt.slice(0, 200))}…</pre>`;
    });
  }

  // 컨텍스트
  if (info.context_excerpt) {
    html += `<h4>📝 LLM 전달 컨텍스트 (앞 500자)</h4><pre>${escapeHtml(info.context_excerpt)}</pre>`;
  }

  // Intermediate Steps (에이전트 모드)
  if (info.intermediate_steps && info.intermediate_steps.length > 0) {
    html += `<h4>⚙️ 에이전트 실행 단계</h4>`;
    info.intermediate_steps.forEach((step, i) => {
      const input  = typeof step.tool_input === "string"
        ? step.tool_input
        : JSON.stringify(step.tool_input, null, 2);
      html += `<pre>Step ${i + 1} — 툴: ${escapeHtml(step.tool)}\n입력: ${escapeHtml(input.slice(0, 150))}\n출력: ${escapeHtml(step.tool_output.slice(0, 200))}…</pre>`;
    });
  }

  html += `</div>`;
  return html;
}

function toggleDebug(id) {
  const panel = document.getElementById(id);
  panel?.classList.toggle("open");
}

/* ── 유틸 ────────────────────────────────────────────────── */
function scrollToBottom() {
  const area = document.getElementById("chatArea");
  area.scrollTop = area.scrollHeight;
}

function escapeHtml(str) {
  if (typeof str !== "string") str = String(str ?? "");
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
