"""개발·AI 뉴스 헤드라인 수집 (긱뉴스 + Hacker News)

사용: python -I fetch.py   → 콘솔에 헤드라인 출력 (요약·발송은 Claude 가 함)
"""
import html
import json
import re
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
        return r.read().decode("utf-8", "replace")


def geeknews(n=6):
    x = get("https://feeds.feedburner.com/geeknews-feed")
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", x, re.S)[:n]:
        t = re.search(r"<title[^>]*>(.*?)</title>", e, re.S)
        l = re.search(r"<link[^>]*href=['\"]([^'\"]+)", e)
        out.append((html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", t.group(1))).strip(), html.unescape(l.group(1)).split("&utm_")[0] if l else ""))
    return out


def hackernews(n=6):
    ids = json.loads(get("https://hacker-news.firebaseio.com/v0/topstories.json"))[:30]
    items = []
    for i in ids:
        try:
            it = json.loads(get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json"))
        except Exception:
            continue
        if it and it.get("type") == "story":
            items.append((it.get("score", 0), it.get("title", ""), f"https://news.ycombinator.com/item?id={i}"))
    return sorted(items, reverse=True)[:n]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("[긱뉴스]")
    for t, l in geeknews():
        print("-", t, l)
    print("[Hacker News] (점수순)")
    for s, t, l in hackernews():
        print(f"- ({s}) {t} {l}")
