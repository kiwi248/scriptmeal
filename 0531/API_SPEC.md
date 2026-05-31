# 다이어트 레시피 AI — API 명세서

> **Swagger UI**: `{BASE_URL}/docs` (일반 엔드포인트 테스트용)
> **주의**: `/api/chat/stream` 은 SSE 방식으로 Swagger에서 테스트 불가. 본 문서 참고.

---

## 공통 정보

| 항목 | 내용 |
|---|---|
| Base URL | 배포 후 전달 예정 (로컬: `http://localhost:8000`) |
| 인증 | 없음 |
| Content-Type | `application/json` |
| 세션 관리 | `session_id` 문자열로 구분 (클라이언트가 생성·보관) |

---

## 엔드포인트 목록

| Method | Path | 설명 | Swagger 테스트 |
|---|---|---|---|
| POST | `/api/chat/stream` | 챗봇 스트리밍 응답 **(주력)** | ❌ 불가 |
| POST | `/api/chat` | 챗봇 일반 응답 (테스트용) | ✅ 가능 |
| POST | `/api/history` | 레시피 히스토리 저장 | ✅ 가능 |
| GET | `/api/history` | 레시피 히스토리 조회 | ✅ 가능 |
| POST | `/api/favorites` | 즐겨찾기 저장 | ✅ 가능 |
| GET | `/api/favorites` | 즐겨찾기 조회 | ✅ 가능 |
| DELETE | `/api/favorites/{id}` | 즐겨찾기 삭제 | ✅ 가능 |
| GET | `/health` | 서버 상태 확인 | ✅ 가능 |

---

## 1. POST `/api/chat/stream` ⭐ 주력 엔드포인트

챗봇 응답을 **SSE(Server-Sent Events)** 스트리밍으로 수신합니다.

### Request

```http
POST /api/chat/stream
Content-Type: application/json
```

```json
{
  "message": "떡볶이 먹고 싶어",
  "history": [
    { "role": "user",      "content": "안녕" },
    { "role": "assistant", "content": "안녕하세요! 어떤 레시피를 원하시나요?" }
  ]
}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `message` | string | ✅ | 유저 입력 메시지 |
| `history` | array | ❌ | 이전 대화 목록. 없으면 빈 배열 `[]` |
| `history[].role` | string | ✅ | `"user"` 또는 `"assistant"` |
| `history[].content` | string | ✅ | 해당 턴의 메시지 내용 |

### Response — SSE 이벤트 스트림

`Content-Type: text/event-stream`

각 이벤트는 `data: {JSON}\n\n` 형식으로 전달됩니다.

#### 이벤트 타입 3가지

**① `tool_start` — 툴 실행 시작 알림**

AI가 내부적으로 툴을 호출할 때 발생합니다. UI 로딩 메시지 표시에 활용하세요.

```
data: {"type": "tool_start", "tool": "get_diet_products"}
```

| `tool` 값 | 의미 | 권장 UI 메시지 |
|---|---|---|
| `get_diet_products` | DB에서 다이어트 제품 검색 중 | "🛒 관련 다이어트 제품 검색 중..." |
| `search_recipe` | 웹에서 레시피 검색 중 | "🔍 레시피 웹 검색 중..." |
| `get_weather_recipe` | 날씨 정보 조회 중 | "☀️ 날씨 정보 조회 중..." |

**② `chunk` — 응답 텍스트 조각**

최종 레시피/답변이 청크 단위로 스트리밍됩니다. 수신할 때마다 화면에 누적해서 표시하세요.

```
data: {"type": "chunk", "value": "## 다이어트 떡볶이\n\n### 재료\n"}
data: {"type": "chunk", "value": "- 곤약 떡 200g (22kcal)\n"}
data: {"type": "chunk", "value": "- 저당 떡볶이양념 100g (55kcal)\n"}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `value` | string | 텍스트 조각. 누적하면 전체 응답이 됩니다 |

**③ `done` — 스트리밍 완료**

스트림의 마지막 이벤트입니다. `value`에 시판 제품 구매 정보가 담겨 옵니다.

```
data: {"type": "done", "value": "\n\n---\n🛒 사용된 제품 구매 정보\n곤약 떡 22kcal | 약 180g 1개 899원 | 쿠팡"}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `value` | string | 구매 정보 문자열. 없으면 빈 문자열 `""` |

#### 이벤트 흐름 예시

```
[특정 음식 요청: "떡볶이 먹고 싶어"]

data: {"type": "tool_start", "tool": "get_diet_products"}
data: {"type": "chunk",      "value": "## 다이어트 떡볶이\n\n"}
data: {"type": "chunk",      "value": "### 재료\n- 곤약 떡 200g (22kcal)\n"}
data: {"type": "chunk",      "value": "..."}
data: {"type": "done",       "value": "\n\n---\n🛒 사용된 제품 구매 정보\n곤약 떡 22kcal | 약 180g 1개 899원 | 쿠팡"}
```

```
[메뉴 추천 요청: "오늘 날씨에 어울리는 메뉴 추천해줘"]

data: {"type": "tool_start", "tool": "get_weather_recipe"}
data: {"type": "chunk",      "value": "📅 현재 날짜/시간: 2026년 05월 31일 16:02 | 날씨: 맑음 | 기온: 30.7°C\n\n"}
data: {"type": "chunk",      "value": "오이냉국을 추천드립니다...\n"}
data: {"type": "done",       "value": ""}
```

```
[생소한 음식 요청: "두바이 초콜릿 레시피"]

data: {"type": "tool_start", "tool": "get_diet_products"}
data: {"type": "tool_start", "tool": "search_recipe"}
data: {"type": "chunk",      "value": "## 다이어트 두바이 초콜릿\n\n"}
data: {"type": "chunk",      "value": "..."}
data: {"type": "done",       "value": "\n\n---\n🛒 사용된 제품 구매 정보\n..."}
```

```
[후속 질문: "스플렌다가 뭐야?"]

