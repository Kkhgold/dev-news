"""개발·AI 뉴스 페이지 생성기

사용: python -I build.py data/2026-11-07.json
data json 형식:
  {"date": "2026-11-07", "weekday": "토요일", "picks": ["오늘의 한 줄 1", ...],
   "items": [{"src": "GN"|"HN", "title": "원제", "ko": "한글 제목", "tag": "AI|개발|하드웨어|...",
              "url": "...", "score": 1030}]}
결과: index.html, reports/DATE.html, kakao.txt
"""
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://kkhgold.github.io/dev-news/"

CSS = r"""
:root{color-scheme:light;--bg:#f4f5f8;--surface:#fff;--text:#121722;--text-2:#4d5666;--muted:#7b8494;--line:#e3e7ee;--chip:#eef1f6;
--accent:#6250d6;--gn:#1baf7a;--hn:#eb6834;--hero-a:#1d1442;--hero-b:#4b3aa8;--shadow:0 1px 2px rgba(16,24,40,.04),0 4px 16px rgba(16,24,40,.06)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#0e1016;--surface:#171a22;--text:#eceff5;--text-2:#b5bccb;--muted:#8a93a3;
--line:#2a303c;--chip:#232834;--accent:#9085e9;--gn:#199e70;--hn:#d95926;--hero-a:#130d2e;--hero-b:#33267a;--shadow:none}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#0e1016;--surface:#171a22;--text:#eceff5;--text-2:#b5bccb;--muted:#8a93a3;--line:#2a303c;--chip:#232834;
--accent:#9085e9;--gn:#199e70;--hn:#d95926;--hero-a:#130d2e;--hero-b:#33267a;--shadow:none}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Pretendard","Malgun Gothic","Noto Sans KR",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}
.hero{background:linear-gradient(135deg,var(--hero-a),var(--hero-b));color:#fff;padding:24px 16px 22px}.hero .in{max-width:820px;margin:0 auto}
.kicker{opacity:.75;font-size:.82rem;letter-spacing:.05em}.hero h1{margin:4px 0 6px;font-size:1.6rem}.hero p{margin:0;opacity:.85;font-size:.92rem}
.tabbar{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.tb-in{max-width:820px;margin:0 auto;padding:8px 12px;display:flex;gap:6px;overflow-x:auto;scrollbar-width:none}.tb-in::-webkit-scrollbar{display:none}
.tabbar button{flex:0 0 auto;border:1px solid var(--line);background:var(--surface);color:var(--text-2);font:inherit;font-size:.9rem;font-weight:700;padding:7px 14px;border-radius:999px;cursor:pointer}
.tabbar button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
.wrap{max-width:820px;margin:0 auto;padding:14px 16px 56px}
.picks{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:14px 16px;box-shadow:var(--shadow);margin-bottom:14px}
.picks h2{margin:0 0 6px;font-size:1rem}.picks ul{margin:0;padding-left:18px}.picks li{margin:5px 0}
.list{display:grid;gap:10px}
.item{display:flex;gap:12px;align-items:flex-start;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px 14px;box-shadow:var(--shadow);
 text-decoration:none;color:inherit;transition:transform .16s,border-color .16s;opacity:0;animation:up .45s cubic-bezier(.2,.8,.2,1) forwards}
.item:hover{transform:translateY(-2px);border-color:var(--accent)}
.rk{flex:0 0 28px;height:28px;border-radius:8px;display:grid;place-items:center;font-weight:800;font-size:.85rem;color:#fff}
.rk.GN{background:var(--gn)}.rk.HN{background:var(--hn)}
.ko{font-weight:700;font-size:.98rem}.orig{color:var(--muted);font-size:.8rem;margin-top:2px}
.meta{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}.chip{background:var(--chip);color:var(--text-2);border-radius:999px;padding:1px 9px;font-size:.75rem;font-weight:600}
.legend{display:flex;gap:14px;color:var(--muted);font-size:.8rem;margin:4px 0 10px}.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.arch a{display:inline-block;background:var(--chip);color:var(--text);text-decoration:none;border-radius:999px;padding:4px 12px;margin:3px 4px 3px 0;font-size:.85rem}
h3{font-size:1rem;margin:26px 0 8px}footer{color:var(--muted);font-size:.78rem;margin-top:28px;text-align:center}
@keyframes up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.item{animation:none;opacity:1}}
"""

