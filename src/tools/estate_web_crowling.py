"""간단한 주택 정책 기사 크롤링 도구.

- 대상 사이트: https://housing-post.com (직접 HTML 구조를 확인해서 작성)
- 사용 목적: 외부 모듈에서 함수를 불러 기사 데이터를 바로 활용
"""

"""
from tools.estate_web_crowling import export_policy_factors

saved_path = export_policy_factors(max_page=3)
print(saved_path)

"""


import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://housing-post.com"
LIST_PATH = "/List.aspx?CNO=11389"
MAX_PAGE = 3
DATA_ROOT = Path("C:/RAG_COMMANDER/src/data/policy_factors")


def _collect_form_inputs(soup):
    inputs = {}
    for tag in soup.select("form input"):
        name = tag.get("name")
        if not name:
            continue
        input_type = (tag.get("type") or "").lower()
        if input_type in {"submit", "image", "button"}:
            continue
        inputs[name] = tag.get("value", "")
    return inputs


def _extract_event_target(href_value):
    marker = "__doPostBack('"
    if not href_value or marker not in href_value:
        return ""
    start = href_value.index(marker) + len(marker)
    end = href_value.find("'", start)
    return href_value[start:end] if end != -1 else ""


def _collect_links(soup):
    links = []
    for anchor in soup.select("a.alink"):
        href = anchor.get("href")
        if href and "View.aspx" in href:
            full_url = urljoin(BASE_URL, href)
            if full_url not in links:
                links.append(full_url)
    return links


def _fetch_article(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    encoding = response.encoding or response.apparent_encoding or "utf-8"
    response.encoding = encoding
    return response.text


def _parse_article(article_url):
    soup = BeautifulSoup(_fetch_article(article_url), "html.parser")

    title_box = soup.select_one(".article-title")
    title = title_box.get_text(strip=True) if title_box else ""

    meta_box = soup.select_one(".article-meta")
    date_text = ""
    if meta_box:
        spans = meta_box.find_all("span")
        if len(spans) > 1:
            raw_date = spans[1].get_text(" ", strip=True)
            date_text = raw_date.replace("승인", "", 1).strip()

    body_box = soup.select_one(".article-body")
    content = body_box.get_text("\n", strip=True) if body_box else ""

    return {
        "url": article_url,
        "title": title,
        "date": date_text,
        "content": content,
    }


def collect_articles(max_page: int = MAX_PAGE):
    session = requests.Session()
    listing_url = urljoin(BASE_URL, LIST_PATH)

    response = session.get(listing_url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    form_inputs = _collect_form_inputs(soup)

    links = _collect_links(soup)
    current_page = 1

    while current_page < max_page:
        target_page = current_page + 1
        target = ""

        for anchor in soup.select("a.paging"):
            if anchor.get_text(strip=True) == str(target_page):
                target = _extract_event_target(anchor.get("href"))
                break

        if not target:
            break

        payload = form_inputs.copy()
        payload["__EVENTTARGET"] = target
        payload["__EVENTARGUMENT"] = ""

        response = session.post(listing_url, data=payload, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        form_inputs = _collect_form_inputs(soup)

        for link in _collect_links(soup):
            if link not in links:
                links.append(link)

        current_page = target_page

    articles = []
    for link in links:
        articles.append(_parse_article(link))

    return articles


def build_output_path(base_dir=DATA_ROOT):
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    return base_dir / f"policy_factors_{today}.json"


def save_articles(records, file_path):
    with Path(file_path).open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def export_policy_factors(max_page: int = MAX_PAGE, base_dir=DATA_ROOT):
    articles = collect_articles(max_page=max_page)
    output_path = build_output_path(base_dir=base_dir)
    save_articles(articles, output_path)
    return output_path
