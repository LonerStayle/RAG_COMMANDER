import pandas as pd
from utils.util import get_project_root
from utils.llm import LLMProfile
def unsold_units(target_area):
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

        질문: {target_area}
        """
    )
    query = llm.content


    path = get_project_root() / "src" / "data" / "unsold_units" / "미분양_데이터 - 최종.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    filtered = df[df["시군구"].astype(str).str.contains(query)]
    
    result = filtered.to_dict(orient="records")
    return result