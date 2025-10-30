import requests
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
ECOS_API_KEY = os.getenv("ECOS_API_KEY")


# --- FRED 데이터 가져오기 (미국) ---
def _get_fred_data(series_id, start_date="2015-01-01"):
    base_url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "frequency": "m"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        observations = data.get("observations", [])
        df = pd.DataFrame(observations)
        df = df[df['value'] != '.']
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'])
        return df[['date', 'value']]
    except Exception as e:
        print(f"FRED API 오류 ({series_id}): {e}")
        return None


# --- 한국은행 데이터 가져오기 ---
def _get_ecos_data(start_date="201501"):
    if not ECOS_API_KEY:
        print(" ECOS_API_KEY가 설정되지 않았습니다.")
        return None

    base_url = "https://ecos.bok.or.kr/api/StatisticSearch"
    try:
        url = f"{base_url}/{ECOS_API_KEY}/json/kr/1/1000/722Y001/M/{start_date}/{datetime.now().strftime('%Y%m')}/0101000"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
            rows = data['StatisticSearch']['row']
            df = pd.DataFrame(rows)
            df['date'] = pd.to_datetime(df['TIME'], format='%Y%m')
            df['value'] = pd.to_numeric(df['DATA_VALUE'])
            return df[['date', 'value']]
        else:
            return None
    except Exception as e:
        print(f" 한국은행 API 오류: {e}")
        return None


# --- 메인 비교 함수 ---
def _compare_interest_rates():
    """한·미 기준금리 데이터를 JSON 형태로 반환"""
    kr_rate = _get_ecos_data("201501")
    us_rate = _get_fred_data("FEDFUNDS", "2015-01-01")

    if kr_rate is None and us_rate is None:
        return {"error": "데이터를 가져오지 못했습니다."}

    merged = None
    if kr_rate is not None:
        kr_rate = kr_rate.rename(columns={'value': '한국_기준금리'})
        merged = kr_rate
    if us_rate is not None:
        us_rate = us_rate.rename(columns={'value': '미국_기준금리'})
        merged = us_rate if merged is None else pd.merge(merged, us_rate, on='date', how='outer')

    merged = merged.sort_values('date')
    merged['연월'] = merged['date'].dt.strftime('%Y-%m')

    # JSON 변환
    data_json = {
        "meta": {
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(merged)
        },
        "data": [
            {
                "date": row['연월'],
                "kr_rate": round(row['한국_기준금리'], 2) if pd.notna(row.get('한국_기준금리')) else None,
                "us_rate": round(row['미국_기준금리'], 2) if pd.notna(row.get('미국_기준금리')) else None
            }
            for _, row in merged.iterrows()
        ]
    }

    return data_json

import json
def get_rate():
    result = _compare_interest_rates()
    result["data"] = sorted(result["data"], key=lambda x: x["date"], reverse=True)
    return json.dumps(result, ensure_ascii=False, indent=2)


