"""
채팅 컨트롤러 — POST /api/chat

mode 값에 따라 agent_service 또는 rag_service 를 호출하고
ChatResponse 를 JSON 으로 반환한다.
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.models.chat_model import ChatRequest, ChatResponse
from backend.services.agent_service import invoke_agent
from backend.services.rag_service import invoke_rag

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    사용자 메시지를 받아 RAG 또는 에이전트로 응답을 생성한다.

    - mode="agent" : RAG + Tavily 웹서치 에이전트
    - mode="rag"   : ConversationalRAG (대화 이력 유지)
    """
    logger.info(
        "[ChatController] POST /api/chat — mode=%s | session_id=%s | message=%s",
        req.mode, req.session_id, req.message[:80],
    )

    if not req.message.strip():
        logger.warning("[ChatController] 빈 메시지 수신 — 400 반환")
        raise HTTPException(status_code=400, detail="메시지가 비어 있습니다.")

    try:
        if req.mode == "rag":
            logger.info("[ChatController] RAG 모드 → rag_service.invoke_rag 호출")
            response = await invoke_rag(req.message, req.session_id)
        else:
            logger.info("[ChatController] 에이전트 모드 → agent_service.invoke_agent 호출")
            response = await invoke_agent(req.message, req.session_id)

        logger.info(
            "[ChatController] 응답 생성 완료 — tool_used=%s | sources=%s | answer_len=%d",
            response.tool_used, response.sources, len(response.answer),
        )
        return response

    except Exception as exc:
        logger.exception("[ChatController] 처리 중 오류 발생: %s", exc)
        raise HTTPException(status_code=500, detail=f"서버 오류: {exc}") from exc
