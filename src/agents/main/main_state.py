from langgraph.graph.message import MessagesState
from utils.util import attach_auto_keys

from pydantic import BaseModel, Field
from typing import Optional,Dict

@attach_auto_keys
class MainState(MessagesState):
    start_input: dict
    insight_outputs: dict
    final_report: str


class StartConfirmation(BaseModel):
    confirm: bool = Field(
        description="작업을 시작할지 여부입니다. yes 또는 no 중 하나를 입력합니다."
    )
    
    question:str = Field(
        description="보고서 내용을 구체적으로 작성하기 위해 사용자에게 제시할 추가 질문 입니다."
    )
    
    reason: Optional[str] = Field(
        description="confirm 이 False 일 경우, 시작하지 않으려는 이유를 간단히 입력합니다."
    )
    
    verification:str = Field(
        description="사용자가 필수 정보를 모두 제공해줘서 실제 보고 작성을 시작할 것임을 전달하는 메시지 입니다."
    )    

# 최초 입력 데이터 (보고서 생성 전 사용자가 직접 입력하는 정보)
class StartInput(BaseModel):
    target_area: str = Field(
        description="조사하려는 주소입니다. 예시: 인천광역시 부평구 부개동 13-5번지 일원",
    )

    scale: str = Field(
        description="단지의 규모를 나타냅니다. 예시: 대단지, 중규모, 소규모, 주력 타입 84㎡ 등"
    )

    total_units: Optional[int] = Field(
        description="전체 세대수입니다. 예시: 1050"
    )

    units_by_type: Optional[str] = Field(
        description="타입별 세대수입니다. 예시: {'59㎡': 300, '84㎡': 700}"
    )

    brand: Optional[str] = Field(description="대표 평형 / 브랜드 / 시공사 입니다.")

    orientation: Optional[str] = Field(description="향 / 배치 형태 입니다.")

    parking_ratio: Optional[float] = Field(description="주차시설 비율 입니다.")

    terrain_condition: Optional[str] = Field(description="지형조건입니다. 예시: 평지, 경사지, 복합지형")

    gross_area: Optional[float] = Field(description="단지의 연면적(m²)입니다.")

    floor_area_ratio_range: Optional[float] = Field(
         description="용적률(%)입니다."
    )
    
    building_coverage_ratio_range: Optional[float] = Field(
        description="건폐율(%)입니다."
    )
