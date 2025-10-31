from tools.rag.document_loader.csv_loader import load_csv_loader
from utils.util import get_project_root
from langchain_community.retrievers import BM25Retriever

def jeonse_price_retrieve(query):
    path = get_project_root() / "src"/ "data"/ "supply_demand" / "(월) 평균전세가격_아파트_r_one_2020_01_2025_09 - 최종.csv"
    loader = load_csv_loader(path)
    docs = loader.load()    
    retriever = BM25Retriever.from_documents(docs)
    retriever.k = 1 
    new_docs = retriever.invoke(query)
    result  = []
    for doc in new_docs:
        result.append(doc.page_content[1:])
    return result[0]
    