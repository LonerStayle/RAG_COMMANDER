# -*- coding: utf-8 -*-

# 웹 페이지의 HTML을 가져오기 위해 사용하는 라이브러리입니다.
# 출처: https://pypi.org/project/requests/
import requests

# 가져온 HTML을 분석하여 원하는 정보를 쉽게 찾게 도와주는 라이브러리입니다.
# 출처: https://pypi.org/project/beautifulsoup4/
from bs4 import BeautifulSoup

# 파이썬의 리스트나 딕셔너리 데이터를 JSON 파일 형식으로 저장할 때 사용하는 기본 라이브러리입니다.
import json

# 폴더를 만들거나 파일 경로를 다룰 때 사용하는 파이썬 기본 라이브러리입니다.
import os

# 오늘 날짜를 가져와 파일 이름에 사용하기 위한 파이썬 기본 라이브러리입니다.
from datetime import datetime

# --- 설정 ---
# 데이터가 저장될 폴더 경로
SAVE_DIRECTORY = r"C:\RAG_COMMANDER\src\data\population_insight"
# 하우징포스트 웹사이트 주소
BASE_URL = "https://housing-post.com/"

# --- [수정된 부분 1] ---
# 웹사이트에 요청할 때, 우리가 일반 브라우저인 것처럼 보이게 할 정보입니다.
# 많은 웹사이트들이 이 정보가 없으면 로봇으로 판단하고 접근을 막습니다.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def get_article_links_from(page_number):
    """
    지정된 페이지 번호에서 모든 기사의 상세 페이지 링크를 수집하는 함수입니다.
    """
    list_url = f"https://housing-post.com/List.aspx?CNO=11389&PAGE={page_number}"
    print(f"{page_number}번 페이지에서 기사 링크를 수집합니다...")

    # --- [수정된 부분 2] ---
    # requests로 페이지를 요청할 때, 위에서 만든 headers 정보를 함께 보냅니다.
    response = requests.get(list_url, headers=HEADERS)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = []
    
    # --- [수정된 부분 3] ---
    # 기사 목록(ul 태그)을 먼저 찾고, 그 결과가 실제로 존재하는지 확인하는 단계를 추가합니다.
    # 이렇게 하면, 목록을 찾지 못해도 프로그램이 멈추지 않고 안전하게 넘어갑니다.
    article_list_ul = soup.find('ul', class_='article-list')
    
    if article_list_ul: # 만약 article_list_ul이 None이 아니라면(즉, 목록을 찾았다면)
        articles_in_page = article_list_ul.find_all('li')
        
        for article_item in articles_in_page:
            link_tag = article_item.find('a')
            if link_tag:
                full_link = BASE_URL + link_tag['href']
                links.append(full_link)
    else: # 목록을 찾지 못했다면
        print(f"  [경고] {page_number}번 페이지에서 기사 목록('article-list')을 찾을 수 없습니다.")

    return links


def get_article_details_from(article_url):
    """
    기사 링크를 받아, 해당 기사의 제목, 날짜, 본문을 추출하는 함수입니다.
    """
    print(f" - 기사 내용 수집 중: {article_url}")
    
    # 여기에도 headers 정보를 추가해 줍니다.
    response = requests.get(article_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    try:
        title = soup.find('div', class_='article-header').find('h3').get_text(strip=True)
        date = soup.find('span', class_='date').get_text(strip=True)
        content = soup.find('div', id='article-view-content').get_text(strip=True)
        
        return {
            'title': title,
            'date': date,
            'content': content
        }
    except Exception:
        print(f"   [!] 정보를 추출하지 못했습니다. 이 기사는 건너뜁니다.")
        return None


def save_articles_to_json(article_list):
    """
    수집된 모든 기사 리스트를 JSON 파일로 저장하는 함수입니다.
    """
    os.makedirs(SAVE_DIRECTORY, exist_ok=True)
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    file_name = f"housing-post_articles_{today_str}.json"
    
    full_path = os.path.join(SAVE_DIRECTORY, file_name)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(article_list, f, ensure_ascii=False, indent=4)
        
    print("-" * 50)
    print("크롤링이 성공적으로 완료되었습니다!")
    print(f"총 {len(article_list)}개의 기사를 수집했습니다.")
    print(f"저장된 파일: {full_path}")
    print("-" * 50)


# --- 메인 실행 ---
if __name__ == "__main__":
    
    all_articles_data = []

    page1_links = get_article_links_from(1)
    page2_links = get_article_links_from(2)
    page3_links = get_article_links_from(3)
    page4_links = get_article_links_from(4)
    page5_links = get_article_links_from(5)
    
    total_links = page1_links + page2_links + page3_links + page4_links + page5_links
    
    for link in total_links:
        article_content = get_article_details_from(link)
        if article_content:
            all_articles_data.append(article_content)

    if all_articles_data:
        save_articles_to_json(all_articles_data)
    else:
        print("수집된 기사가 없어 파일을 저장하지 않았습니다.")