from tools.rag.vector_store import get_pgvector_store

from tools.rag.db_collection_name import HOUSING_FAQ_KEY
from tools.rag.db_collection_name import HOUSING_RULE_KEY
from dotenv import load_dotenv

load_dotenv()


def housing_faq_retrieve():
    """FAQ 데이터 리트리버"""
    store = get_pgvector_store(HOUSING_FAQ_KEY)
    return store.as_retriever(search_kwargs={"k": 20})


def housing_rule_retrieve():
    """주택공급 규칙 리트리버"""
    store = get_pgvector_store(HOUSING_RULE_KEY)
    return store.as_retriever(search_kwargs={"k": 20})
