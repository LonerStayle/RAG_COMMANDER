"""
서울 구별 주택공급 현황 조회 도구

이 모듈은 주택공급 데이터(Excel/CSV)를 읽고,
서울의 25개 구별 공급현황을 조회하는 LangChain tool을 제공합니다.
"""

from typing import Optional, List, Dict, Any, Literal, Union
from langchain_core.tools import tool
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64

load_dotenv()


# 서울 25개 구 리스트
SEOUL_DISTRICTS = [
    "종로구", "중구", "용산구", "성동구", "광진구",
    "동대문구", "중랑구", "성북구", "강북구", "도봉구",
    "노원구", "은평구", "서대문구", "마포구", "양천구",
    "강서구", "구로구", "금천구", "영등포구", "동작구",
    "관악구", "서초구", "강남구", "송파구", "강동구"
]


class HousingSupplyTool:
    """주택공급 현황 조회 클래스"""

    def __init__(self, data_path: Optional[str] = None):
        """
        Args:
            data_path: 공급현황 데이터 파일 경로 (.xlsx 또는 .csv)
        """
        self.data_path = data_path
        self.df = None

        if data_path and os.path.exists(data_path):
            self.load_data(data_path)

    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        공급현황 데이터 파일 로드

        Args:
            file_path: Excel 또는 CSV 파일 경로

        Returns:
            DataFrame
        """
        print(f"📁 데이터 로드 중: {file_path}")

        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                self.df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                self.df = pd.read_csv(file_path)
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {file_path}")

            print(f"✅ 데이터 로드 완료: {len(self.df)}행 × {len(self.df.columns)}열")
            print(f"컬럼: {list(self.df.columns)}")

            return self.df

        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return pd.DataFrame()

    def filter_seoul_districts(
        self,
        df: Optional[pd.DataFrame] = None,
        district_column: str = "시군구"
    ) -> pd.DataFrame:
        """
        서울의 25개 구만 필터링

        Args:
            df: DataFrame (None이면 self.df 사용)
            district_column: 구 이름이 있는 컬럼명

        Returns:
            서울 구만 포함된 DataFrame
        """
        if df is None:
            df = self.df

        if df is None or df.empty:
            print("⚠️ 데이터가 없습니다.")
            return pd.DataFrame()

        if district_column not in df.columns:
            print(f"❌ 컬럼 '{district_column}'을(를) 찾을 수 없습니다.")
            print(f"사용 가능한 컬럼: {list(df.columns)}")
            return pd.DataFrame()

        # 서울 구만 필터링
        # "서울특별시 강남구" 또는 "강남구" 형태 모두 지원
        filtered = df[
            df[district_column].apply(
                lambda x: any(district in str(x) for district in SEOUL_DISTRICTS)
            )
        ]

        print(f"✅ 서울 구 필터링 완료: {len(filtered)}개 구")

        return filtered

    def get_supply_by_district(
        self,
        district: Optional[str] = None,
        year: Optional[str] = None,
        district_column: str = "시군구",
        year_column: Optional[str] = "연도"
    ) -> pd.DataFrame:
        """
        특정 구 또는 전체 서울 구의 공급현황 조회

        Args:
            district: 구 이름 (None이면 전체)
            year: 연도 (None이면 전체)
            district_column: 구 컬럼명
            year_column: 연도 컬럼명

        Returns:
            공급현황 DataFrame
        """
        if self.df is None or self.df.empty:
            print("⚠️ 데이터가 로드되지 않았습니다.")
            return pd.DataFrame()

        # 서울 구 필터링
        result = self.filter_seoul_districts(self.df, district_column)

        # 특정 구 필터링
        if district:
            result = result[
                result[district_column].str.contains(district, na=False)
            ]
            print(f"🔍 '{district}' 필터링: {len(result)}건")

        # 연도 필터링
        if year and year_column and year_column in result.columns:
            result = result[result[year_column].astype(str) == str(year)]
            print(f"📅 '{year}년' 필터링: {len(result)}건")

        return result

    def get_summary_by_district(
        self,
        district_column: str = "시군구",
        value_column: str = "공급량"
    ) -> pd.DataFrame:
        """
        구별 공급현황 요약

        Args:
            district_column: 구 컬럼명
            value_column: 집계할 값 컬럼명

        Returns:
            구별 합계 DataFrame
        """
        if self.df is None or self.df.empty:
            print("⚠️ 데이터가 로드되지 않았습니다.")
            return pd.DataFrame()

        # 서울 구만 필터링
        seoul_df = self.filter_seoul_districts(self.df, district_column)

        if value_column not in seoul_df.columns:
            print(f"❌ 컬럼 '{value_column}'을(를) 찾을 수 없습니다.")
            return pd.DataFrame()

        # 구별 합계
        summary = seoul_df.groupby(district_column)[value_column].sum().reset_index()
        summary = summary.sort_values(value_column, ascending=False)

        print(f"✅ 구별 요약 완료: {len(summary)}개 구")

        return summary

    def format_output(
        self,
        df: pd.DataFrame,
        title: str = "공급현황"
    ) -> str:
        """DataFrame을 읽기 쉽게 포맷팅"""
        if df is None or df.empty:
            return f"{title}: 데이터 없음"

        output = [f"\n{'='*80}"]
        output.append(f"{title}")
        output.append('='*80)
        output.append(f"총 {len(df)}건")
        output.append("")

        # 데이터 출력 (최대 20건)
        display_df = df.head(20)
        output.append(display_df.to_string(index=False))

        if len(df) > 20:
            output.append(f"\n... 외 {len(df) - 20}건")

        output.append('='*80)

        return "\n".join(output)

    def prepare_date_columns(
        self,
        df: Optional[pd.DataFrame] = None,
        date_column: str = "연월"
    ) -> pd.DataFrame:
        """
        날짜 컬럼을 datetime으로 변환하고 연도/월 컬럼 추가

        Args:
            df: DataFrame (None이면 self.df 사용)
            date_column: 날짜 컬럼명

        Returns:
            날짜 정보가 추가된 DataFrame
        """
        if df is None:
            df = self.df.copy()
        else:
            df = df.copy()

        if df is None or df.empty:
            return df

        if date_column not in df.columns:
            print(f"⚠️ '{date_column}' 컬럼이 없습니다.")
            return df

        # 날짜 변환 시도
        try:
            df[date_column] = pd.to_datetime(df[date_column])
        except:
            try:
                df[date_column] = pd.to_datetime(df[date_column], format='%Y%m')
            except Exception as e:
                print(f"⚠️ 날짜 변환 실패: {e}")
                return df

        # 연도, 월 컬럼 추가
        df['연도'] = df[date_column].dt.year
        df['월'] = df[date_column].dt.month

        return df

    def get_yearly_analysis(
        self,
        district: Optional[str] = None,
        date_column: str = "연월",
        value_column: str = "공급량"
    ) -> pd.DataFrame:
        """
        연도별 공급량 분석

        Args:
            district: 특정 구 (None이면 전체 서울)
            date_column: 날짜 컬럼명
            value_column: 집계할 값 컬럼명

        Returns:
            연도별 집계 DataFrame
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        # 서울 구 필터링
        df = self.filter_seoul_districts(self.df)

        # 특정 구 필터링
        if district:
            df = df[df.apply(lambda x: district in str(x), axis=1)]

        # 날짜 컬럼 준비
        df = self.prepare_date_columns(df, date_column)

        if '연도' not in df.columns or value_column not in df.columns:
            print(f"⚠️ 필요한 컬럼이 없습니다: 연도, {value_column}")
            return pd.DataFrame()

        # 연도별 집계
        yearly = df.groupby('연도')[value_column].agg(['sum', 'mean', 'count']).reset_index()
        yearly.columns = ['연도', '총공급량', '평균공급량', '데이터건수']

        return yearly.sort_values('연도')

    def get_monthly_analysis(
        self,
        district: Optional[str] = None,
        date_column: str = "연월",
        value_column: str = "공급량"
    ) -> pd.DataFrame:
        """
        월별 공급 패턴 분석

        Args:
            district: 특정 구 (None이면 전체 서울)
            date_column: 날짜 컬럼명
            value_column: 집계할 값 컬럼명

        Returns:
            월별 평균 DataFrame
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        # 서울 구 필터링
        df = self.filter_seoul_districts(self.df)

        # 특정 구 필터링
        if district:
            df = df[df.apply(lambda x: district in str(x), axis=1)]

        # 날짜 컬럼 준비
        df = self.prepare_date_columns(df, date_column)

        if '월' not in df.columns or value_column not in df.columns:
            return pd.DataFrame()

        # 월별 집계
        monthly = df.groupby('월')[value_column].agg(['mean', 'sum', 'count']).reset_index()
        monthly.columns = ['월', '평균공급량', '총공급량', '데이터건수']

        return monthly.sort_values('월')

    def get_district_comparison(
        self,
        districts: List[str],
        date_column: Optional[str] = None,
        district_column: str = "시군구",
        value_column: str = "공급량"
    ) -> pd.DataFrame:
        """
        여러 구의 공급량 비교

        Args:
            districts: 비교할 구 목록
            date_column: 날짜 컬럼 (있으면 시계열 비교)
            district_column: 구 컬럼명
            value_column: 집계할 값 컬럼명

        Returns:
            구별 비교 DataFrame
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        results = []

        for district in districts:
            district_df = self.df[
                self.df[district_column].str.contains(district, na=False)
            ]

            if len(district_df) == 0:
                continue

            if date_column and date_column in district_df.columns:
                # 시계열 데이터
                district_df = self.prepare_date_columns(district_df, date_column)
                if '연도' in district_df.columns:
                    yearly = district_df.groupby('연도')[value_column].sum().reset_index()
                    yearly['구'] = district
                    results.append(yearly)
            else:
                # 단순 합계
                total = district_df[value_column].sum() if value_column in district_df.columns else 0
                results.append({
                    '구': district,
                    '총공급량': total
                })

        if not results:
            return pd.DataFrame()

        if isinstance(results[0], dict):
            return pd.DataFrame(results)
        else:
            return pd.concat(results, ignore_index=True)


