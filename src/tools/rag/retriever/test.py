from tools.rag.document_loader.default_loader import load_with_pymupdf
from utils.util import get_project_root  # 현재 프로젝트의 경로를 가져옴

def retriever_housingfaq():
    doc_path = get_project_root() / "src" / "data" / "2024 주택청약 FAQ.pdf"
    documents =load_with_pymupdf(get_project_root() + doc_path)
    
