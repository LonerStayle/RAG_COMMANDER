from langchain_community.vectorstores import PGVector
from tools.rag.db_collection_name import AGE_POPULATION_KEY
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os
from utils.llm import LLMProfile


# 2025년 4 ~ 9월 -> 인구 연령별 분포
def age_population_retriever(question):
    load_dotenv()
    POSTGRES_URL = os.getenv("POSTGRES_URL")
    emb = OpenAIEmbeddings(model="text-embedding-3-large")
    store = PGVector(
        collection_name=AGE_POPULATION_KEY,
        embedding_function=emb,
        connection_string=POSTGRES_URL,
    )
    retriever = store.as_retriever(seach_type={"k": 1})
    search_result = retriever.invoke(question)
    search_doc = search_result[0].page_content
    response = LLMProfile.dev_llm().invoke(f"""
        당신은 RAG중 리트리버 결과로 받은 문서중에 다음 질문에 적절한 내용만 찾아서 정리하는 사람입니다.
        질문 - {question}

        [제한 사항]
        불필요한 말은 절대 삼가하십시오, 당신은 RAG 전용일 뿐입니다.                                                        

        [문서 내용]
        {search_doc}                                                        
        """)
    return response.content
