# 주택공급 현황 분석 도구 (Housing Supply Tool)

서울시 25개 구의 주택공급 데이터를 분석하는 LangChain 도구 모음입니다.

---

## 📋 목차

1. [설치 및 설정](#설치-및-설정)
2. [기본 도구](#기본-도구)
3. [고급 분석 도구](#고급-분석-도구)
4. [사용 예제](#사용-예제)
5. [데이터 형식 요구사항](#데이터-형식-요구사항)

---

## 설치 및 설정

### 필요한 패키지

```bash
pip install pandas openpyxl langchain-core matplotlib
```

### import

```python
from tools.housing_supply_tool import (
    load_housing_supply_data,
    get_seoul_district_supply,
    get_supply_summary_by_district,
    analyze_yearly_supply,
    analyze_monthly_pattern,
    compare_districts_supply,
    generate_supply_report,
    get_housing_supply_tools  # 전체 도구 리스트
)
```

---

## 기본 도구

### 1. load_housing_supply_data

데이터 파일을 로드하고 기본 정보를 확인합니다.

```python
from tools.housing_supply_tool import load_housing_supply_data

result = load_housing_supply_data.invoke({
    "file_path": "data/공급현황.xlsx"
})
print(result)
```

**Args:**
- `file_path` (str): Excel 또는 CSV 파일 경로

**Returns:**
- 데이터 로드 결과 및 기본 정보

---

### 2. get_seoul_district_supply

서울 25개 구의 공급 데이터를 조회합니다.

```python
from tools.housing_supply_tool import get_seoul_district_supply

# 서울 전체
result = get_seoul_district_supply.invoke({
    "file_path": "data/공급현황.xlsx"
})

# 특정 구만
result = get_seoul_district_supply.invoke({
    "file_path": "data/공급현황.xlsx",
    "district": "강남구"
})
```

**Args:**
- `file_path` (str): 데이터 파일 경로
- `district` (Optional[str]): 특정 구 이름 (None이면 전체)
- `district_column` (str): 구 컬럼명 (기본값: "시군구")

**Returns:**
- 서울 구별 공급 데이터

---

### 3. get_supply_summary_by_district

구별 공급량을 집계하여 순위를 보여줍니다.

```python
from tools.housing_supply_tool import get_supply_summary_by_district

result = get_supply_summary_by_district.invoke({
    "file_path": "data/공급현황.xlsx",
    "value_column": "세대수"
})
```

**Args:**
- `file_path` (str): 데이터 파일 경로
- `district_column` (str): 구 컬럼명 (기본값: "시군구")
- `value_column` (str): 집계할 값 컬럼명 (기본값: "공급량")

**Returns:**
- 구별 총 공급량 (많은 순으로 정렬)

---

## 고급 분석 도구

### 4. analyze_yearly_supply

연도별 공급량 추이를 분석합니다.

```python
from tools.housing_supply_tool import analyze_yearly_supply

# 서울 전체 연도별
result = analyze_yearly_supply.invoke({
    "file_path": "data/공급현황.xlsx",
    "date_column": "연월",
    "value_column": "공급량"
})

# 특정 구의 연도별
result = analyze_yearly_supply.invoke({
    "file_path": "data/공급현황.xlsx",
    "district": "강남구",
    "date_column": "연월"
})
```

**Args:**
- `file_path` (str): 데이터 파일 경로
- `district` (Optional[str]): 특정 구 (None이면 서울 전체)
- `date_column` (str): 날짜 컬럼명 (기본값: "연월")
- `value_column` (str): 집계 값 컬럼명 (기본값: "공급량")

**Returns:**
- 연도별 총공급량, 평균공급량, 데이터건수

**출력 예시:**
```
================================================================================
서울 전체 연도별 공급량
================================================================================
총 10건

연도  총공급량  평균공급량  데이터건수
2015   12000     1000        120
2016   15000     1250        120
2017   13500     1125        120
...
================================================================================
```

---

### 5. analyze_monthly_pattern

월별 공급 패턴을 분석합니다 (계절성 파악).

```python
from tools.housing_supply_tool import analyze_monthly_pattern

result = analyze_monthly_pattern.invoke({
    "file_path": "data/공급현황.xlsx",
    "district": "서초구"
})
```

**Args:**
- `file_path` (str): 데이터 파일 경로
- `district` (Optional[str]): 특정 구 (None이면 서울 전체)
- `date_column` (str): 날짜 컬럼명 (기본값: "연월")
- `value_column` (str): 집계 값 컬럼명 (기본값: "공급량")

**Returns:**
- 월별 평균공급량, 총공급량, 데이터건수

**출력 예시:**
```
================================================================================
서울 전체 월별 공급 패턴
================================================================================
총 12건

 월  평균공급량  총공급량  데이터건수
  1       950    9500        50
  2      1050   10500        50
  3      1200   12000        50
...
================================================================================
```

---

### 6. compare_districts_supply

여러 구의 공급량을 비교합니다.

```python
from tools.housing_supply_tool import compare_districts_supply

# 강남3구 비교
result = compare_districts_supply.invoke({
    "file_path": "data/공급현황.xlsx",
    "districts": "강남구,서초구,송파구",
    "date_column": "연월"
})
```

**Args:**
- `file_path` (str): 데이터 파일 경로
- `districts` (str): 쉼표로 구분된 구 이름들 (예: "강남구,서초구,송파구")
- `date_column` (Optional[str]): 날짜 컬럼 (시계열 비교)
- `district_column` (str): 구 컬럼명 (기본값: "시군구")
- `value_column` (str): 집계 값 컬럼명 (기본값: "공급량")

**Returns:**
- 구별 비교 데이터 (시계열이면 연도별, 아니면 총합)

**출력 예시:**
```
================================================================================
구별 공급량 비교 (강남구, 서초구, 송파구)
================================================================================
총 30건

연도  공급량      구
2015  1200   강남구
2015   980   서초구
2015  1450   송파구
...
================================================================================
```

---

### 7. generate_supply_report

종합 리포트를 생성합니다.

```python
from tools.housing_supply_tool import generate_supply_report

result = generate_supply_report.invoke({
    "file_path": "data/공급현황.xlsx",
    "date_column": "연월",
    "district_column": "시군구",
    "value_column": "공급량"
})
```

**Args:**
- `file_path` (str): 데이터 파일 경로
- `date_column` (Optional[str]): 날짜 컬럼명
- `district_column` (str): 구 컬럼명 (기본값: "시군구")
- `value_column` (str): 집계 값 컬럼명 (기본값: "공급량")

**Returns:**
- 종합 분석 리포트 (기본 통계, 기간, TOP 5 구, 연도별 추이)

**출력 예시:**
```
================================================================================
서울시 주택공급 현황 종합 리포트
================================================================================

[1] 기본 통계
--------------------------------------------------------------------------------
  총 공급량: 150,000
  평균 공급량: 1,250.00
  최대 공급량: 5,000
  최소 공급량: 100

[2] 분석 기간
--------------------------------------------------------------------------------
  시작: 2015-01-01
  종료: 2024-12-31
  기간: 약 10.0년

[3] 구별 공급량 TOP 5
--------------------------------------------------------------------------------
  1. 송파구: 18,500
  2. 강남구: 15,200
  3. 서초구: 12,800
  4. 강서구: 11,500
  5. 양천구: 10,300

[4] 연도별 공급량 추이
--------------------------------------------------------------------------------
  2015년: 12,000
  2016년: 15,000
  2017년: 13,500
  ...

================================================================================
리포트 생성 완료 (2025-10-29 15:30:00)
================================================================================
```

---

## 사용 예제

### Agent에서 사용하기

```python
from langchain.agents import create_tool_calling_agent
from langchain_openai import ChatOpenAI
from tools.housing_supply_tool import get_housing_supply_tools

# LLM 초기화
llm = ChatOpenAI(model="gpt-4", temperature=0)

# 도구 가져오기
tools = get_housing_supply_tools()

# Agent 생성
agent = create_tool_calling_agent(llm, tools, prompt)

# 실행
result = agent.invoke({
    "input": "서울시 강남구의 연도별 주택 공급량을 분석해주세요"
})
```

### 직접 호출

```python
from tools.housing_supply_tool import analyze_yearly_supply

result = analyze_yearly_supply.invoke({
    "file_path": "data/공급현황.xlsx",
    "district": "강남구",
    "date_column": "연월",
    "value_column": "세대수"
})

print(result)
```

---

## 데이터 형식 요구사항

### 필수 컬럼

#### 기본 도구용

| 컬럼명 예시 | 설명 | 필수여부 |
|-----------|------|---------|
| `시군구` 또는 `지역` | 행정구역 정보 | ✅ 필수 |
| `공급량` 또는 `세대수` | 공급량 값 | ✅ 필수 |

#### 고급 분석 도구용 (시계열 분석)

| 컬럼명 예시 | 설명 | 필수여부 |
|-----------|------|---------|
| `연월` 또는 `날짜` | 날짜 정보 (YYYY-MM, YYYYMM 등) | ✅ 필수 |
| `시군구` 또는 `지역` | 행정구역 정보 | ✅ 필수 |
| `공급량` 또는 `세대수` | 공급량 값 | ✅ 필수 |

### 데이터 예시

#### Excel/CSV 형식

```csv
연월,시군구,공급량
2024-01,서울특별시 강남구,120
2024-01,서울특별시 서초구,95
2024-02,서울특별시 강남구,110
2024-02,서울특별시 서초구,100
...
```

또는

```csv
날짜,지역,세대수
202401,강남구,120
202401,서초구,95
202402,강남구,110
...
```

---

## 서울 25개 구 목록

도구는 다음 25개 구를 자동으로 인식하여 필터링합니다:

```
종로구, 중구, 용산구, 성동구, 광진구
동대문구, 중랑구, 성북구, 강북구, 도봉구
노원구, 은평구, 서대문구, 마포구, 양천구
강서구, 구로구, 금천구, 영등포구, 동작구
관악구, 서초구, 강남구, 송파구, 강동구
```

---

## 문제 해결

### Q1. "날짜 변환 실패" 에러

**원인:** 날짜 컬럼 형식이 인식되지 않음

**해결:**
- 날짜 형식을 확인하고 Excel에서 "2024-01" 또는 "202401" 형식으로 통일
- 또는 데이터 전처리 후 사용

### Q2. "컬럼을 찾을 수 없습니다" 에러

**원인:** 컬럼 이름이 다름

**해결:**
- `district_column`, `date_column`, `value_column` 파라미터로 실제 컬럼 이름 지정

```python
result = analyze_yearly_supply.invoke({
    "file_path": "data.xlsx",
    "date_column": "기준월",  # 실제 컬럼 이름
    "value_column": "신규세대수"  # 실제 컬럼 이름
})
```

### Q3. 서울 구가 제대로 필터링 안 됨

**원인:** 구 이름 형식이 다름

**해결:**
- 데이터의 구 이름이 "서울특별시 강남구" 또는 "강남구" 형태여야 함
- 다른 형태라면 데이터 전처리 필요

---

## 라이선스

MIT License

## 작성자

RAG Commander Team

## 최종 업데이트

2025-10-29
