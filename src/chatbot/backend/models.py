"""
챗봇 API 요청/응답 모델
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    """채팅 메시지 모델"""
    role: str = Field(..., description="메시지 역할 (user, assistant, system)")
    content: str = Field(..., description="메시지 내용")


class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str = Field(..., description="사용자 메시지", min_length=1)
    target_area: Optional[str] = Field(None, description="사업지 장소 (예: 서울특별시 강남구 역삼동)")
    main_type: Optional[str] = Field(None, description="단지 타입 (예: 84타입)")
    total_units: Optional[str] = Field(None, description="세대수 (예: 120세대)")
    session_id: Optional[str] = Field(None, description="세션 ID (대화 기록 관리)")
    use_faq: bool = Field(True, description="FAQ 데이터 사용 여부")
    use_rule: bool = Field(True, description="주택공급 규칙 데이터 사용 여부")


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    response: str = Field(..., description="AI 응답 메시지")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="참조 문서 소스")
    session_id: Optional[str] = Field(None, description="세션 ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")


class StreamChunk(BaseModel):
    """스트리밍 응답 청크"""
    type: str = Field(..., description="청크 타입 (text, sources, done)")
    content: Optional[str] = Field(None, description="텍스트 내용")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="참조 문서")
    error: Optional[str] = Field(None, description="에러 메시지")


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str = Field(..., description="서비스 상태")
    version: str = Field(..., description="API 버전")
    message: str = Field(..., description="상태 메시지")


class PDFUploadResponse(BaseModel):
    """PDF 업로드 응답"""
    success: bool = Field(..., description="업로드 성공 여부")
    message: str = Field(..., description="응답 메시지")
    file_path: Optional[str] = Field(None, description="저장된 파일 경로")
    policy_date: Optional[str] = Field(None, description="추출된 정책 날짜")
    policy_type: Optional[str] = Field(None, description="추출된 정책 유형")
    title: Optional[str] = Field(None, description="추출된 제목")
