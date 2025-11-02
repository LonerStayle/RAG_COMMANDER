from tools.rag.document_loader.csv_loader import load_csv_loader
from utils.util import get_project_root

def house_supply_retrieve():
    path = get_project_root() / "src"/ "data"/ "supply_demand" / "서울시_구별_10년_월별_주택공급.csv"
    loader = load_csv_loader(path, encoding="utf-8", autodetect_encoding=True)
    docs = loader.load()
    result = []
    for doc in docs:
        
        result.append(doc.page_content)
        
    return result

