# render_html.py
"""curricula/{arxiv_id}.json → docs/{arxiv_id}/day_*.html + figures/*.png"""
import html
import json
import os
import sys

import fitz  # pymupdf


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo",
               "Pretendard", "Noto Sans KR", sans-serif;
  background: #fafafa; color: #1a1a1a;
  line-height: 1.7; padding: 16px 16px 80px;
  max-width: 680px; margin: 0 auto;
}

/* HERO CARD */
.hero {
  background:
    radial-gradient(ellipse at top right, rgba(2, 49, 189, 0.18), transparent 55%),
    #161616;
  color: white;
  border-radius: 20px;
  padding: 36px 28px;
  margin: 8px 0 32px;
  position: relative;
  overflow: hidden;
}
.hero-meta {
  color: #023BE6;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.3px;
  margin-bottom: 24px;
}
.hero-tag {
  position: absolute;
  top: 28px;
  right: 28px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
}
.hero-title {
  font-size: 36px;
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 18px;
  color: white;
  word-break: keep-all;
}
.hero-subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 16px;
  line-height: 1.55;
}
@media (max-width: 480px) {
  .hero { padding: 28px 22px; }
  .hero-tag { top: 22px; right: 22px; font-size: 12px; padding: 5px 11px; }
  .hero-title { font-size: 30px; }
  .hero-subtitle { font-size: 15px; }
}

