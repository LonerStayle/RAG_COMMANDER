"""
정책 에이전트에서 사용하는 타입 정의
순환 import를 피하기 위해 별도 파일로 분리
"""

from pydantic import BaseModel, Field


class ReportCheck(BaseModel):
    """
    보고서가 템플릿을 충족했는지 나타내는 구조화된 평가 결과
    """

    is_complete: bool = Field(description="모든 필수 항목이 채워졌으면 True")
    missing_sections: list[str] = Field(default_factory=list)
    missing_information: str = Field(default="")
    search_queries: list[str] = Field(default_factory=list)