# LangChain tool로 래핑
@tool
def load_housing_supply_data(file_path: str) -> str:
    """
    주택공급 데이터 파일을 로드합니다.

    이 도구는 Excel 또는 CSV 형식의 주택공급 데이터를 읽고,
    기본 정보를 출력합니다.

    Args:
        file_path: 데이터 파일 경로 (.xlsx 또는 .csv)

    Returns:
        데이터 로드 결과

    Examples:
        >>> load_housing_supply_data("data/공급현황_2024.xlsx")
    """
    tool_instance = HousingSupplyTool()
    df = tool_instance.load_data(file_path)

    if df.empty:
        return "데이터 로드 실패"

    return tool_instance.format_output(df, f"공급 데이터 ({file_path})")


@tool
def get_seoul_district_supply(
    file_path: str,
    district: Optional[str] = None,
    district_column: str = "시군구"
) -> str:
    """
    서울의 구별 주택공급 현황을 조회합니다.

    이 도구는 서울의 25개 구 공급현황을 조회하거나,
    특정 구의 공급현황을 상세히 확인할 수 있습니다.

    Args:
        file_path: 공급 데이터 파일 경로
        district: 조회할 구 이름 (예: "강남구", None이면 전체)
        district_column: 구 이름 컬럼명 (기본값: "시군구")

    Returns:
        구별 공급현황

    Examples:
        >>> get_seoul_district_supply("data/공급.xlsx")  # 전체 서울
        >>> get_seoul_district_supply("data/공급.xlsx", "강남구")  # 강남구만
    """
    tool_instance = HousingSupplyTool(file_path)

    if tool_instance.df is None or tool_instance.df.empty:
        return "데이터 로드 실패"

    result = tool_instance.get_supply_by_district(
        district=district,
        district_column=district_column
    )

    title = f"서울 {district} 공급현황" if district else "서울 전체 공급현황"
    return tool_instance.format_output(result, title)


