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
