import requests, os, time, random
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_suffix('.env')) 

# === CẤU HÌNH ===
TOKEN = os.getenv("GITHUB_TOKEN")  # thay bằng token thật nếu cần
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

MIN_LENGTH = 10

def get_random_substring(s):
    if len(s) < MIN_LENGTH:
        return s
    start = random.randint(0, len(s) - MIN_LENGTH)
    end = random.randint(start + MIN_LENGTH, len(s))
    return s[start:end]

def search_github_code(query_string):
    query = quote_plus(query_string)
    url = f"https://api.github.com/search/code?q={query}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        repos = {item["repository"]["full_name"] for item in data.get("items", [])}
        return data.get("total_count", 0), sorted(repos)
    else:
        print(f"❌ Request failed ({response.status_code}): {response.text}")
        return 0, []

def basic_search(keywords: list[str]) -> list[str]:
    """
    Nhận vào danh sách chuỗi tìm kiếm, trả ra danh sách repo GitHub.
    """
    seen_repos = set()

    for keyword in keywords:
        sub = get_random_substring(keyword)
        print(f"🔍 Đang tìm kiếm: {sub}")
        count, repos = search_github_code(sub)
        time.sleep(10)  # tránh giới hạn API

        for repo in repos:
            seen_repos.add(repo)

    return sorted(seen_repos)