@tool
def get_supply_summary_by_district(
    file_path: str,
    district_column: str = "시군구",
    value_column: str = "공급량"
) -> str:
    """
    서울 25개 구별 공급현황을 요약합니다.

    각 구의 총 공급량을 집계하여 많은 순으로 정렬합니다.

    Args:
        file_path: 공급 데이터 파일 경로
        district_column: 구 이름 컬럼명
        value_column: 집계할 값 컬럼명 (예: "공급량", "세대수")

    Returns:
        구별 공급량 요약

    Examples:
        >>> get_supply_summary_by_district("data/공급.xlsx", value_column="세대수")
    """
    tool_instance = HousingSupplyTool(file_path)

    if tool_instance.df is None or tool_instance.df.empty:
        return "데이터 로드 실패"

    summary = tool_instance.get_summary_by_district(
        district_column=district_column,
        value_column=value_column
    )

    return tool_instance.format_output(summary, "서울 구별 공급 요약")


@tool
def analyze_yearly_supply(
    file_path: str,
    district: Optional[str] = None,
    date_column: str = "연월",
    value_column: str = "공급량"
) -> str:
    """
    연도별 주택공급량을 분석합니다.

    이 도구는 시계열 데이터에서 연도별 총공급량, 평균공급량을 집계합니다.

    Args:
        file_path: 공급 데이터 파일 경로
        district: 특정 구 이름 (None이면 서울 전체)
        date_column: 날짜 컬럼명 (기본값: "연월")
        value_column: 집계할 값 컬럼명 (기본값: "공급량")

    Returns:
        연도별 공급량 분석 결과

    Examples:
        >>> analyze_yearly_supply("data/공급.xlsx")  # 서울 전체 연도별
        >>> analyze_yearly_supply("data/공급.xlsx", "강남구")  # 강남구만
    """
    tool_instance = HousingSupplyTool(file_path)

    if tool_instance.df is None or tool_instance.df.empty:
        return "데이터 로드 실패"

    result = tool_instance.get_yearly_analysis(
        district=district,
        date_column=date_column,
        value_column=value_column
    )

    title = f"{district} 연도별 공급량" if district else "서울 전체 연도별 공급량"
    return tool_instance.format_output(result, title)


