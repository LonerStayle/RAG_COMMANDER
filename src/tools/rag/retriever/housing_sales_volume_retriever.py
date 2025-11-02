from tools.rag.document_loader.csv_loader import load_csv_loader
from utils.util import get_project_root
from langchain_community.retrievers import BM25Retriever

def housing_sales_volume_retrieve(query):
    path = get_project_root() / "src"/ "data"/ "supply_demand" / "서울_주택매매거래현황 - 최종.csv"
    loader = load_csv_loader(path, encoding='utf-8', autodetect_encoding=True)
    docs = loader.load()
    result = []
    retriever = BM25Retriever.from_documents(docs)
    retriever.k = 10
    new_docs = retriever.invoke(query)
    result  = []
    for doc in new_docs:
        result.append(doc.page_content[1:])
    return result