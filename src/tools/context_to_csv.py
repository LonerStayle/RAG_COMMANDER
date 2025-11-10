import re, json
import pandas as pd
from utils.llm import LLMProfile
from utils.google_drive_uploader import upload_to_drive
from utils.util import get_data_dir

get_data_dir() / "temp"

# -------<01. 주택 청약 START>---------
# ['housing_faq']['housing_faq_context']
def housing_faq_context_to_drive(data_list):
    rows = []
    for block in data_list:
        pattern = r'Q\d*:\s*(.*?)\\nA\d*:\s*(.*?)(?=\\nQ\d*:|"$)'
        qa_pairs = re.findall(pattern, block)
        for q, a in qa_pairs:
            # 앞뒤 공백, 따옴표, 백슬래시 제거
            q_clean = q.strip().replace('\\"', '"').replace("\\\\n", "\n")
            a_clean = a.strip().replace('\\"', '"').replace("\\\\n", "\n")
            rows.append({"질문": q_clean, "답변": a_clean})


    df = pd.DataFrame(rows)
    df.to_csv("주택청약FAQ_temp.csv", index=False, encoding="utf-8-sig")
    link = upload_to_drive(data=df, filename="주택청약FAQ_temp.csv", mime_type="text/csv")
    print("📎 주택청약FAQ_temp.csv 링크:", link)
    return link

# ['housing_faq']['housing_rule_context']
def housing_rule_context_to_drive(data_list):
    content = "\n\n".join(data_list)
    prompt = f"""
    너는 대한민국 '주택공급규칙' 조문을 잘 정리하는 전문가야.

    다음은 여러 조문과 항목이 섞인 원문이야.
    이걸 사람이 보기 좋은 표 구조로 요약해줘.

    각 조문을 분석해 다음 필드로 구성된 JSON 배열로 출력해:
    - 조문명: "제35조(국민주택의 특별공급)" 같은 형식
    - 핵심요약: 핵심 내용 1~2줄
    - 주요조건: 핵심 조건들을 bullet 형태 리스트로
    - 적용대상: 조문이 다루는 대상 (있다면)
    - 비고: 부가 설명 또는 특이사항 (있다면)

    출력은 반드시 JSON 배열만으로 하세요.
    --- 원문 시작 ---
    {content}
    --- 원문 끝 ---
    """
    res = LLMProfile.dev_llm().invoke(prompt)
    summary_json = res.content
    rows = json.loads(summary_json)
    df = pd.DataFrame(rows)
    link = upload_to_drive(data=df, filename="주택공급규칙_temp.csv", mime_type="text/csv")
    print("📎 주택공급규칙_temp.csv 링크:", link)
    return link
# -------</01. 주택 청약 END>---------

# ------<02. 입지분석 START>-------
# ['location_insight']['kakao_api_distance_context']
def location_kakao_to_drive(data, address):
    rows = []
    base_addr = data["주소"]
    for category, value in data.items():
        if category in ("주소", "좌표"):
            continue

        if isinstance(value, dict):  # 예: 교육환경, 편의여건
            for subcat, items in value.items():
                for item in items:
                    rows.append({
                        "지역": base_addr,
                        "분류": category,
                        "세부유형": subcat,
                        "이름": item.get("이름"),
                        "주소": item.get("주소"),
                        "거리(미터)": item.get("거리(미터)")
                    })
        elif isinstance(value, list):  # 예: 교통여건, 자연환경, 미래가치
            for item in value:
                rows.append({
                    "지역": base_addr,
                    "분류": category,
                    "세부유형": None,
                    "이름": item.get("이름"),
                    "주소": item.get("주소"),
                    "거리(미터)": item.get("거리(미터)")
                })

    df = pd.DataFrame(rows, columns=["지역","분류","세부유형","이름","주소","거리(미터)"])

    lat = data["좌표"]["latitude"]
    lon = data["좌표"]["longitude"]

    footer = pd.DataFrame([
        {"지역": base_addr, "분류": "메타", "세부유형": "검색좌표", "이름": "위도", "주소": str(lat), "거리(미터)": None},
        {"지역": base_addr, "분류": "메타", "세부유형": "검색좌표", "이름": "경도", "주소": str(lon), "거리(미터)": None},
    ], columns=df.columns)


    final_df = pd.concat([df, footer], ignore_index=True)
    link = upload_to_drive(data=final_df, filename=f"{address}_입지분석_카카오_temp.csv", mime_type="text/csv")
    print("📎 입지분석_카카오_temp 링크:", link)
    return link
