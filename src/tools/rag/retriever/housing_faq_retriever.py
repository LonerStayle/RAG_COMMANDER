from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
import os 
from dotenv import load_dotenv
load_dotenv()

def retriever_housing_faq():
    emb = OpenAIEmbeddings(model="text-embedding-3-large")
    connection_url = os.getenv("POSTGRES_URL")

    # 기존 collection 불러오기
    collection_name = "text"
    store = PGVector(
        embedding_function=emb,
        connection_string=connection_url,
        collection_name=collection_name,
        use_jsonb=True,
    )
    retriever = store.as_retriever(search_kwargs={"k": 5})
    return retriever
