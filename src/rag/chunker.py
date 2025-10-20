"""
문서 청킹 유틸리티 (2025 기준 최신)
- LangChain 0.3+ 호환
- HuggingFace / OpenAI 임베딩 모델 기반 RAG 전처리에 바로 연결 가능
"""

from typing import List, Optional, Literal, Dict, Any
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    SemanticChunker,
)
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# 기본 Recursive Splitter
def chunk_with_recursive(
    docs: List[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    separators: Optional[List[str]] = None,
    **kwargs
) -> List[Document]:
    """
    ✅ RecursiveCharacterTextSplitter
    - 텍스트 구조를 보존하며 분할
    - 일반 문서 대부분에 적합
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators or ["\n\n", "\n", ".", " "],
        **kwargs
    )
    return splitter.split_documents(docs)


# 토큰 기반 Splitter (LLM 토큰 단위로 제어)
def chunk_with_token(
    docs: List[Document],
    chunk_size: int = 400,
    chunk_overlap: int = 50,
    model_name: str = "gpt-4o-mini",
    **kwargs
) -> List[Document]:
    """
    ✅ TokenTextSplitter
    - LLM 입력 제한 기준으로 분할
    - 짧은 QA 문맥용으로 이상적
    """
    splitter = TokenTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        model_name=model_name,
        **kwargs
    )
    return splitter.split_documents(docs)


# 시맨틱 기반 Splitter (의미 단위 분할)
def chunk_with_semantic(
    docs: List[Document],
    embedding_model: Any = None,
    min_chunk_size: int = 100,
    max_chunk_size: int = 1000,
    threshold: float = 0.4,
    **kwargs
) -> List[Document]:
    """
    - 임베딩 유사도로 의미 단위 감지
    - 논문, 보고서 등 문맥 연결 긴 문서에 적합
    """
    embedding_model = embedding_model or OpenAIEmbeddings(model="text-embedding-3-small")
    splitter = SemanticChunker(
        embeddings=embedding_model,
        breakpoint_threshold_type="percentile",
        min_chunk_size=min_chunk_size,
        max_chunk_size=max_chunk_size,
        breakpoint_threshold=threshold,
        **kwargs
    )
    return splitter.split_documents(docs)



# 적응형 청킹 (문서 종류 자동 감지)
def adaptive_chunker(
    docs: List[Document],
    strategy: Literal["auto", "semantic", "token", "recursive"] = "auto",
    **kwargs
) -> List[Document]:
    """
    자동 청킹 전략 선택기
    - auto: 문서 길이 및 패턴 기반으로 자동 결정
    - semantic: 의미 기반
    - token: 토큰 단위
    - recursive: 기본 구조 기반
    """
    if not docs:
        return []

    avg_len = sum(len(d.page_content) for d in docs) / len(docs)

    if strategy == "semantic" or (strategy == "auto" and avg_len > 1500):
        print("→ SemanticChunker 사용")
        return chunk_with_semantic(docs, **kwargs)
    elif strategy == "token" or (strategy == "auto" and avg_len < 400):
        print("→ TokenTextSplitter 사용")
        return chunk_with_token(docs, **kwargs)
    else:
        print("→ RecursiveCharacterTextSplitter 사용")
        return chunk_with_recursive(docs, **kwargs)
