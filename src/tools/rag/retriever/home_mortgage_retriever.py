from tools.rag.document_loader.csv_loader import load_csv_loader
from utils.util import get_project_root

def home_mortgage_retrieve():
    path = get_project_root() / "src"/ "data"/ "economic_metrics" / "대출금리_10년_데이터 - 최종.csv"
    loader = load_csv_loader(path, encoding='utf-8', autodetect_encoding=True)
    docs = loader.load()
    result = []
    for doc in docs:        
        result.append(doc.page_content[1:])
    
    return result