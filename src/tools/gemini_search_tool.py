# Google Gemini API 공식 문서: https://ai.google.dev/gemini-api/docs
import google.genai as genai
from dotenv import load_dotenv
import os
import time

load_dotenv()

# Gemini API 클라이언트 생성
# 공식 문서: https://ai.google.dev/gemini-api/docs/python-sdk
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def gemini_search(prompt: str):
    """
    Gemini API를 사용하여 프롬프트에 대한 응답을 생성합니다.
    서버 오류 시 3번까지 재시도합니다.

    Args:
        prompt: Gemini에게 전달할 프롬프트 텍스트

    Returns:
        Gemini가 생성한 응답 텍스트
    """
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro", contents=prompt
            )
            return response.text
        except Exception as e:
            error_message = str(e)
            is_last_attempt = attempt == max_retries - 1

            if is_last_attempt:
                return f"Gemini API 오류: {error_message}. 잠시 후 다시 시도해주세요."

            time.sleep(retry_delay)
            continue

    return "Gemini API 호출 실패"


"""
from src.tools.gemini_search_tool import gemini_search

result = gemini_search("프롬프트 텍스트를 여기에 입력")
print(result)
"""

if __name__ == "__main__":

    
    prompt =  f"""
    <CONTEXT>
    사업지: 서울특별시 강남구 언주로 711
    세대수: 1000세대
    타입: 84m²
    일시: 2025-11-07
    </CONTEXT>

    <GOAL>
    - <CONTEXT>의 주소, 규모, 타입, 일시가 유사하고, 최단거리에 있는 매매아파트 3개, 분양아파트트 3개를 찾아서 매매아파트 3개는 각각의 평당매매가격, 분양단지 3개는 각각의 평당분양가격을 출력해 주세요
    </GOAL>
    <RULE>
    - 다른말은 생략하고 무조건 <OUTPUT>형식("json 형식")으로만 출력해주세요.
    - 매매아파트는 준공연도를 명시하세요.
    - 마크다운 코드블록은 제거하고 출력해 주세요.
    - 정확한 정보인지 확인하고 출력해 주세요.
    </RULE>
    <OUTPUT>
    {{
      "매매아파트": [
        {{
          "주소와단지명": "",
          "세대수": "",
          "타입": "",
          "평당매매가격": "",
          "준공연도": "",
          "사업지와의의거리": "",
          "주변호재": ""
        }}
      ],
      "분양아파트": [
        {{
          "주소와단지명": "",
          "세대수": "",
          "타입": "",
          "평당분양가격": "",
          "청약경쟁쟁률": "",
          "사업지와의거리": "",
          "주변호재": ""
        }}
      ]
    }}
    </OUTPUT>
    """
    result = gemini_search(prompt)
    print(result)
