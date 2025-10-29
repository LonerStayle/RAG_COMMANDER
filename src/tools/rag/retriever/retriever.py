from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
import os 
from tools.rag.document_loader.default_loader import load_with_pymupdf
from utils.util import get_project_root
from tools.rag.chunker.default_chunker import adaptive_chunker 
from dotenv import load_dotenv
load_dotenv()

def retriever_housing_faq(**kwargs):
    doc_path = get_project_root() / "src" / "data" / "2024 주택청약 FAQ.pdf"
    documents = load_with_pymupdf(doc_path)
    chunk_list = adaptive_chunker(documents)
    
    emb = OpenAIEmbeddings(model = "text-embedding-3-small")
    collection_name = "text"
    connection_url = os.getenv("POSTGRES_URL")
    store = PGVector.from_documents(
        documents= chunk_list,
        embedding= emb, 
        connection_string = connection_url,
        collection_name= collection_name,
        use_jsonb=True,
        pre_delete_collection=False
        )
    return store.as_retriever(kwargs)