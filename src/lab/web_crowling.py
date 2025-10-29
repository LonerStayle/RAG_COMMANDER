from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import json
import time


# Driver Setup
def create_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    return webdriver.Chrome(options=options)


# Navigation
def go_to_page(driver, url):
    driver.get(url)
    time.sleep(3)


# HTML Parsing
def get_page_html(driver):
    return driver.page_source


def parse_html(html):
    return BeautifulSoup(html, 'html.parser')


def find_all_links(soup):
    return soup.find_all('a', href=True)


# Link Filtering
def has_detail_in_url(link):
    return 'Detail.aspx' in link.get('href', '')


def has_enough_text(link):
    return len(link.get_text(strip=True)) > 10


def is_article_link(link):
    return has_detail_in_url(link) and has_enough_text(link)


def extract_article_urls(driver):
    html = get_page_html(driver)
    soup = parse_html(html)
    all_links = find_all_links(soup)

    # Debug: print all links
    print(f"   DEBUG: Total links found: {len(all_links)}")
    detail_links = [l for l in all_links if 'Detail' in l.get('href', '')]
    print(f"   DEBUG: Links with 'Detail': {len(detail_links)}")
    if detail_links:
        print(f"   DEBUG: First Detail link: {detail_links[0].get('href', '')[:80]}")

    article_links = filter(is_article_link, all_links)
    urls = [link.get('href') for link in article_links]
    return list(set(urls))


# Data Extraction
def extract_title(soup):
    tag = soup.find('h1') or soup.find('h2') or soup.find('title')
    return tag.get_text(strip=True) if tag else ""


def extract_date(soup):
    tag = soup.find('time') or soup.find(class_=lambda x: x and 'date' in str(x).lower())
    return tag.get_text(strip=True) if tag else ""


def extract_content(soup):
    tag = soup.find('article') or soup.find('div', class_='content') or soup.find('body')
    return tag.get_text(separator=' ', strip=True)[:1000] if tag else ""


def extract_article_data(driver):
    html = get_page_html(driver)
    soup = parse_html(html)

    return {
        "url": driver.current_url,
        "title": extract_title(soup),
        "date": extract_date(soup),
        "content": extract_content(soup),
        "source": "housing-post"
    }


# Crawling
def make_full_url(href):
    return href if href.startswith('http') else f"https://housing-post.com{href}"


def scrape_article(driver, url, index, total):
    try:
        full_url = make_full_url(url)
        print(f"   [{index}/{total}] {url[:50]}...")

        go_to_page(driver, full_url)
        article = extract_article_data(driver)

        if article['title']:
            print(f"      OK: {article['title'][:30]}")
            return article

        return None

    except Exception as e:
        print(f"      FAIL: {str(e)[:40]}")
        return None


def scrape_page(driver, page_url):
    print(f"\nPage: {page_url}")

    go_to_page(driver, page_url)
    article_urls = extract_article_urls(driver)

    print(f"   Found {len(article_urls)} articles")

    articles = []
    for index, url in enumerate(article_urls, 1):
        article = scrape_article(driver, url, index, len(article_urls))
        if article:
            articles.append(article)
        time.sleep(1)

    return articles


def create_page_url(base_url, page_number):
    return base_url if page_number == 1 else f"{base_url}&page={page_number}"


def crawl_pages(base_url, total_pages):
    driver = create_driver()
    all_articles = []

    try:
        for page_num in range(1, total_pages + 1):
            page_url = create_page_url(base_url, page_num)
            articles = scrape_page(driver, page_url)
            all_articles.extend(articles)
            time.sleep(2)

        return all_articles

    finally:
        driver.quit()


# Save
def create_output_dir(dir_path):
    Path(dir_path).mkdir(parents=True, exist_ok=True)


def generate_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"housing_post_{timestamp}.json"


def create_json_data(articles):
    return {
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(articles),
        "articles": articles
    }


def save_to_json(articles, output_dir="src/data/policy_factors"):
    create_output_dir(output_dir)

    filename = generate_filename()
    filepath = Path(output_dir) / filename

    json_data = create_json_data(articles)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved: {filepath}")
    print(f"   Total: {len(articles)} articles")

    return str(filepath)


# Main
def crawl_housing_post(base_url, pages):
    print("=" * 60)
    print(f"Start crawling: {pages} pages")
    print("=" * 60)

    articles = crawl_pages(base_url, pages)

    print("\n" + "=" * 60)
    print(f"Done! Total: {len(articles)} articles")
    print("=" * 60)

    return articles


def show_preview(article):
    print(f"\nTitle: {article['title']}")
    print(f"Date: {article['date']}")
    print(f"URL: {article['url']}")
    print(f"Content: {article['content'][:80]}...")


def main():
    BASE_URL = "https://housing-post.com/List.aspx?CNO=11389"
    PAGES = 3

    articles = crawl_housing_post(BASE_URL, PAGES)

    if articles:
        save_to_json(articles)

        print("\n" + "=" * 60)
        print("Preview (first 3)")
        print("=" * 60)

        for article in articles[:3]:
            show_preview(article)

        remaining = len(articles) - 3
        if remaining > 0:
            print(f"\n... and {remaining} more")

        return articles
    else:
        print("\nNo results")
        return []


if __name__ == "__main__":
    main()