data: {"type": "chunk", "value": "스플렌다는 설탕 대체 감미료로..."}
data: {"type": "done",  "value": ""}
```

### intent 추론 방법

`/api/chat/stream`은 intent를 별도로 반환하지 않습니다.
`tool_start` 이벤트의 `tool` 값으로 의도를 추론하세요.

| 수신된 tool | intent |
|---|---|
| `get_diet_products` 또는 `search_recipe` | `SPECIFIC_FOOD` (특정 음식) |
| `get_weather_recipe` | `GENERAL_RECIPE` (조건 기반) |
| tool 이벤트 없음 | `OFF_TOPIC` (주제 외) 또는 후속 질문 |

### JavaScript 구현 예시

```javascript
const response = await fetch('/api/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: userInput, history: chatHistory }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let fullReply = '';
let intent = 'OFF_TOPIC';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const lines = decoder.decode(value).split('\n');
  for (const line of lines) {
    if (!line.startsWith('data: ')) continue;
    const data = JSON.parse(line.slice(6));

    if (data.type === 'tool_start') {
      // 툴별 로딩 메시지 표시
      if (data.tool === 'get_diet_products') {
        intent = 'SPECIFIC_FOOD';
        showStatus('🛒 관련 다이어트 제품 검색 중...');
      } else if (data.tool === 'search_recipe') {
        intent = 'SPECIFIC_FOOD';
        showStatus('🔍 레시피 웹 검색 중...');
      } else if (data.tool === 'get_weather_recipe') {
        intent = 'GENERAL_RECIPE';
        showStatus('☀️ 날씨 정보 조회 중...');
      }

    } else if (data.type === 'chunk') {
      // 텍스트 누적 표시
      hideStatus();
      fullReply += data.value;
      updateUI(fullReply);

    } else if (data.type === 'done') {
      // 스트리밍 완료, 구매 정보 처리
      const purchaseInfo = data.value;  // 빈 문자열이면 구매 정보 없음
      if (purchaseInfo) showPurchaseInfo(purchaseInfo);
    }
  }
}
```

### 오류 응답

| HTTP 상태 | 원인 |
|---|---|
| `500` | 서버 초기화 실패 또는 OpenAI API 오류 |

---

## 2. POST `/api/chat` (Swagger 테스트용)

스트리밍 없이 완성된 응답을 한 번에 반환합니다. **프로덕션에서는 사용하지 마세요.**

### Request

`/api/chat/stream`과 동일

### Response

```json
{
  "reply": "## 다이어트 떡볶이\n\n### 재료\n...",
  "intent": "SPECIFIC_FOOD"
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `reply` | string | 레시피 전체 텍스트 (구매 정보 포함) |
| `intent` | string | `SPECIFIC_FOOD` / `GENERAL_RECIPE` / `OFF_TOPIC` |

---

## 3. POST `/api/history` — 히스토리 저장

레시피 응답이 완료된 후 프론트엔드에서 호출하세요.

### Request

```json
{
  "session_id":   "my-session",
  "user_message": "떡볶이 먹고 싶어",
  "recipe_reply": "## 다이어트 떡볶이\n...",
  "intent":       "SPECIFIC_FOOD"
}
```

### Response `201 Created`

```json
{
  "id":           1,
  "session_id":   "my-session",
  "user_message": "떡볶이 먹고 싶어",
  "recipe_reply": "## 다이어트 떡볶이\n...",
  "intent":       "SPECIFIC_FOOD",
  "created_at":   "2026-05-31T16:02:00.000Z"
}
```

---

## 4. GET `/api/history` — 히스토리 조회

```http
GET /api/history?session_id=my-session
```

### Response `200 OK`

```json
[
  {
    "id":           1,
    "session_id":   "my-session",
    "user_message": "떡볶이 먹고 싶어",
    "recipe_reply": "## 다이어트 떡볶이\n...",
    "intent":       "SPECIFIC_FOOD",
    "created_at":   "2026-05-31T16:02:00.000Z"
  }
]
```

> 최신순 정렬, 최대 30건 반환

---

## 5. POST `/api/favorites` — 즐겨찾기 저장

Request / Response 구조는 `/api/history`와 동일합니다.

```http
POST /api/favorites
```

---

## 6. GET `/api/favorites` — 즐겨찾기 조회

```http
GET /api/favorites?session_id=my-session
```

Response 구조는 `/api/history` 조회와 동일합니다. 최신순 전체 반환.

---

## 7. DELETE `/api/favorites/{id}` — 즐겨찾기 삭제

```http
DELETE /api/favorites/1
```

### Response `200 OK`

```json
{ "message": "삭제되었습니다." }
```

### 오류

| HTTP 상태 | 원인 |
|---|---|
| `404` | 해당 id의 즐겨찾기 없음 |
| `500` | 서버 오류 |

---

## 8. GET `/health` — 서버 상태 확인

```http
GET /health
```

```json
{ "status": "ok" }
```

---

## 응답 텍스트 포맷 참고

레시피 응답(`reply`, `chunk` 누적값)은 마크다운 형식입니다.

```markdown
## 레시피 제목

### 재료
- 재료명 분량 (칼로리)

### 조리법
1. 단계별 설명

### 칼로리
- 재료1 + 재료2 = 총 Nkcal

---
🛒 사용된 제품 구매 정보
제품명 Nkcal | 약 가격 | 구매처
```

> `---` 구분선 기준으로 레시피 본문과 구매 정보를 분리할 수 있습니다.
> 구매 정보가 없으면 `---` 이하 섹션이 없습니다.
