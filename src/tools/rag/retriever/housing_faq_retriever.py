from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
import os
from tools.rag.db_collection_name import HOUSING_FAQ_KEY
from tools.rag.db_collection_name import HOUSING_RULE_KEY
from dotenv import load_dotenv

load_dotenv()


def housing_faq_retrieve():
    emb = OpenAIEmbeddings(model="text-embedding-3-large")
    connection_url = os.getenv("POSTGRES_URL")

    store = PGVector(
        embedding_function=emb,
        connection_string=connection_url,
        collection_name=HOUSING_FAQ_KEY,
        use_jsonb=True,
    )
    retriever = store.as_retriever(kwargs={"k": 10})
    return retriever


def housing_rule_retrieve():
    emb = OpenAIEmbeddings(model="text-embedding-3-large")
    connection_url = os.getenv("POSTGRES_URL")
    
    # 기존 collection 불러오기
    store = PGVector(
        embedding_function=emb,
        connection_string=connection_url,
        collection_name=HOUSING_RULE_KEY,
        use_jsonb=True,
    )
    retriever = store.as_retriever(search_kwargs={"k": 10})
    return retriever
