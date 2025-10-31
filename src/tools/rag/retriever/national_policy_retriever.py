from tools.rag.document_loader.csv_loader import load_csv_loader
from utils.util import get_project_root

def national_policy_retrieve():
    path = get_project_root() / "src"/ "data"/ "policy_factors" / "국토교통부_부동산정책(2024~2025) - 최종.csv"
    loader = load_csv_loader(path)
    docs = loader.load()
    result = []
    for doc in docs:
        result.append(doc.page_content)
    return result