@tool
def analyze_monthly_pattern(
    file_path: str,
    district: Optional[str] = None,
    date_column: str = "연월",
    value_column: str = "공급량"
) -> str:
    """
    월별 주택공급 패턴을 분석합니다.

    전체 기간의 데이터를 월별로 집계하여 계절별 공급 패턴을 파악합니다.

    Args:
        file_path: 공급 데이터 파일 경로
        district: 특정 구 이름 (None이면 서울 전체)
        date_column: 날짜 컬럼명 (기본값: "연월")
        value_column: 집계할 값 컬럼명 (기본값: "공급량")

    Returns:
        월별 평균 공급량 분석 결과

    Examples:
        >>> analyze_monthly_pattern("data/공급.xlsx")
        >>> analyze_monthly_pattern("data/공급.xlsx", "서초구")
    """
    tool_instance = HousingSupplyTool(file_path)

    if tool_instance.df is None or tool_instance.df.empty:
        return "데이터 로드 실패"

    result = tool_instance.get_monthly_analysis(
        district=district,
        date_column=date_column,
        value_column=value_column
    )

    title = f"{district} 월별 공급 패턴" if district else "서울 전체 월별 공급 패턴"
    return tool_instance.format_output(result, title)


@tool
def compare_districts_supply(
    file_path: str,
    districts: str,  # 쉼표로 구분된 구 이름들
    date_column: Optional[str] = None,
    district_column: str = "시군구",
    value_column: str = "공급량"
) -> str:
    """
    여러 구의 주택공급량을 비교 분석합니다.

    선택한 구들의 공급량을 비교하여 지역별 차이를 파악합니다.

    Args:
        file_path: 공급 데이터 파일 경로
        districts: 비교할 구 목록 (쉼표로 구분, 예: "강남구,서초구,송파구")
        date_column: 날짜 컬럼명 (있으면 시계열 비교)
        district_column: 구 컬럼명 (기본값: "시군구")
        value_column: 집계할 값 컬럼명 (기본값: "공급량")

    Returns:
        구별 비교 분석 결과

    Examples:
        >>> compare_districts_supply("data/공급.xlsx", "강남구,서초구,송파구")
        >>> compare_districts_supply("data/공급.xlsx", "강남구,서초구", date_column="연월")
    """
    tool_instance = HousingSupplyTool(file_path)

    if tool_instance.df is None or tool_instance.df.empty:
        return "데이터 로드 실패"

    # 쉼표로 구분된 구 이름을 리스트로 변환
    district_list = [d.strip() for d in districts.split(",")]

    result = tool_instance.get_district_comparison(
        districts=district_list,
        date_column=date_column,
        district_column=district_column,
        value_column=value_column
    )

    return tool_instance.format_output(result, f"구별 공급량 비교 ({', '.join(district_list)})")


