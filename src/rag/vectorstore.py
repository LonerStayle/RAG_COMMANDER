
"""
PostgreSQL (pgvector) 전용 벡터스토어 유틸리티
- LangChain 0.3+ 호환
- embedding model, connection, collection 자동 관리
"""

import os
from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from dotenv import load_dotenv



# PGVector 스토어 빌더
def build_pgvector_store(
    docs: Optional[List[Document]] = None,
    collection_name: str = "rag_docs",
    embedding_model: Embeddings = None,
) -> PGVector:
    load_dotenv()
    
    """
    - 해당 collection_name 이 없으면 → 새로 생성
    - 이미 존재하면 → 기존 인덱스 재활용
    - docs=None 으로 호출하면 항상 로드 모드로 동작
    """
    embedding_model = embedding_model
    connection_url = os.getenv("DATABASE_URL")
    try:
        # 존재하는 컬렉션을 불러오기 시도
        store = PGVector(
            connection_string=connection_url,
            embedding_function=embedding_model,
            collection_name=collection_name,
            use_jsonb=True,
        )
        if docs:
            print(f"'{collection_name}' 컬렉션에 {len(docs)}개 문서를 추가합니다.")
            store.add_documents(docs)

        print(f"✅ 기존 PGVector 컬렉션 '{collection_name}' 재사용 중")
        return store

    except Exception as e:
        # 실패시 새로 생성 
        print(f"⚙️ 컬렉션 '{collection_name}'을 새로 생성합니다. (사유: {e})")
        store = PGVector.from_documents(
            documents=docs or [],
            embedding=embedding_model,
            connection_string=connection_url,
            collection_name=collection_name,
            use_jsonb=True,
            pre_delete_collection=False,  
        )
        print(f"✅ 새 PGVector 컬렉션 '{collection_name}' 생성 완료")
        return store