JS = r"""
(function(){const bs=[...document.querySelectorAll('.tabbar button')];
bs.forEach(b=>b.onclick=()=>{const f=b.dataset.f;bs.forEach(x=>x.setAttribute('aria-pressed',x===b?'true':'false'));
 let n=0;document.querySelectorAll('.item').forEach(it=>{const show=f==='all'||it.dataset.src===f||it.dataset.tag===f;it.hidden=!show;
  if(show){it.style.animation='none';it.offsetHeight;it.style.animation='';it.style.animationDelay=(n++*40)+'ms';}});});
document.querySelectorAll('.item').forEach((it,i)=>it.style.animationDelay=(i*40)+'ms');})();
"""


def esc(x):
    return html.escape(str(x))


def render(d, archive):
    items = d.get("items", [])
    tags = []
    for it in items:
        if it.get("tag") and it["tag"] not in tags:
            tags.append(it["tag"])
    btns = ["<button data-f='all' aria-pressed='true'>전체</button>",
            "<button data-f='GN' aria-pressed='false'>🇰🇷 긱뉴스</button>",
            "<button data-f='HN' aria-pressed='false'>🟧 Hacker News</button>"]
    btns += [f"<button data-f='{esc(t)}' aria-pressed='false'>#{esc(t)}</button>" for t in tags]
    rows = ""
    for i, it in enumerate(items, 1):
        src = it.get("src", "GN")
        meta = f"<span class='chip'>{'긱뉴스' if src == 'GN' else 'Hacker News'}</span>"
        if it.get("tag"):
            meta += f"<span class='chip'>#{esc(it['tag'])}</span>"
        if it.get("score"):
            meta += f"<span class='chip'>▲ {esc(it['score'])}점</span>"
        orig = f"<div class='orig'>{esc(it['title'])}</div>" if it.get("title") and it.get("title") != it.get("ko") else ""
        rows += (f"<a class='item' href='{esc(it['url'])}' target='_blank' rel='noopener' data-src='{src}' data-tag='{esc(it.get('tag', ''))}'>"
                 f"<span class='rk {src}'>{i}</span><div><div class='ko'>{esc(it.get('ko') or it['title'])}</div>{orig}<div class='meta'>{meta}</div></div></a>")
    picks = ""
    if d.get("picks"):
        picks = "<div class='picks'><h2>⚡ 오늘의 포인트</h2><ul>" + "".join(f"<li>{esc(x)}</li>" for x in d["picks"]) + "</ul></div>"
    arch = ""
    if archive:
        arch = "<h3>🗂 지난 소식</h3><div class='arch'>" + "".join(f"<a href='{SITE}reports/{a}.html'>{a}</a>" for a in archive) + "</div>"
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>개발 뉴스</title><meta name='description' content='개발·AI 뉴스 {esc(d['date'])}'>"
            f"<meta property='og:title' content='🧑‍💻 개발·AI 뉴스 {esc(d['date'])}'><style>{CSS}</style></head><body>"
            f"<header class='hero'><div class='in'><div class='kicker'>DEV &amp; AI DAILY</div><h1>🧑‍💻 {esc(d['date'])} ({esc(d.get('weekday', ''))})</h1>"
            "<p>긱뉴스 최신글 + Hacker News 인기글</p></div></header>"
            f"<nav class='tabbar' aria-label='필터'><div class='tb-in'>{''.join(btns)}</div></nav>"
            f"<main class='wrap'>{picks}<div class='legend'><span><i style='background:var(--gn)'></i>긱뉴스</span><span><i style='background:var(--hn)'></i>Hacker News</span></div>"
            f"<div class='list'>{rows}</div>{arch}<footer>출처: GeekNews(news.hada.io) · Hacker News · 제목은 Claude가 번역했어요</footer></main>"
            f"<script>{JS}</script></body></html>")


def kakao_text(d):
    head = f"🧑‍💻 {d['date'][5:].replace('-', '/')} 개발·AI 뉴스\n"
    tail = f"🔗 {SITE}"
    lines = ""
    for it in d.get("items", [])[:6]:
        line = f"• {it.get('ko') or it['title']}\n"
        if len(head + lines + line + tail) > 195:
            break
        lines += line
    return head + lines + tail


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        d = json.load(f)
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    archive = sorted({n[:-5] for n in os.listdir(os.path.join(ROOT, "reports")) if n.endswith(".html")} | {d["date"]}, reverse=True)
    page = render(d, archive)
    for path in (os.path.join(ROOT, "reports", d["date"] + ".html"), os.path.join(ROOT, "index.html")):
        with open(path, "w", encoding="utf-8") as f:
            f.write(page)
    text = kakao_text(d)
    with open(os.path.join(ROOT, "kakao.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text, f"\n({len(text)}자)")


if __name__ == "__main__":
    main()
