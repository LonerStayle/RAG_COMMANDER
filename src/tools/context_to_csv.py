import re, json
import pandas as pd
from utils.llm import LLMProfile
from utils.google_drive_uploader import upload_to_drive

# -------<01. 주택 청약 START>---------
def housing_faq_context_to_drive(data_list):
    # 전체 Q/A 수집
    rows = []
    for block in data_list:
        pattern = r'Q\d*:\s*(.*?)\\nA\d*:\s*(.*?)(?=\\nQ\d*:|"$)'
        qa_pairs = re.findall(pattern, block)
        for q, a in qa_pairs:
            # 앞뒤 공백, 따옴표, 백슬래시 제거
            q_clean = q.strip().replace('\\"', '"').replace("\\\\n", "\n")
            a_clean = a.strip().replace('\\"', '"').replace("\\\\n", "\n")
            rows.append({"질문": q_clean, "답변": a_clean})

    # DataFrame 생성
    df = pd.DataFrame(rows)

    link = upload_to_drive(data=df, filename="주택청약FAQ_temp.csv", mime_type="text/csv")
    print("📎 Google Drive 링크:", link)
    return link

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
    return link
# -------</01. 주택 청약 END>---------

# ------<02. 입지분석 START>-------
def location_kakao_to_drive(data):
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
    link = upload_to_drive(data=final_df, filename="입지분석_카카오_temp.csv", mime_type="text/csv")
    return link
# ------</02. 입지분석 END>-------

# ------<03. 정책>-------
# ------</03. 정책>-------

# ------<04. 공급과 수요>-------
# ------</04. 공급과 수요>-------

# ------<05. 미분양>-------
# ------</05. 미분양>-------

# ------<06. 인구분석>-------
# ------</06. 인구분석>-------



def upload_test(df):
    link = upload_to_drive(data=df, filename="test.csv", mime_type="text/csv")
    return link
