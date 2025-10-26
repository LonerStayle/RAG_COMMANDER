from enum import Enum
from pathlib import Path
from utils.util import get_project_root


class PromptType(Enum):
    
    def __init__(self, value, path, description):
        self._value_ = value   # ✅ Enum의 내부 value는 _value_ 로 할당
        self.path = path
        self.description = description

    def to_dict(self):
        return {"path": self.path, "description": self.description}


    MAIN_START_CONFIRMATION = (
        "MAIN_START_CONFIRMATION",
        str(Path(get_project_root()) / "src" / "prompts" / "main.yaml"),
        "메인 에이전트의 시작 여부 확인 메시지",
    )
    
    MAIN_START = (
        "MAIN_START",
        str(Path(get_project_root()) / "src" / "prompts" / "main.yaml"),
        "메인 에이전트의 보고서 작성 시작 메시지",
    )
    
    #---1. <입지 분석>---
    LOCATION_INSIGHT_SYSTEM = (
        "LOCATION_INSIGHT_SYSTEM",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_location_insight.yaml"),
        "입지 분석 에이전트의 시스템 메시지",
    )
    
    LOCATION_INSIGHT_HUMAN = (
        "LOCATION_INSIGHT_HUMAN",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_location_insight.yaml"),
        "입지 분석 에이전트의 실행 메시지",
    )
    
    #---2. 경제/정책 분석---
    ECONOMIC_INSIGHT_SYSTEM = (
        "ECONOMIC_INSIGHT_SYSTEM",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_economic_insight.yaml"),
        "경제/정책 분석 에이전트의 시스템 메시지",
    )
    
    ECONOMIC_INSIGHT_HUMAN = (
        "ECONOMIC_INSIGHT_HUMAN",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_economic_insight.yaml"),
        "경제/정책 분석 에이전트의 실행 메시지",
    )
    
    #---3. 수급 분석 분석---
    SUPPLY_DEMAND_SYSTEM = (
        "SUPPLY_DEMAND_SYSTEM",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_supply_demend.yaml"),
        "수요와 공급 분석 에이전트의 시스템 메시지",
    )
    
    SUPPLY_DEMAND_HUMAN = (
        "SUPPLY_DEMAND_HUMAN",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_supply_demend.yaml"),
        "수요와 공급 분석 에이전트의 실행 메시지",
    ) 
    
    #---4. 미분양 심화 분석 ---
    UNSOLD_INSIGHT_SYSTEM = (
        "UNSOLD_INSIGHT_SYSTEM",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_unsold_insight.yaml"),
        "미분양 분석 에이전트의 시스템 메시지",
    )
    
    UNSOLD_INSIGHT_HUMAN = (
        "UNSOLD_INSIGHT_HUMAN",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_unsold_insight.yaml"),
        "미분양 분석 에이전트의 실행 메시지",
    )       
    
    #---5. 주변 시세 및 경쟁 분석 ---
    NEARBY_MARKET_SYSTEM = (
        "NEARBY_MARKET_SYSTEM",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_nearby_market.yaml"),
        "주변 시세 및 경쟁 분석 에이전트의 시스템 메시지",
    )
    
    NEARBY_MARKET_HUMAN = (
        "NEARBY_MARKET_HUMAN",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_nearby_market.yaml"),
        "주변 시세 및 경쟁 분석 에이전트의 실행 메시지",
    )       
    
     
    #---6. 주변 시세 및 경쟁 분석 ---
    POPULATION_INSIGHT_SYSTEM = (
        "POPULATION_INSIGHT_SYSTEM",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_population_insight.yaml"),
        "유동 인구 분석 에이전트의 시스템 메시지",
    )
    
    POPULATION_INSIGHT_HUMAN = (
        "POPULATION_INSIGHT_HUMAN",
        str(Path(get_project_root()) / "src" / "prompts" / "analysis_population_insight.yaml"),
        "유동 인구 분석 에이전트의 실행 메시지",
    )   
    
    #---7. 정민재 이사 ---
    JUNG_MIN_JAE_SYSTEM = (
        "JUNG_MIN_JAE_SYSTEM",
        str(Path(get_project_root()) / "src" / "prompts" / "jung_min_jae.yaml"),
        "정민재 이사의 생각이 담긴 시스템 메시지",
    )
    
    JUNG_MIN_JAE_HUMAN = (
        "JUNG_MIN_JAE_HUMAN",
        str(Path(get_project_root()) / "src" / "prompts" / "jung_min_jae.yaml"),
        "정민재 이사의 실행 메시지",
    )
    
    JUNG_MIN_JAE_SUMMARY = (
        "JUNG_MIN_JAE_SUMMARY",
        str(Path(get_project_root()) / "src" / "prompts" / "jung_min_jae.yaml"),
        "정민재 이사의 이전 보고서 페이지 요약 메시지",
    )
    
    
    JUNG_MIN_JAE_SEGMENT_01 = (
        "JUNG_MIN_JAE_SEGMENT_01",
        str(Path(get_project_root()) / "src" / "prompts" / "jung_min_jae.yaml"),
        "정민재 이사의 보고서 페이지 별 내용 01",
    )
    
    JUNG_MIN_JAE_SEGMENT_02 = (
        "JUNG_MIN_JAE_SEGMENT_02",
        str(Path(get_project_root()) / "src" / "prompts" / "jung_min_jae.yaml"),
        "정민재 이사의 보고서 페이지 별 내용 02",
    )
    
    JUNG_MIN_JAE_SEGMENT_03 = (
        "JUNG_MIN_JAE_SEGMENT_03",
        str(Path(get_project_root()) / "src" / "prompts" / "jung_min_jae.yaml"),
        "정민재 이사의 보고서 페이지 별 내용 03",
    )
    
    