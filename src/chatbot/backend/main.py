"""
Housing FAQ 챗봇 FastAPI 서버
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import uuid
import json
import os
import tempfile
import sys
from pathlib import Path
from typing import AsyncGenerator

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "src"))

from models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    StreamChunk,
    PDFUploadResponse,
)
from chat_agent_langgraph import HousingChatAgentLangGraph

# PDF 로더 및 리트리버 임포트
from tools.rag.document_loader.policy_pdf_loader import policy_pdf_loader
from tools.rag.retriever.policy_pdf_retriever import PolicyPDFRetriever

# FastAPI 앱 초기화
app = FastAPI(
    title="Housing FAQ Chatbot API (LangGraph)",
    description="LangGraph 기반 주택 청약 및 분양 FAQ 챗봇 API",
    version="2.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 챗봇 에이전트 초기화 (싱글톤) - LangGraph 버전
chat_agent = HousingChatAgentLangGraph()


@app.get("/", response_model=HealthResponse)
async def root():
    """헬스체크 엔드포인트"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        message="Housing FAQ Chatbot API is running",
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크 엔드포인트"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        message="Service is operational",
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    일반 챗봇 엔드포인트 (비스트리밍)

    Args:
        request: 채팅 요청 데이터

    Returns:
        ChatResponse: AI 응답 및 참조 문서
    """
    try:
        # 세션 ID 생성 (없는 경우)
        session_id = request.session_id or str(uuid.uuid4())

        # 챗봇 처리
        response, sources = chat_agent.chat(
            message=request.message,
            target_area=request.target_area,
            main_type=request.main_type,
            total_units=request.total_units,
            session_id=session_id,
            use_faq=request.use_faq,
            use_rule=request.use_rule,
        )

        return ChatResponse(
            response=response,
            sources=sources,
            session_id=session_id,
            metadata={
                "target_area": request.target_area,
                "main_type": request.main_type,
                "total_units": request.total_units,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 처리 중 오류 발생: {str(e)}")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    스트리밍 챗봇 엔드포인트

    Args:
        request: 채팅 요청 데이터

    Returns:
        StreamingResponse: 스트리밍 응답
    """

    async def generate() -> AsyncGenerator[str, None]:
        """스트리밍 응답 생성기"""
        try:
            # 세션 ID 생성
            session_id = request.session_id or str(uuid.uuid4())

            # 세션 ID 먼저 전송
            session_chunk = StreamChunk(
                type="session", content=session_id
            )
            yield f"data: {session_chunk.model_dump_json()}\n\n"

            # 챗봇 스트리밍 처리
            async for chunk in chat_agent.stream_chat(
                message=request.message,
                target_area=request.target_area,
                main_type=request.main_type,
                total_units=request.total_units,
                session_id=session_id,
                use_faq=request.use_faq,
                use_rule=request.use_rule,
            ):
                if chunk["type"] == "text":
                    stream_chunk = StreamChunk(
                        type="text", content=chunk["content"]
                    )
                elif chunk["type"] == "sources":
                    stream_chunk = StreamChunk(
                        type="sources", sources=chunk["sources"]
                    )
                elif chunk["type"] == "done":
                    stream_chunk = StreamChunk(type="done")

                yield f"data: {stream_chunk.model_dump_json()}\n\n"

        except Exception as e:
            error_chunk = StreamChunk(type="error", error=str(e))
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.delete("/chat/history/{session_id}")
async def clear_history(session_id: str):
    """
    특정 세션의 대화 기록 삭제

    Args:
        session_id: 세션 ID

    Returns:
        삭제 완료 메시지
    """
    try:
        chat_agent.clear_history(session_id)
        return {"message": f"세션 {session_id}의 대화 기록이 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 기록 삭제 실패: {str(e)}")


@app.get("/chat/history/{session_id}")
async def get_history(session_id: str):
    """
    특정 세션의 대화 기록 조회

    Args:
        session_id: 세션 ID

    Returns:
        대화 기록
    """
    try:
        history = chat_agent._get_conversation_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 기록 조회 실패: {str(e)}")


@app.post("/upload/pdf", response_model=PDFUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    PDF 파일 업로드 및 벡터 DB에 저장

    Args:
        file: 업로드할 PDF 파일

    Returns:
        PDFUploadResponse: 업로드 결과
    """
    try:
        # 파일 확장자 확인
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail="PDF 파일만 업로드 가능합니다."
            )

        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # PDF 로드 및 메타데이터 추출
            policy_document = policy_pdf_loader.load_pdf(temp_file_path)

            # PolicyPDFRetriever에 문서 추가
            retriever = PolicyPDFRetriever()
            retriever.add_documents([policy_document])

            # 임시 파일 삭제
            os.unlink(temp_file_path)

            return PDFUploadResponse(
                success=True,
                message="PDF 파일이 성공적으로 업로드되고 DB에 저장되었습니다.",
                file_path=file.filename,
                policy_date=policy_document.policy_date,
                policy_type=policy_document.policy_type.value,
                title=policy_document.title,
            )

        except Exception as e:
            # 에러 발생 시 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise e

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"PDF 업로드 중 오류 발생: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