@tool
def generate_supply_report(
    file_path: str,
    date_column: Optional[str] = "연월",
    district_column: str = "시군구",
    value_column: str = "공급량"
) -> str:
    """
    서울시 주택공급 현황 종합 리포트를 생성합니다.

    전체 통계, 연도별 추이, 구별 순위 등을 포함한 종합 보고서를 생성합니다.

    Args:
        file_path: 공급 데이터 파일 경로
        date_column: 날짜 컬럼명
        district_column: 구 컬럼명
        value_column: 집계할 값 컬럼명

    Returns:
        종합 리포트

    Examples:
        >>> generate_supply_report("data/공급.xlsx")
    """
    tool_instance = HousingSupplyTool(file_path)

    if tool_instance.df is None or tool_instance.df.empty:
        return "데이터 로드 실패"

    output = []
    output.append("=" * 80)
    output.append("서울시 주택공급 현황 종합 리포트")
    output.append("=" * 80)

    # 서울 데이터 필터링
    seoul_df = tool_instance.filter_seoul_districts(tool_instance.df, district_column)

    # 1. 기본 통계
    output.append("\n[1] 기본 통계")
    output.append("-" * 80)
    if value_column in seoul_df.columns:
        total = seoul_df[value_column].sum()
        avg = seoul_df[value_column].mean()
        max_val = seoul_df[value_column].max()
        min_val = seoul_df[value_column].min()

        output.append(f"  총 공급량: {total:,.0f}")
        output.append(f"  평균 공급량: {avg:,.2f}")
        output.append(f"  최대 공급량: {max_val:,.0f}")
        output.append(f"  최소 공급량: {min_val:,.0f}")

    # 2. 기간 정보
    if date_column and date_column in seoul_df.columns:
        output.append("\n[2] 분석 기간")
        output.append("-" * 80)
        seoul_df = tool_instance.prepare_date_columns(seoul_df, date_column)
        if date_column in seoul_df.columns:
            try:
                min_date = seoul_df[date_column].min()
                max_date = seoul_df[date_column].max()
                output.append(f"  시작: {min_date}")
                output.append(f"  종료: {max_date}")
                years = (max_date - min_date).days / 365
                output.append(f"  기간: 약 {years:.1f}년")
            except:
                pass

    # 3. 구별 TOP 5
    output.append("\n[3] 구별 공급량 TOP 5")
    output.append("-" * 80)
    district_summary = tool_instance.get_summary_by_district(
        district_column=district_column,
        value_column=value_column
    )
    if not district_summary.empty:
        top5 = district_summary.head(5)
        for idx, row in enumerate(top5.iterrows(), 1):
            output.append(f"  {idx}. {row[1][district_column]}: {row[1][value_column]:,.0f}")

    # 4. 연도별 추이
    if date_column:
        output.append("\n[4] 연도별 공급량 추이")
        output.append("-" * 80)
        yearly = tool_instance.get_yearly_analysis(
            date_column=date_column,
            value_column=value_column
        )
        if not yearly.empty:
            for idx, row in yearly.iterrows():
                output.append(f"  {int(row['연도'])}년: {row['총공급량']:,.0f}")

    output.append("\n" + "=" * 80)
    output.append(f"리포트 생성 완료 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    output.append("=" * 80)

    return "\n".join(output)


# 편의 함수
def get_housing_supply_tools():
    """주택공급 도구 목록 반환 (전체)"""
    return [
        load_housing_supply_data,
        get_seoul_district_supply,
        get_supply_summary_by_district,
        analyze_yearly_supply,
        analyze_monthly_pattern,
        compare_districts_supply,
        generate_supply_report
    ]


def get_basic_supply_tools():
    """기본 주택공급 도구 목록 반환"""
    return [
        load_housing_supply_data,
        get_seoul_district_supply,
        get_supply_summary_by_district
    ]


def get_advanced_supply_tools():
    """고급 주택공급 분석 도구 목록 반환"""
    return [
        analyze_yearly_supply,
        analyze_monthly_pattern,
        compare_districts_supply,
        generate_supply_report
    ]


if __name__ == "__main__":
    # 테스트 코드
    print("=" * 80)
    print("주택공급 Tool 테스트")
    print("=" * 80)

    # 예제 데이터 생성
    import pandas as pd

    sample_data = pd.DataFrame({
        "시군구": [
            "서울특별시 강남구", "서울특별시 서초구", "서울특별시 송파구",
            "경기도 성남시", "서울특별시 강동구"
        ],
        "연도": [2024, 2024, 2024, 2024, 2024],
        "공급량": [1000, 800, 1200, 1500, 600]
    })

    # 임시 파일 저장
    test_file = "test_supply.xlsx"
    sample_data.to_excel(test_file, index=False)

    print(f"\n📝 테스트 데이터 생성: {test_file}")
    print(sample_data)

    print("\n[1] 서울 전체 공급현황")
    result = get_seoul_district_supply.invoke({
        "file_path": test_file
    })
    print(result)

    print("\n[2] 강남구 공급현황")
    result = get_seoul_district_supply.invoke({
        "file_path": test_file,
        "district": "강남구"
    })
    print(result)

    print("\n[3] 구별 공급 요약")
    result = get_supply_summary_by_district.invoke({
        "file_path": test_file,
        "value_column": "공급량"
    })
    print(result)

    # 임시 파일 삭제
    os.remove(test_file)
    print(f"\n🗑️ 테스트 파일 삭제: {test_file}")
