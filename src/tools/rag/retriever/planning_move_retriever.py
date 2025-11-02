from tools.rag.document_loader.csv_loader import load_csv_loader
from utils.util import get_project_root
from utils.llm import LLMProfile

def planning_move_retrieve(query):
    path = get_project_root() /"src"/"data"/"supply_demand"/"250829_입주예정물량 공개용.csv"
    docs = load_csv_loader(path, encoding='utf-8', autodetect_encoding=True).load()
    
    llm = LLMProfile.dev_llm().invoke(
    f"""
    당신은 에이전트의 플로우 중에 아주 작은 파트를 맡고 있습니다.
    JSON 데이터 중에 주소가 {query}의 자치구 (강동구, 강서구 ..등) 중의 유사한 자치구만 찾아서 데이터를 남겨놔주세요
    에이전트 개발중 일부분이기 때문에 절대 불필요한 말을 금합니다. 해당 데이터만 얘기하세요
    
    [강력지침]
    - 아래 내용중의 해당하는 내용만 찾아서 골라 원래 JSON으로만 말하세요
    - ``` 이나 이상한 json 이러고 시작하는말 다 없애세요
    
    {docs}
    """
    )
    return llm.content
    