/* CONTENT */
.content { font-size: 17px; white-space: pre-wrap; margin-bottom: 32px; }
.figure-box {
  background: #f0f4ff; border-left: 4px solid #5b8def;
  padding: 14px 16px; border-radius: 8px;
  margin: 24px 0; font-size: 15px;
}
.figure-box .label {
  font-size: 12px; color: #5b8def; font-weight: 600;
  margin-bottom: 4px; letter-spacing: 0.5px;
}
.figure-box .desc { margin-bottom: 10px; }
.figure-box img {
  display: block; max-width: 100%; margin-top: 8px;
  border-radius: 6px; border: 1px solid #d0d8ec; cursor: zoom-in;
}
.trigger { color: #888; font-size: 13px; text-align: center; margin: 24px 0; }
.nav {
  display: flex; justify-content: space-between; gap: 12px;
  margin-top: 40px; padding-top: 24px; border-top: 1px solid #eee;
}
.nav a, .nav span {
  flex: 1; text-align: center; padding: 14px;
  border-radius: 8px; text-decoration: none;
  font-weight: 500; color: #333; background: #f0f0f0;
}
.nav .disabled { color: #bbb; background: #f7f7f7; pointer-events: none; }
.home-link {
  display: block; text-align: center; margin-top: 24px;
  color: #888; font-size: 14px; text-decoration: none;
}

/* INDEX */
.day-list { list-style: none; padding: 0; }
.day-list li { margin-bottom: 10px; }
.day-list a {
  display: block; padding: 16px 18px; background: white;
  border-radius: 10px; border: 1px solid #eee;
  text-decoration: none; color: #1a1a1a;
}
.day-num { color: #5b8def; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; }
.day-title { font-size: 16px; font-weight: 500; margin-top: 2px; }
.index-title { font-size: 22px; font-weight: 700; margin: 24px 0 8px; }
.index-meta { color: #888; font-size: 14px; margin-bottom: 24px; }
"""


def day_tag(day_num: int, total: int = 10) -> str:
    """Day 번호 → 카테고리 태그 (10일 커리큘럼 기준)."""
    if day_num <= 2:
        return "배경"
    elif day_num <= 4:
        return "개요"
    elif day_num <= 8:
        return "방법론"
    elif day_num == 9:
        return "결과"
    else:
        return "응용"


def page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


def render_pdf_page(pdf_path: str, page_num: int, output_path: str, dpi: int = 150):
    """PDF 특정 페이지를 PNG로 렌더링."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    pix = page.get_pixmap(dpi=dpi)
    pix.save(output_path)
    doc.close()


def render_day(num: int, data: dict, total: int) -> str:
    title = html.escape(data.get("title", ""))
    intent = html.escape(data.get("intent", ""))
    content = html.escape(data.get("content", "").strip())
    figure = data.get("suggested_figure")
    figure_page = data.get("figure_page")
    trigger = html.escape(data.get("trigger_type", "?"))
    tag = day_tag(num, total)
    
    # Hero card
    hero = f"""
<div class="hero">
  <div class="hero-meta">오늘의 학습 · DAY {num}</div>
  <div class="hero-tag">{tag}</div>
  <h1 class="hero-title">{title}</h1>
  <div class="hero-subtitle">{intent}</div>
</div>"""
    
    # Figure block
    figure_block = ""
    if figure and figure != "null":
        img_html = ""
        if figure_page and isinstance(figure_page, int):
            img_html = (
                f'<a href="figures/page_{figure_page}.png" target="_blank">'
                f'<img src="figures/page_{figure_page}.png" alt="Figure" loading="lazy">'
                '</a>'
            )
        figure_block = (
            '<div class="figure-box">'
            '<div class="label">참고 그림</div>'
            f'<div class="desc">{html.escape(figure)}</div>'
            f'{img_html}'
            '</div>'
        )
    
    prev_btn = ('<span class="disabled">← 이전</span>' if num == 1
                else f'<a href="day_{num - 1}.html">← Day {num - 1}</a>')
    next_btn = ('<span class="disabled">다음 →</span>' if num == total
                else f'<a href="day_{num + 1}.html">Day {num + 1} →</a>')
    
    body = f"""
{hero}
<div class="content">{content}</div>
{figure_block}
<div class="trigger">Trigger Type {trigger}</div>
<div class="nav">{prev_btn}{next_btn}</div>
<a class="home-link" href="index.html">전체 Day 목록 →</a>"""
    
    return page(f"Day {num} — {data.get('title', '')}", body)


def render_index(curriculum: dict, paper_id: str) -> str:
    keys = sorted([k for k in curriculum if k.startswith("day_")],
                  key=lambda x: int(x.split("_")[1]))
    items = []
    for k in keys:
        num = int(k.split("_")[1])
        title = html.escape(curriculum[k].get("title", ""))
        items.append(
            f'<li><a href="day_{num}.html">'
            f'<div class="day-num">DAY {num}</div>'
            f'<div class="day-title">{title}</div>'
            '</a></li>'
        )
    
    body = f"""
<div class="index-meta">arXiv {paper_id}</div>
<h1 class="index-title">10일 마이크로러닝</h1>
<ul class="day-list">
{chr(10).join(items)}
</ul>"""
    
    return page(f"{paper_id} — 10일 마이크로러닝", body)


def render_paper(arxiv_id: str):
    json_path = f"curricula/{arxiv_id}.json"
    pdf_path = f"papers/{arxiv_id}.pdf"
    
    with open(json_path, "r", encoding="utf-8") as f:
        curriculum = json.load(f)
    
    out_dir = f"docs/{arxiv_id}"
    os.makedirs(out_dir, exist_ok=True)
    
    day_keys = sorted([k for k in curriculum if k.startswith("day_")],
                      key=lambda x: int(x.split("_")[1]))
    total = len(day_keys)
    
    # figure 페이지 렌더링
    figure_pages = set()
    for k in day_keys:
        fp = curriculum[k].get("figure_page")
        if fp and isinstance(fp, int):
            figure_pages.add(fp)
    
    if figure_pages and os.path.exists(pdf_path):
        print(f"\nfigure 페이지 렌더링 중... ({len(figure_pages)}장)")
        for fp in sorted(figure_pages):
            output_path = f"{out_dir}/figures/page_{fp}.png"
            if not os.path.exists(output_path):
                render_pdf_page(pdf_path, fp, output_path)
                print(f"  생성: figures/page_{fp}.png")
            else:
                print(f"  스킵 (이미 있음): figures/page_{fp}.png")
    
    # HTML 생성
    for k in day_keys:
        num = int(k.split("_")[1])
        html_text = render_day(num, curriculum[k], total)
        with open(f"{out_dir}/day_{num}.html", "w", encoding="utf-8") as f:
            f.write(html_text)
    
    with open(f"{out_dir}/index.html", "w", encoding="utf-8") as f:
        f.write(render_index(curriculum, arxiv_id))
    
    abs_path = os.path.abspath(f"{out_dir}/index.html")
    print(f"\n렌더 완료: {out_dir}/")
    print(f"\n브라우저로 열기:")
    print(f"  file:///{abs_path.replace(chr(92), '/')}")


if __name__ == "__main__":
    arxiv_id = sys.argv[1] if len(sys.argv) > 1 else "2401.01339"
    render_paper(arxiv_id)