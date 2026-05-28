# render_html.py
"""curricula/{arxiv_id}.json → docs/{arxiv_id}/day_*.html + figures/*.png"""
import html
import json
import os
import re
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
  margin: 8px 0 24px;
  position: relative;
  overflow: hidden;
}
.hero-meta { color: #4d7cff; font-size: 14px; font-weight: 700; letter-spacing: 0.3px; margin-bottom: 24px; }
.hero-tag {
  position: absolute; top: 28px; right: 28px;
  background: rgba(255,255,255,0.1); color: white;
  padding: 6px 14px; border-radius: 999px;
  font-size: 13px; font-weight: 500;
}
.hero-title { font-size: 36px; font-weight: 800; line-height: 1.15; margin-bottom: 18px; color: white; word-break: keep-all; }
.hero-subtitle { color: rgba(255,255,255,0.7); font-size: 16px; line-height: 1.55; }
.progress-bar { height: 4px; background: rgba(255,255,255,0.15); border-radius: 2px; overflow: hidden; margin-top: 24px; }
.progress-fill { height: 100%; background: #4d7cff; border-radius: 2px; transition: width 0.3s; }
@media (max-width: 480px) {
  .hero { padding: 28px 22px; }
  .hero-tag { top: 22px; right: 22px; font-size: 12px; padding: 5px 11px; }
  .hero-title { font-size: 30px; }
  .hero-subtitle { font-size: 15px; }
}

/* TABS */
.tabs {
  display: flex; overflow-x: auto;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 24px; gap: 4px;
  -webkit-overflow-scrolling: touch;
}
.tab {
  padding: 12px 16px; background: none; border: none;
  font-size: 15px; color: #888; cursor: pointer;
  border-bottom: 2px solid transparent;
  white-space: nowrap; font-family: inherit;
}
.tab.active { color: #0231BD; border-bottom-color: #0231BD; font-weight: 600; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }

/* CONTENT (학습 탭) */
.content { font-size: 17px; white-space: pre-wrap; margin-bottom: 24px; }
.content strong { color: #0231BD; font-weight: 700; }
.figure-box {
  background: #f0f4ff; border-left: 4px solid #5b8def;
  padding: 14px 16px; border-radius: 8px;
  margin: 24px 0; font-size: 15px;
}
.figure-box .label { font-size: 12px; color: #5b8def; font-weight: 600; margin-bottom: 4px; letter-spacing: 0.5px; }
.figure-box .desc { margin-bottom: 10px; }
.figure-box img { display: block; max-width: 100%; margin-top: 8px; border-radius: 6px; border: 1px solid #d0d8ec; cursor: zoom-in; }
.figure-explain {
  margin-top: 12px; padding-top: 12px;
  border-top: 1px dashed #d0d8ec;
  font-size: 13px; color: #555; line-height: 1.55;
}
.trigger { color: #aaa; font-size: 12px; text-align: center; margin: 24px 0; }

/* CONCEPTS */
.concept-card {
  background: white; border: 1px solid #eee;
  border-radius: 10px; padding: 16px; margin-bottom: 12px;
}
.concept-term { font-size: 16px; font-weight: 700; color: #0231BD; margin-bottom: 6px; }
.concept-def { font-size: 15px; color: #333; }

/* EXPRESSIONS */
.expr-card {
  background: white; border: 1px solid #eee;
  border-radius: 10px; padding: 16px; margin-bottom: 12px;
}
.expr-en { font-size: 17px; font-weight: 700; color: #1a1a1a; margin-bottom: 2px; }
.expr-ko { font-size: 13px; color: #888; margin-bottom: 12px; }
.expr-example {
  background: #f7f9ff; border-left: 3px solid #4d7cff;
  padding: 10px 12px; border-radius: 4px; font-size: 14px;
  font-style: italic; color: #333; margin-bottom: 8px;
}
.expr-context { font-size: 13px; color: #666; }

/* MCQ */
.mcq-card {
  background: white; border: 1px solid #eee;
  border-radius: 10px; padding: 18px; margin-bottom: 16px;
}
.mcq-q-num { font-size: 12px; color: #4d7cff; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 8px; }
.mcq-question { font-size: 16px; font-weight: 600; margin-bottom: 16px; line-height: 1.5; }
.mcq-options { display: flex; flex-direction: column; gap: 8px; }
.mcq-option {
  text-align: left; padding: 12px 14px;
  background: #f7f7f7; border: 1px solid #eee;
  border-radius: 8px; font-size: 14px; cursor: pointer;
  font-family: inherit; color: #333;
  transition: background 0.15s;
}
.mcq-option:hover { background: #eef0f3; }
.mcq-option.correct { background: #e7f6ec; border-color: #34a853; color: #1e7e34; }
.mcq-option.wrong { background: #fbe9e9; border-color: #ea4335; color: #b22222; }
.mcq-explanation { display: none; margin-top: 12px; padding: 12px; background: #f0f4ff; border-radius: 6px; font-size: 14px; color: #333; }
.mcq-explanation.show { display: block; }

/* OPEN QUESTION */
.oq-card {
  background: white; border: 1px solid #eee;
  border-radius: 10px; padding: 18px;
}
.oq-question { font-size: 16px; font-weight: 600; margin-bottom: 14px; line-height: 1.5; }
.oq-answer {
  width: 100%; min-height: 100px; padding: 12px;
  border: 1px solid #ddd; border-radius: 8px;
  font-family: inherit; font-size: 15px; line-height: 1.5;
  resize: vertical; margin-bottom: 12px;
}
.oq-btn-row { display: flex; gap: 8px; flex-wrap: wrap; }
.oq-btn {
  padding: 10px 14px; background: #f0f0f0; border: none;
  border-radius: 6px; font-size: 14px; cursor: pointer;
  font-family: inherit; color: #333;
}
.oq-btn.primary { background: #0231BD; color: white; }
.oq-hint, .oq-takeaway { display: none; margin-top: 14px; padding: 12px 14px; border-radius: 8px; font-size: 14px; }
.oq-hint.show, .oq-takeaway.show { display: block; }
.oq-hint { background: #fffce0; border-left: 3px solid #f9c74f; }
.oq-takeaway { background: #f0f4ff; border-left: 3px solid #0231BD; }
.oq-label { font-size: 12px; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 6px; }
.oq-hint .oq-label { color: #b58c00; }
.oq-takeaway .oq-label { color: #0231BD; }

/* NAV */
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
.home-link { display: block; text-align: center; margin-top: 24px; color: #888; font-size: 14px; text-decoration: none; }

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
.day-list .today a { border-color: #0231BD; background: #f0f4ff; }
.today-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  background: #0231BD;
  color: white;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  vertical-align: middle;
  letter-spacing: 0.3px;
}
"""


JS = """
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const target = tab.dataset.target;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(target).classList.add('active');
  });
});

document.querySelectorAll('.mcq-option').forEach(opt => {
  opt.addEventListener('click', () => {
    const card = opt.closest('.mcq-card');
    card.querySelectorAll('.mcq-option').forEach(o => {
      o.classList.remove('correct', 'wrong');
    });
    if (opt.dataset.correct === 'true') {
      opt.classList.add('correct');
    } else {
      opt.classList.add('wrong');
      card.querySelector('.mcq-option[data-correct="true"]').classList.add('correct');
    }
    card.querySelector('.mcq-explanation').classList.add('show');
  });
});

document.querySelectorAll('.oq-hint-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.closest('.oq-card').querySelector('.oq-hint').classList.add('show');
  });
});

document.querySelectorAll('.oq-submit-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.closest('.oq-card').querySelector('.oq-takeaway').classList.add('show');
  });
});
"""


def day_tag(day_num: int, total: int = 10) -> str:
    if day_num <= 2: return "배경"
    elif day_num <= 4: return "개요"
    elif day_num <= 8: return "방법론"
    elif day_num == 9: return "결과"
    else: return "응용"


def page(title: str, body: str, with_js: bool = False) -> str:
    script = f"<script>{JS}</script>" if with_js else ""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {{
    delimiters: [
      {{left: '$$', right: '$$', display: true}},
      {{left: '$', right: '$', display: false}}
    ],
    throwOnError: false
  }});"></script>
<style>{CSS}</style>
</head>
<body>
{body}
{script}
</body>
</html>"""


def render_pdf_page(pdf_path: str, page_num: int, output_path: str, dpi: int = 150):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    pix = page.get_pixmap(dpi=dpi)
    pix.save(output_path)
    doc.close()


def format_content(content: str) -> str:
    """HTML escape + Markdown bold → <strong>."""
    text = html.escape(content)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return text


def render_content_tab(data: dict, total: int) -> str:
    content = format_content(data.get("content", "").strip())
    figure = data.get("suggested_figure")
    figure_page = data.get("figure_page")
    figure_desc = data.get("figure_description")  # ← 추가
    trigger = html.escape(data.get("trigger_type", "?"))
    
    figure_block = ""
    if figure and figure != "null":
        img_html = ""
        if figure_page and isinstance(figure_page, int):
            img_html = (
                f'<a href="figures/page_{figure_page}.png" target="_blank">'
                f'<img src="figures/page_{figure_page}.png" alt="Figure" loading="lazy">'
                '</a>'
            )
        desc_html = ""  # ← 추가
        if figure_desc and figure_desc != "null":
            desc_html = f'<div class="figure-explain">{html.escape(figure_desc)}</div>'
        figure_block = (
            '<div class="figure-box">'
            '<div class="label">참고 그림</div>'
            f'<div class="desc">{html.escape(figure)}</div>'
            f'{img_html}'
            f'{desc_html}'  # ← 추가
            '</div>'
        )
    
    return f"""
<div class="content">{content}</div>
{figure_block}
<div class="trigger">Trigger Type {trigger}</div>"""


def render_concepts_tab(data: dict) -> str:
    concepts = data.get("key_concepts", []) or []
    if not concepts:
        return '<p style="color:#888;">핵심 개념이 등록돼 있지 않아요.</p>'
    cards = []
    for c in concepts:
        term = html.escape(c.get("term", ""))
        definition = html.escape(c.get("definition", ""))
        cards.append(
            f'<div class="concept-card">'
            f'<div class="concept-term">{term}</div>'
            f'<div class="concept-def">{definition}</div>'
            '</div>'
        )
    return "\n".join(cards)


def render_expressions_tab(data: dict) -> str:
    exprs = data.get("english_expressions", []) or []
    if not exprs:
        return '<p style="color:#888;">영어 표현이 등록돼 있지 않아요.</p>'
    cards = []
    for e in exprs:
        en = html.escape(e.get("expression", ""))
        ko = html.escape(e.get("korean", ""))
        ex = html.escape(e.get("example", ""))
        ctx = html.escape(e.get("context", ""))
        cards.append(
            f'<div class="expr-card">'
            f'<div class="expr-en">{en}</div>'
            f'<div class="expr-ko">{ko}</div>'
            f'<div class="expr-example">{ex}</div>'
            f'<div class="expr-context">{ctx}</div>'
            '</div>'
        )
    return "\n".join(cards)


def render_quiz_tab(data: dict) -> str:
    mcq = data.get("mcq", []) or []
    oq = data.get("open_question", {}) or {}
    
    out = []
    
    # MCQ
    for i, q in enumerate(mcq, start=1):
        question = html.escape(q.get("question", ""))
        options = q.get("options", [])
        correct = q.get("correct", 0)
        explanation = html.escape(q.get("explanation", ""))
        
        opts_html = []
        for idx, opt in enumerate(options):
            is_correct = "true" if idx == correct else "false"
            opts_html.append(
                f'<button class="mcq-option" data-correct="{is_correct}">'
                f'{html.escape(opt)}'
                '</button>'
            )
        
        out.append(
            f'<div class="mcq-card">'
            f'<div class="mcq-q-num">객관식 Q{i}</div>'
            f'<div class="mcq-question">{question}</div>'
            f'<div class="mcq-options">{"".join(opts_html)}</div>'
            f'<div class="mcq-explanation">{explanation}</div>'
            '</div>'
        )
    
    # Open Question
    if oq:
        question = html.escape(oq.get("question", ""))
        hint = html.escape(oq.get("hint", ""))
        takeaway = html.escape(oq.get("key_takeaway", ""))
        
        out.append(f"""
<div class="oq-card">
  <div class="mcq-q-num">주관식</div>
  <div class="oq-question">{question}</div>
  <textarea class="oq-answer" placeholder="답을 적어보세요..."></textarea>
  <div class="oq-btn-row">
    <button class="oq-btn oq-hint-btn">힌트 보기</button>
    <button class="oq-btn primary oq-submit-btn">답안 제출 → 피드백 보기</button>
  </div>
  <div class="oq-hint">
    <div class="oq-label">힌트</div>
    <div>{hint}</div>
  </div>
  <div class="oq-takeaway">
    <div class="oq-label">꼭 짚고 가야 할 것</div>
    <div>{takeaway}</div>
  </div>
</div>""")
    
    return "\n".join(out) if out else '<p style="color:#888;">퀴즈가 등록돼 있지 않아요.</p>'


def render_day(num: int, data: dict, total: int) -> str:
    title = html.escape(data.get("title", ""))
    intent = html.escape(data.get("intent", ""))
    tag = day_tag(num, total)
    progress_pct = int((num / total) * 100)
    
    hero = f"""
<div class="hero">
  <div class="hero-meta">오늘의 학습 · DAY {num}</div>
  <div class="hero-tag">{tag}</div>
  <h1 class="hero-title">{title}</h1>
  <div class="hero-subtitle">{intent}</div>
  <div class="progress-bar">
    <div class="progress-fill" style="width: {progress_pct}%"></div>
  </div>
</div>"""
    
    tabs_nav = """
<div class="tabs">
  <button class="tab active" data-target="tab-content">학습</button>
  <button class="tab" data-target="tab-concepts">핵심 개념</button>
  <button class="tab" data-target="tab-expressions">영어 표현</button>
  <button class="tab" data-target="tab-quiz">퀴즈</button>
</div>"""
    
    tabs_content = f"""
<div class="tab-panel active" id="tab-content">{render_content_tab(data, total)}</div>
<div class="tab-panel" id="tab-concepts">{render_concepts_tab(data)}</div>
<div class="tab-panel" id="tab-expressions">{render_expressions_tab(data)}</div>
<div class="tab-panel" id="tab-quiz">{render_quiz_tab(data)}</div>"""
    
    prev_btn = ('<span class="disabled">← 이전</span>' if num == 1
                else f'<a href="day_{num - 1}.html">← Day {num - 1}</a>')
    next_btn = ('<span class="disabled">다음 →</span>' if num == total
                else f'<a href="day_{num + 1}.html">Day {num + 1} →</a>')
    
    body = f"""
{hero}
{tabs_nav}
{tabs_content}
<div class="nav">{prev_btn}{next_btn}</div>
<a class="home-link" href="index.html">전체 Day 목록 →</a>"""
    
    return page(f"Day {num} — {data.get('title', '')}", body, with_js=True)


def render_index(curriculum: dict, paper_id: str) -> str:
    keys = sorted([k for k in curriculum if k.startswith("day_")],
                  key=lambda x: int(x.split("_")[1]))
    paper_title = curriculum.get("_meta", {}).get("paper_title", paper_id)
    items = []
    for k in keys:
        num = int(k.split("_")[1])
        title = html.escape(curriculum[k].get("title", ""))
        items.append(
            f'<li data-day="{num}"><a href="day_{num}.html">'
            f'<div class="day-num">DAY {num}</div>'
            f'<div class="day-title">{title}</div>'
            '</a></li>'
        )
    body = f"""
<div class="index-meta">arXiv {paper_id}</div>
<h1 class="index-title">{html.escape(paper_title)}</h1>
<ul class="day-list">{chr(10).join(items)}</ul>
<script>
const params = new URLSearchParams(window.location.search);
const today = params.get('day');
if (today) {{
  const el = document.querySelector(`li[data-day="${{today}}"]`);
  if (el) {{
    el.classList.add('today');
    const badge = document.createElement('span');
    badge.className = 'today-badge';
    badge.textContent = '오늘';
    el.querySelector('.day-num').appendChild(badge);
    el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
  }}
}}
</script>"""
    return page(f"{paper_title} — 10일 마이크로러닝", body)


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
    
    for k in day_keys:
        num = int(k.split("_")[1])
        html_text = render_day(num, curriculum[k], total)
        with open(f"{out_dir}/day_{num}.html", "w", encoding="utf-8") as f:
            f.write(html_text)
    
    with open(f"{out_dir}/index.html", "w", encoding="utf-8") as f:
        f.write(render_index(curriculum, arxiv_id))
    
    abs_path = os.path.abspath(f"{out_dir}/index.html")
    print(f"\n렌더 완료: {out_dir}/")
    print(f"  브라우저: file:///{abs_path.replace(chr(92), '/')}")


if __name__ == "__main__":
    arxiv_id = sys.argv[1] if len(sys.argv) > 1 else "2401.01339"
    render_paper(arxiv_id)