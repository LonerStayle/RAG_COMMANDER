"""
한국 및 미국 금리 조회 도구

이 모듈은 FRED API(미국)와 ECOS API(한국)를 사용하여
주요 금리 데이터를 조회하는 LangChain tool을 제공합니다.
"""

from typing import Optional, List, Dict, Any, Literal
from langchain_core.tools import tool
from dotenv import load_dotenv
import requests
import os
import json
from datetime import datetime, timedelta
import pandas as pd

load_dotenv()


class InterestRateTool:
    """금리 조회 클래스"""

    def __init__(self):
        # API 키 가져오기 (공백 제거)
        self.fred_api_key = os.getenv("FRED_API_KEY", "").strip()
        self.ecos_api_key = os.getenv("ECOS_API_KEY", "").strip()
        self.fred_base_url = "https://api.stlouisfed.org/fred/series/observations"

        # FRED 시리즈 ID
        self.fred_series = {
            "base_rate": "FEDFUNDS",  # 미국 기준금리
            "10y_treasury": "DGS10",   # 10년물 국채 수익률
        }

        # 디버깅 정보 출력
        if not self.fred_api_key:
            print("⚠️ FRED_API_KEY가 설정되지 않았습니다.")
        else:
            print(f"✅ FRED_API_KEY 로드 완료 (길이: {len(self.fred_api_key)})")

        if not self.ecos_api_key:
            print("⚠️ ECOS_API_KEY가 설정되지 않았습니다.")
        else:
            print(f"✅ ECOS_API_KEY 로드 완료 (길이: {len(self.ecos_api_key)})")

    def get_us_rates(
        self,
        rate_type: Literal["base_rate", "10y_treasury"] = "base_rate",
        months: int = 12,
        frequency: str = "m"
    ) -> List[Dict[str, Any]]:
        """
        미국 금리 데이터 조회 (FRED API)

        Args:
            rate_type: 금리 종류 ("base_rate" or "10y_treasury")
            months: 조회할 기간 (개월 수)
            frequency: 데이터 주기 (d: 일별, m: 월별, q: 분기별, a: 연간)

        Returns:
            금리 데이터 리스트 [{"date": "YYYY-MM-DD", "value": "X.XX"}]
        """
        if not self.fred_api_key:
            raise ValueError("FRED_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

        series_id = self.fred_series.get(rate_type)
        if not series_id:
            raise ValueError(f"유효하지 않은 rate_type: {rate_type}")

        # 시작 날짜 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)

        params = {
            "series_id": series_id,
            "api_key": self.fred_api_key,
            "file_type": "json",
            "frequency": frequency,
            "observation_start": start_date.strftime("%Y-%m-%d"),
        }

        print(f"🔍 FRED API 요청: {series_id} ({rate_type})")
        print(f"📅 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        try:
            response = requests.get(self.fred_base_url, params=params)
            print(f"📥 응답 상태 코드: {response.status_code}")

            response.raise_for_status()

            data = response.json()
            observations = data.get("observations", [])

            if not observations:
                print(f"⚠️ 데이터가 없습니다. 응답: {data}")
                return []

            # "." 값 제거 (데이터 없음)
            results = []
            for obs in observations:
                if obs["value"] != ".":
                    try:
                        results.append({
                            "date": obs["date"],
                            "value": float(obs["value"])
                        })
                    except (ValueError, KeyError) as e:
                        print(f"⚠️ 데이터 파싱 오류: {e}, 데이터: {obs}")
                        continue

            print(f"✅ {len(results)}개 데이터 로드 완료 (전체 {len(observations)}개 중)")
            return results

        except requests.exceptions.RequestException as e:
            print(f"❌ FRED API 요청 중 오류: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"응답 내용: {e.response.text[:500]}")
            return []
        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ 데이터 파싱 오류: {e}")
            return []

    def get_korea_rate(
        self,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """
        한국 기준금리 조회 (ECOS API)

        Args:
            months: 조회할 기간 (개월 수)

        Returns:
            금리 데이터 리스트 [{"date": "YYYY-MM", "value": "X.XX"}]
        """
        if not self.ecos_api_key:
            raise ValueError("ECOS_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

        # 날짜 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)

        # ECOS API URL 구성
        # API: StatisticSearch
        # 인증키: self.ecos_api_key
        # 요청유형: json
        # 언어: kr
        # 요청시작건수: 1
        # 요청종료건수: 1000
        # 통계표코드: 722Y001 (한국은행 기준금리)
        # 주기: M (월간)
        # 검색시작일자: YYYYMM
        # 검색종료일자: YYYYMM

        start_ym = start_date.strftime('%Y%m')
        end_ym = end_date.strftime('%Y%m')

        url = f"https://ecos.bok.or.kr/api/StatisticSearch/{self.ecos_api_key}/json/kr/1/1000/722Y001/M/{start_ym}/{end_ym}"

        print(f"🔍 ECOS API 요청 URL: {url}")

        try:
            response = requests.get(url)
            print(f"📥 응답 상태 코드: {response.status_code}")

            response.raise_for_status()

            data = response.json()
            print(f"📦 응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")

            # ECOS API 응답 구조 확인
            if "StatisticSearch" not in data:
                print(f"❌ ECOS API 응답 오류: {data}")
                return []

            rows = data["StatisticSearch"].get("row", [])

            if not rows:
                print("⚠️ 데이터가 비어있습니다.")
                return []

            results = []
            for row in rows:
                try:
                    results.append({
                        "date": row["TIME"],  # YYYYMM 형식
                        "value": float(row["DATA_VALUE"])
                    })
                except (KeyError, ValueError) as e:
                    print(f"⚠️ 행 파싱 오류: {e}, 행: {row}")
                    continue

            print(f"✅ {len(results)}개 데이터 로드 완료")
            return results

        except requests.exceptions.RequestException as e:
            print(f"❌ ECOS API 요청 중 오류: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"응답 내용: {e.response.text}")
            return []
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"❌ 데이터 파싱 오류: {e}")
            return []

    def compare_rates(
        self,
        months: int = 12
    ) -> Dict[str, Any]:
        """
        한미 금리 비교

        Args:
            months: 조회할 기간 (개월 수)

        Returns:
            비교 결과 딕셔너리
        """
        us_rates = self.get_us_rates("base_rate", months)
        kr_rates = self.get_korea_rate(months)

        if not us_rates or not kr_rates:
            return {
                "error": "데이터 조회 실패",
                "us_data_count": len(us_rates),
                "kr_data_count": len(kr_rates)
            }

        # 최신 값
        latest_us = us_rates[-1] if us_rates else None
        latest_kr = kr_rates[-1] if kr_rates else None

        result = {
            "period_months": months,
            "latest_us_rate": latest_us,
            "latest_kr_rate": latest_kr,
            "rate_spread": None,
            "is_inverted": None,
            "us_trend": self._calculate_trend(us_rates),
            "kr_trend": self._calculate_trend(kr_rates),
        }

        if latest_us and latest_kr:
            spread = latest_us["value"] - latest_kr["value"]
            result["rate_spread"] = round(spread, 2)
            result["is_inverted"] = spread > 0  # 미국 금리가 더 높으면 역전

        return result

    def _calculate_trend(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """금리 추세 계산"""
        if len(data) < 2:
            return {"trend": "insufficient_data"}

        first_value = data[0]["value"]
        last_value = data[-1]["value"]
        change = last_value - first_value
        change_pct = (change / first_value * 100) if first_value != 0 else 0

        return {
            "first_value": first_value,
            "last_value": last_value,
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
            "direction": "up" if change > 0 else "down" if change < 0 else "flat"
        }

    def format_rates(self, data: List[Dict[str, Any]], title: str) -> str:
        """금리 데이터 포맷팅"""
        if not data:
            return f"{title}: 데이터 없음"

        formatted = [f"\n{'='*60}"]
        formatted.append(f"{title}")
        formatted.append('='*60)

        # 최근 12개만 표시
        recent_data = data[-12:]
        for item in recent_data:
            formatted.append(f"날짜: {item['date']}, 금리: {item['value']}%")

        formatted.append(f"\n총 {len(data)}개 데이터 중 최근 {len(recent_data)}개 표시")
        formatted.append('='*60)

        return "\n".join(formatted)


# LangChain tool로 래핑
@tool
def get_us_interest_rate(
    rate_type: Literal["base_rate", "10y_treasury"] = "base_rate",
    months: int = 12
) -> str:
    """
    미국 금리 데이터를 조회합니다.

    이 도구는 FRED(연방준비제도) API를 사용하여 미국의 기준금리나
    10년물 국채 수익률을 조회합니다.

    Args:
        rate_type: 금리 종류
            - "base_rate": 미국 기준금리 (FEDFUNDS)
            - "10y_treasury": 10년물 국채 수익률 (DGS10)
        months: 조회할 기간 (개월 수, 기본값: 12)

    Returns:
        금리 데이터 (날짜와 금리 값 포함)

    Examples:
        >>> get_us_interest_rate("base_rate", 12)
        >>> get_us_interest_rate("10y_treasury", 6)
    """
    tool_instance = InterestRateTool()
    data = tool_instance.get_us_rates(rate_type, months)

    rate_name = "미국 기준금리" if rate_type == "base_rate" else "미국 10년물 국채 수익률"
    return tool_instance.format_rates(data, rate_name)


@tool
def get_korea_interest_rate(months: int = 12) -> str:
    """
    한국 기준금리 데이터를 조회합니다.

    이 도구는 ECOS(한국은행 경제통계시스템) API를 사용하여
    한국의 기준금리를 조회합니다.

    Args:
        months: 조회할 기간 (개월 수, 기본값: 12)

    Returns:
        금리 데이터 (날짜와 금리 값 포함)

    Examples:
        >>> get_korea_interest_rate(12)
        >>> get_korea_interest_rate(24)
    """
    tool_instance = InterestRateTool()
    data = tool_instance.get_korea_rate(months)
    return tool_instance.format_rates(data, "한국 기준금리")


@tool
def compare_korea_us_rates(months: int = 12) -> str:
    """
    한국과 미국의 기준금리를 비교합니다.

    이 도구는 한미 금리를 비교하여 금리 격차, 역전 여부, 추세 등을
    분석합니다.

    Args:
        months: 조회할 기간 (개월 수, 기본값: 12)

    Returns:
        한미 금리 비교 분석 결과

    Examples:
        >>> compare_korea_us_rates(12)
        >>> compare_korea_us_rates(24)
    """
    tool_instance = InterestRateTool()
    result = tool_instance.compare_rates(months)

    if "error" in result:
        return f"오류: {result['error']}"

    formatted = [f"\n{'='*60}"]
    formatted.append(f"한미 금리 비교 분석 (최근 {months}개월)")
    formatted.append('='*60)

    if result["latest_us_rate"]:
        formatted.append(f"\n[미국 기준금리]")
        formatted.append(f"  최신: {result['latest_us_rate']['value']}% ({result['latest_us_rate']['date']})")
        if result["us_trend"]:
            trend = result["us_trend"]
            formatted.append(f"  추세: {trend['direction']} ({trend['change']:+.2f}%p, {trend['change_percent']:+.2f}%)")

    if result["latest_kr_rate"]:
        formatted.append(f"\n[한국 기준금리]")
        formatted.append(f"  최신: {result['latest_kr_rate']['value']}% ({result['latest_kr_rate']['date']})")
        if result["kr_trend"]:
            trend = result["kr_trend"]
            formatted.append(f"  추세: {trend['direction']} ({trend['change']:+.2f}%p, {trend['change_percent']:+.2f}%)")

    if result["rate_spread"] is not None:
        formatted.append(f"\n[금리 격차]")
        formatted.append(f"  미국 - 한국: {result['rate_spread']:+.2f}%p")
        formatted.append(f"  금리 역전: {'예 (미국 > 한국)' if result['is_inverted'] else '아니오 (한국 >= 미국)'}")

    formatted.append('='*60)

    return "\n".join(formatted)


# 편의 함수
def get_interest_rate_tools():
    """금리 조회 도구 목록 반환"""
    return [
        get_us_interest_rate,
        get_korea_interest_rate,
        compare_korea_us_rates
    ]


if __name__ == "__main__":
    # 테스트 코드
    print("=" * 80)
    print("금리 조회 Tool 테스트")
    print("=" * 80)

    print("\n[1] 미국 기준금리 조회")
    result = get_us_interest_rate.invoke({"rate_type": "base_rate", "months": 12})
    print(result)

    print("\n[2] 한국 기준금리 조회")
    result = get_korea_interest_rate.invoke({"months": 12})
    print(result)

    print("\n[3] 한미 금리 비교")
    result = compare_korea_us_rates.invoke({"months": 12})
    print(result)
