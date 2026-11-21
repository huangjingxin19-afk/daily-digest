#!/usr/bin/env python3
"""Build the daily digest static site.

Reads content/YYYY-MM-DD-hot.md and content/YYYY-MM-DD-benefits.md,
writes site/index.html (latest day), site/archive.html, site/YYYY-MM-DD.html.
Self-contained: tiny markdown subset renderer, no third-party deps.
"""
import html
import os
import re
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(BASE, "content")
OUT = os.path.join(BASE, "docs")

CSS = """
:root{color-scheme:light dark}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.75;background:#f6f7f9;color:#1c1e21}
@media (prefers-color-scheme:dark){body{background:#14161a;color:#e8eaed}}
.wrap{max-width:720px;margin:0 auto;padding:16px}
header.site{padding:20px 0 8px}
header.site h1{font-size:24px;margin:0}
header.site .sub{opacity:.65;font-size:13px;margin-top:4px}
nav.top{display:flex;gap:16px;padding:10px 0;border-bottom:1px solid rgba(128,128,128,.3);margin-bottom:16px}
nav.top a{color:inherit;text-decoration:none;font-weight:600}
section.card{background:rgba(255,255,255,.7);border:1px solid rgba(128,128,128,.25);border-radius:12px;padding:16px 18px;margin:16px 0}
@media (prefers-color-scheme:dark){section.card{background:rgba(255,255,255,.05)}}
section.card h2{margin-top:0;font-size:20px}
article h1{font-size:20px}article h2{font-size:18px}article h3{font-size:16px;margin:18px 0 6px}
article p{margin:8px 0}
article ul,article ol{padding-left:22px;margin:8px 0}
article li{margin:5px 0}
a{color:#2563eb;word-break:break-all}
@media (prefers-color-scheme:dark){a{color:#7aa7ff}}
ul.archive{list-style:none;padding:0}
ul.archive li{padding:10px 0;border-bottom:1px solid rgba(128,128,128,.2)}
footer{opacity:.55;font-size:12px;padding:24px 0;text-align:center}
"""


def inline(text):
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def render_md(md):
    lines = md.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = min(len(m.group(1)) + 1, 4)
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue
        if stripped in ("---", "***", "___"):
            out.append("<hr>")
            i += 1
            continue
        if re.match(r"^[-*•]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*•]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*•]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        if re.match(r"^\d+[.、)]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+[.、)]\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+[.、)]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        m = re.match(r"^\*\*(.+)\*\*$", stripped)
        if m and len(stripped) < 60:
            out.append(f"<h3>{inline(m.group(1))}</h3>")
            i += 1
            continue
        out.append(f"<p>{inline(stripped)}</p>")
        i += 1
    return "\n".join(out)


def page(title, body, updated):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="site"><h1>每日汇总</h1><div class="sub">AI 热点 · 免费福利，每天早上更新</div></header>
<nav class="top"><a href="index.html">今日</a><a href="archive.html">归档</a></nav>
{body}
<footer>最后更新：{updated}</footer>
</div>
</body>
</html>
"""


def day_body(date, hot_html, benefits_html):
    parts = [f"<h2>{date}</h2>"]
    if hot_html:
        parts.append(f'<section class="card"><h2>AI 热点</h2><article>{hot_html}</article></section>')
    if benefits_html:
        parts.append(f'<section class="card"><h2>每日免费福利</h2><article>{benefits_html}</article></section>')
    if not hot_html and not benefits_html:
        parts.append("<p>这一天暂无内容。</p>")
    return "\n".join(parts)


def main():
    os.makedirs(OUT, exist_ok=True)
    dates = {}
    if os.path.isdir(CONTENT):
        for name in os.listdir(CONTENT):
            m = re.match(r"^(\d{4}-\d{2}-\d{2})-(hot|benefits)\.md$", name)
            if m:
                dates.setdefault(m.group(1), {})[m.group(2)] = os.path.join(CONTENT, name)
    updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    for old in os.listdir(OUT):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\.html$", old)
        if m and m.group(1) not in dates:
            os.remove(os.path.join(OUT, old))
    if not dates:
        body = "<p>暂无内容，第一份汇总生成后这里会自动出现。</p>"
        with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
            f.write(page("每日汇总", body, updated))
        with open(os.path.join(OUT, "archive.html"), "w", encoding="utf-8") as f:
            f.write(page("归档 · 每日汇总", "<h2>归档</h2><p>暂无。</p>", updated))
        print("no content yet; wrote placeholder index/archive")
        return 0
    for date in sorted(dates):
        entry = dates[date]
        hot = render_md(open(entry["hot"], encoding="utf-8").read()) if "hot" in entry else ""
        ben = render_md(open(entry["benefits"], encoding="utf-8").read()) if "benefits" in entry else ""
        with open(os.path.join(OUT, f"{date}.html"), "w", encoding="utf-8") as f:
            f.write(page(f"{date} · 每日汇总", day_body(date, hot, ben), updated))
    latest = max(dates)
    entry = dates[latest]
    hot = render_md(open(entry["hot"], encoding="utf-8").read()) if "hot" in entry else ""
    ben = render_md(open(entry["benefits"], encoding="utf-8").read()) if "benefits" in entry else ""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page("每日汇总", day_body(latest, hot, ben), updated))
    items = "".join(
        f'<li><a href="{d}.html">{d}</a></li>' for d in sorted(dates, reverse=True)
    )
    with open(os.path.join(OUT, "archive.html"), "w", encoding="utf-8") as f:
        f.write(page("归档 · 每日汇总", f"<h2>归档</h2><ul class=\"archive\">{items}</ul>", updated))
    print(f"built {len(dates)} day(s), latest {latest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
