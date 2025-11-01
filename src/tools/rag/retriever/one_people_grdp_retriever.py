from langchain_community.retrievers import BM25Retriever
from utils.util import get_project_root
from utils.llm import LLMProfile
from tools.rag.document_loader.csv_loader import load_csv_loader


def one_people_grdp_retrieve(address: str):
    llm = LLMProfile.dev_llm().invoke(
        f"""
    당신은 대한민국 서울특별시 자치구를 찾아주는 도우미 입니다. 
    에이전트 흐름중 사용하고 있습니다. 주소 질문에 특정 자치구만 찾아서 
    그부분만 출력해주시면 됩니다.
    
    [강력 지침]
    - 자치구 말이외에 절대 다른말을 하지마세요
    - 자치구만 말씀하세요
    
    [예시]
    1. "서울특별시 종로구" -> "종로구"
    2. "서울 강동구 서초동" -> "강남구
    
    질문: {address}
    """
    )
    query = llm.content
    path = (
        get_project_root()
        / "src"
        / "data"
        / "economic_metrics"
        / "서울_자치구별_1인당_GRDP.csv"
    )

    loader = load_csv_loader(path)
    docs = loader.load()
    seoul_docs = []

    for doc in docs:
        seoul_docs.append(doc)

    retriever = BM25Retriever.from_documents(seoul_docs)
    retriever.k = 1
    new_docs = retriever.invoke(query)
    result = []
    for doc in new_docs:
        result.append(doc.page_content[7:])
    return result[0]
