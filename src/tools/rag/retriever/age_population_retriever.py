from langchain_community.vectorstores import PGVector
from tools.rag.db_collection_name import AGE_POPULATION_KEY
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os
from utils.llm import LLMProfile
from tools.rag.vector_store import get_pgvector_store

# 2025년 4 ~ 9월 -> 인구 연령별 분포
def age_population_retrieve(question):
    load_dotenv()
    POSTGRES_URL = os.getenv("POSTGRES_URL")
    llm = LLMProfile.dev_llm().invoke(
        f"""
        당신은 대한민국 서울특별시 자치구를 찾아주는 도우미 입니다. 
        에이전트 흐름중 사용하고 있습니다. 주소 질문에 특정 자치구만 찾아서 
        그부분만 출력해주시면 됩니다.

        [강력 지침]
        - 자치구 말이외에 절대 다른말을 하지마세요
        - 자치구만 말씀하세요

        [예시]
        1. "서울특별시 종로구" -> "종로구"
        2. "서울 강동구 서초동" -> "강남구

        질문: {question}
        """
    )
    query = llm.content
    store = get_pgvector_store(AGE_POPULATION_KEY)
    retriever = store.as_retriever(search_type="similarity", search_kwargs={"k": 1})
    search_result = retriever.invoke(query)

    if not search_result:
        return f"'{query}' 지역의 연령별 인구 데이터를 찾을 수 없습니다."

    search_doc = search_result[0].page_content[4:]
    return search_doc
