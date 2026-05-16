from pydantic import BaseModel, Field
from typing import Optional, Any


class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자 입력 메시지")
    mode: str = Field(default="agent", description="'agent' 또는 'rag'")
    session_id: str = Field(default="default", description="대화 세션 ID")


class RetrievedDoc(BaseModel):
    """ChromaDB에서 검색된 단일 문서 정보"""
    recipe_name: str
    excerpt: str = Field(description="page_content 앞 200자")
    score: Optional[float] = Field(default=None, description="유사도 점수 (높을수록 유사)")


class IntermediateStep(BaseModel):
    """에이전트가 실행한 툴 호출 1건"""
    tool: str
    tool_input: Any
    tool_output: str


class DebugInfo(BaseModel):
    """응답 생성 과정 추적 정보"""
    query_used: str = Field(default="", description="실제로 검색에 사용된 쿼리")
    retrieved_docs: list[RetrievedDoc] = Field(default_factory=list)
    context_excerpt: str = Field(default="", description="LLM에 넘긴 컨텍스트 앞 500자")
    tools_used: list[str] = Field(default_factory=list)
    intermediate_steps: list[IntermediateStep] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    tool_used: Optional[str] = Field(default=None, description="사용된 툴 레이블")
    sources: list[str] = Field(default_factory=list, description="참고 레시피 이름 목록")
    debug_info: DebugInfo = Field(default_factory=DebugInfo)