# ------</02. 입지분석 END>-------

# ------<03. 정책 START>-------
# ['policy_output']['region_context']
def region_news_to_drive(data_list):
    df = pd.DataFrame(data_list)
    link = upload_to_drive(data=df, filename="지역별_정책_모음_temp.csv", mime_type="text/csv")
    return link

# ['policy_output']['national_context']
def netional_news_to_drive(data_list):
    rows = []

    for item in data_list:
        date_match = re.search(r"날짜:\s*([0-9\-]+)", item)
        title_match = re.search(r"제목:\s*(.*?)\n링크:", item, re.DOTALL)
        link_match = re.search(r"링크:\s*(https?://[^\s]+)", item)

        date = date_match.group(1) if date_match else ""
        title = title_match.group(1).strip() if title_match else ""
        link = link_match.group(1).strip() if link_match else ""

        rows.append({
            "날짜": date,
            "제목": title,
            "링크": link
        })

    df = pd.DataFrame(rows)
    link = upload_to_drive(data=df, filename="국가적_정책_모음_temp.csv", mime_type="text/csv")
    print("📎 국가적_정책_모음_temp 링크:", link)
    return link
# ------</03. 정책END>-------

# ------<04. 공급과 수요>-------

# ['supply_demand']['jeonse_price']
def jense_to_drive(text: str):
    """
    자치구별 월별 데이터를 파싱해 '날짜(YYYY-MM)'와 '금액(원)'으로 CSV 저장
    """
    gu_match = re.search(r"자치구:\s*([^\n]+)", text)
    gu_name = gu_match.group(1).strip() if gu_match else "미상"

    pattern = r"(\d{4})년\s*(\d{1,2})월:\s*([\d\.]+)"
    rows = []

    for year, month, value in re.findall(pattern, text):
        date_str = f"{year}-{int(month):02d}"  # YYYY-MM 형식
        amount_won = float(value) * 1000        # 천원 → 원 변환
        rows.append({
            "자치구": gu_name,
            "날짜": date_str,
            "금액(원)": int(amount_won)
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(by="날짜", ascending=False).reset_index(drop=True)
    link = upload_to_drive(data=df, filename=f"{gu_name}_월별_전세가격_temp.csv", mime_type="text/csv")
    return link

# ['supply_demand']['sale_price']
def sales_to_drive(text: str):
    """
    자치구별 월별 데이터를 파싱해 '날짜(YYYY-MM)'와 '금액(원)'으로 CSV 저장
    """
    gu_match = re.search(r"자치구:\s*([^\n]+)", text)
    gu_name = gu_match.group(1).strip() if gu_match else "미상"

    pattern = r"(\d{4})년\s*(\d{1,2})월:\s*([\d\.]+)"
    rows = []

    for year, month, value in re.findall(pattern, text):
        date_str = f"{year}-{int(month):02d}" 
        amount_won = float(value) * 1000       
        rows.append({
            "자치구": gu_name,
            "날짜": date_str,
            "금액(원)": int(amount_won)
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(by="날짜", ascending=False).reset_index(drop=True)
    link = upload_to_drive(data=df, filename=f"{gu_name}_월별_매매가격_temp.csv", mime_type="text/csv")
    print("📎 _월별_매매가격_temp 링크:", link)
    return link

# ['supply_demand']['use_kor_rate']
def rate_to_drive(data_list):
    df = pd.DataFrame(data_list)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")  
    df = df.sort_values("date", ascending=False)  

    link = upload_to_drive(
        data=df,
        filename="미국_한국_금리_temp.csv",
        mime_type="text/csv"
    )
    return link

# ['supply_demand']['home_mortgage']
def home_mortagage_to_drive(data_list):
    records = []
    for item in data_list:
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", item)
        avg_match = re.search(r"대출평균\(연%\):\s*([\d.]+)", item)
        house_match = re.search(r"주택담보대출\(연%\):\s*([\d.]+)", item)
        personal_match = re.search(r"가계대출\(연%\):\s*([\d.]+)", item)

        if date_match and avg_match and personal_match and house_match:
            records.append({
                "날짜": date_match.group(1),
                "가계대출_평균(연%)": float(avg_match.group(1)),
                "주택담보대출(연%)": float(house_match.group(1)),
                "가계대출(%)": float(personal_match.group(1))
            })

    df = pd.DataFrame(records)
    df = df.sort_values("날짜",ascending=False)

    link = upload_to_drive(
        data=df,
        filename="주택담보대출_temp.csv",
        mime_type="text/csv"
    )
    print("📎 주택담보대출_temp 링크:", link)
    return link

# ['supply_demand']['housing_sales_volume']
def housing_sales_volume_to_drive(data_list,address):
    records = []
    for block in data_list:
        meta = {}
        meta["행정구역별"] = re.search(r"행정구역별:\s*(\S+)", block).group(1)
        meta["매입자거주지"] = re.search(r"매입자거주지:\s*(\S+)", block).group(1)
        meta["항목"] = re.search(r"항목:\s*(.+)", block).group(1).split("\n")[0]
        meta["단위"] = re.search(r"단위:\s*(\S+)", block).group(1)

        monthly_data = re.findall(r"(\d{4}\.\d{2}) 월:\s*([\d.]+)", block)
        for date_str, value in monthly_data:
            record = meta.copy()
            record["날짜"] = date_str.replace(".", "-")
            record["값"] = float(value)
            records.append(record)

    df = pd.DataFrame(records)
    df["날짜"] = pd.to_datetime(df["날짜"], format="%Y-%m")
    df = df.sort_values("값", ascending=False).drop_duplicates(
        subset=["행정구역별", "매입자거주지", "항목", "날짜"], keep="first"
    )

    df = df.sort_values(
        ["행정구역별", "매입자거주지", "항목", "날짜"],
        ascending=[True, True, True, False],
    )

    link = upload_to_drive(
        data=df,
        filename=f"{address}_매매수급지수_temp.csv",
        mime_type="text/csv"
    )
    print("📎 매매수급지수_temp 링크:", link)
    return link

# ["supply_demand"]["planning_move"]
def planning_move_to_csv(data_list,address):
    
    if isinstance(data_list, str):
        data_list = json.loads(data_list)

    df = pd.DataFrame(data_list)
    df["입주예정월"] = df["입주예정월"].astype(str).apply(
        lambda x: f"{x[:4]}-{x[4:]}"
    )
    df = df.sort_values("입주예정월")
    link = upload_to_drive(
        data=df,
        filename=f"{address}_입주예정단지_temp.csv",
        mime_type="text/csv"
    )
    print("📎 _입주예정단지_temp 링크:", link)
    return link

def pre_promise_competition_to_csv(data_list,address):
    if isinstance(data_list, str):
        data_list = json.loads(data_list)

    df = pd.DataFrame(data_list)
    df["공고일"] = pd.to_datetime(df["공고일"], errors="coerce")
    def parse_rate(x):
        if isinstance(x, str):
            m = re.match(r"([\d.]+)", x)
            if m:
                return float(m.group(1))
        return None

    df["경쟁률"] = df["경쟁률"].apply(parse_rate)
    df = df.sort_values("공고일", ascending=False)

    link = upload_to_drive(
        data=df,
        filename=f"{address}_청약경쟁률_temp.csv",
        mime_type="text/csv"
    )
    print("📎 _청약경쟁률_temp 링크:", link)
    return link
# ['supply_demand']['one_people_gdp']
# ['supply_demand']['one_people_grdp']
def gdp_and_grdp_to_drive(one_gdp, one_grdp,address):
    grdp = {}
    for line in one_grdp.strip().splitlines():
        match = re.match(r"(\d{4})_1인당_GRDP:\s*([\d.]+)", line.strip())
        if match:
            year, value = match.groups()
            grdp[year] = float(value)
    
    df_gdp = pd.DataFrame(list(one_gdp.items()), columns=["연도", "1인당 GDP"])
    df_grdp = pd.DataFrame(list(grdp.items()), columns=["연도", "1인당 GRDP"])
    df_merged = pd.merge(df_gdp, df_grdp, on="연도", how="outer").sort_values("연도")
    link = upload_to_drive(
        data=df_merged,
        filename=f"{address}_GDP_와_GRDP_temp.csv",
        mime_type="text/csv"
    )
    print("📎 _GDP_와_GRDP_temp 링크:", link)
    return link 

# 매매수급지수, 10년이상 노후도는 텍스트로 표시하기 
# ["supply_demand"]["year10_after_house"]
# ["supply_demand"]["trade_balance"]

# ------</04. 공급과 수요 END>-------


# ------<05. 미분양 START>-------
# ['unsold_insight']['unsold_unit'] 
def unsold_to_drive(data_list,address):
    df = pd.DataFrame(data_list)
    df["기준월"] = df["연도"].astype(str) + "-" + df["월"].astype(str).str.zfill(2)
    df = df.sort_values(["연도", "월"], ascending=False).reset_index(drop=True)
    df = df.drop(columns=["id", "연도", "월"], errors="ignore")
    df = df[["기준월", "시도", "시군구", "미분양"]]
    link = upload_to_drive(
        data=df,
        filename=f"{address}_미분양_temp.csv",
        mime_type="text/csv"
    )
    print("📎 _미분양_temp 링크:", link)
    return link
# ------</05. 미분양 END>-------

# ------<06. 인구분석 START>-------

# ['population_insight']['age_population_context']
def age_population_to_drive(text, address):
    region_match = re.search(r"행정구역:\s*(\S+)", text)
    region = region_match.group(1) if region_match else "미상"

    pattern = re.compile(r"(\d{4})년(\d{2})월_(계|남|여)_(.+?):\s*([\d,]+)")
    rows = []
    for year, month, gender, category, value in pattern.findall(text):
        rows.append({
            "행정구역": region,
            "기준월": f"{year}-{month}",
            "성별": gender,
            "항목": category.strip(),
            "인구수": int(value.replace(",", ""))
        })

    df = pd.DataFrame(rows)

    pivot = df.pivot_table(
        index=["기준월", "성별"],
        columns="항목",
        values="인구수",
        aggfunc="first"
    ).reset_index()
    pivot = pivot.sort_values(["기준월", "성별"], ascending=[False, True]).reset_index(drop=True)
    pivot = pivot.fillna(0)
    for col in pivot.columns[2:]:
        pivot[col] = pivot[col].astype(int).map("{:,}".format)

    ordered_cols = (
        ["기준월", "성별", "총인구수"]
        + sorted([c for c in pivot.columns if "~" in c], key=lambda x: int(x.split("~")[0]))
    )
    ordered_cols = [c for c in ordered_cols if c in pivot.columns]
    pivot = pivot[ordered_cols]
    pivot = pivot[pivot["성별"] == "계"].drop(columns=["성별"]).reset_index(drop=True)
    link = upload_to_drive(
        data=df,
        filename=f"{address}_연령층분포_temp.csv",
        mime_type="text/csv"
    )
    print("📎 _연령층분포_temp 링크:", link)
    return link

# ['population_insight']['move_population_context']
def move_population_to_drive(data_list, address):
    df = pd.DataFrame(data_list)

    df = df[["year", "origin", "destination", "total"]]
    df = df.rename(columns={
        "year": "기준연도",
        "origin": "전출지",
        "destination": "전입지",
        "total": "이동인구수"
    })

    df = df.sort_values(["기준연도", "전입지", "이동인구수"], ascending=[False, True, False])

    df["이동인구수"] = df["이동인구수"].astype(int).map("{:,}".format)

    link = upload_to_drive(
        data=df,
        filename=f"{address}_인구이동_temp.csv",
        mime_type="text/csv"
    )
    print("📎 _인구이동_temp 링크:", link)
    return link

# ------</06. 인구분석 END>-------

# ------<07. 주변 매매비교 START>------
# ['nearby_market']['kakao_api_distance_context']
def nearby_complexes_to_csv(data_list, address):
    """주변 단지 요약 정보를 CSV로 저장"""
    rows = []
    for item in data_list:
        info = item.get("원본정보", {})
        rows.append({
            "주소": item.get("주소"),
            "타입": item.get("타입"),
            "세대수": info.get("세대수"),
            "면적": info.get("타입"),
            "평당가격": info.get("평당매매가격") or info.get("평당분양가격"),
            "준공연도": info.get("준공연도"),
            "사업지와의거리": info.get("사업지와의의거리"),
            "주변호재": info.get("주변호재"),
            "청약경쟁률": info.get("청약경쟁률"),
            "청약일시": info.get("청약일시"),
            "계약조건": info.get("계약조건")
        })

    df = pd.DataFrame(rows)

    # 가독성 향상: 주요 컬럼 순서
    col_order = [
        "주소", "타입", "세대수", "면적", "평당가격", "준공연도",
        "사업지와의거리", "주변호재", "청약경쟁률", "청약일시", "계약조건"
    ]
    df = df[[c for c in col_order if c in df.columns]]

    link = upload_to_drive(
        data=df,
        filename=f"{address}_주변단지_정보_temp.csv",
        mime_type="text/csv"
    )
    print("📎 _주변단지_정보_temp 링크:", link)
    return link
# ------</07. 주변 매매비교 END>------

def upload_test(df):
    link = upload_to_drive(data=df, filename="test.csv", mime_type="text/csv")
    return link
