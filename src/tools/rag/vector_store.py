from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
from threading import Lock

load_dotenv()

# ✅ 전역 캐싱 및 Lock (동시 초기화 방지)
_pgvector_cache = {}
_pgvector_lock = Lock()

def get_pgvector_store(collection_name: str):
    """
    PGVector 스토어를 안전하게 1회만 초기화하고 재사용.
    SQLAlchemy 메타데이터 중복 정의 문제도 함께 방지.
    """
    with _pgvector_lock:
        if collection_name not in _pgvector_cache:
            try:
                # ⚠️ LangChain 내부의 SQLAlchemy BaseModel metadata 중복 정의 방지
                from langchain_community.vectorstores import pgvector as pgv
                meta = pgv.BaseModel.metadata
                for tname in list(meta.tables.keys()):
                    if tname.startswith("langchain_pg_"):
                        meta.remove(meta.tables[tname])
            except Exception as e:
                print(f"[PGVector Init Warning] {e}")

            emb = OpenAIEmbeddings(model="text-embedding-3-large")
            connection_url = os.getenv("POSTGRES_URL")

            _pgvector_cache[collection_name] = PGVector(
                embedding_function=emb,
                connection_string=connection_url,
                collection_name=collection_name,
                use_jsonb=True,
            )

        return _pgvector_cache[collection_name]
