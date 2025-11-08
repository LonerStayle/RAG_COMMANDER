from pydantic import BaseModel, Field
from typing import Optional
from utils.util import attach_auto_keys

# 최초 입력 데이터 (보고서 생성 전 사용자가 직접 입력하는 정보)
@attach_auto_keys
class StartInput(BaseModel):
    target_area: str = Field(
        description="조사하려는 주소입니다. 예시: 인천광역시 부평구 부개동, 서울특별시 강서구 신길동",
    )
    main_type: str = Field(
        description="단지의 대표 타입 혹은 타입별 세대수입니다. 예시: 84제곱미터 or 84m² or {'59㎡': 300, '84㎡': 700}"
    )
    email: str = Field(
        description="최종 보고서 PPT 파일을 보낼 이메일 주소입니다."
    )
    total_units: str = Field(
        description="단지의 전체 세대수입니다. 예시: 1000세대 or 1000"
    )

    policy_period: Optional[str] = Field(
        default=None,
        description="분석할 정책 기간입니다. 예시: 최근 1년, 2024-2025년 등"
    )
    policy_count: Optional[int] = Field(
        default=None,
        description="분석할 정책 개수입니다. 예시: 1, 2, 3"
    )
    policy_list: Optional[str] = Field(
        default=None,
        description="분석할 정책 리스트입니다. 예시: ['2025.10.15', '2025.06.27']"
    )
    brand: Optional[str] = Field(
        default=None,
        description="브랜드 / 시공사 입니다."
    )
    orientation: Optional[str] = Field(
        default=None,
        description="향 / 배치 형태 입니다."
    )
    parking_ratio: Optional[float] = Field(
        default=None,
        description="주차시설 비율 입니다."
    )
    terrain_condition: Optional[str] = Field(
        default=None,
        description="지형조건입니다. 예시: 평지, 경사지, 복합지형"
    )
    gross_area: Optional[float] = Field(
        default=None,
        description="단지의 연면적(m²)입니다."
    )
    floor_area_ratio_range: Optional[float] = Field(
        default=None,
        description="용적률(%)입니다."
    )
    building_coverage_ratio_range: Optional[float] = Field(
        default=None,
        description="건폐율(%)입니다."
    )