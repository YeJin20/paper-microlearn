# generate_curriculum.py
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from paper_download import download_arxiv_pdf
from pdf_extract import extract_pdf_text


CLAUDE_EXE = r"C:\Users\g1415\.local\bin\claude.exe"
PROMPT_FILE = "prompts/v2.txt"
CURRICULA_DIR = "curricula"
DEFAULT_GOAL = "applying this paper to autonomous driving research"


def get_goal(arxiv_id: str, cli_goal: str = None) -> str:
    """우선순위: CLI --goal > 기존 JSON _meta.goal > DEFAULT_GOAL"""
    if cli_goal:
        return cli_goal
    json_path = f"{CURRICULA_DIR}/{arxiv_id}.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("_meta", {}).get("goal", DEFAULT_GOAL)
        except Exception:
            pass
    return DEFAULT_GOAL


def load_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def call_claude(prompt: str) -> str:
    result = subprocess.run(
        [CLAUDE_EXE, "-p", prompt, "--allowedTools", "Read"],
        capture_output=True, text=True, encoding="utf-8", timeout=900,
    )
    if result.returncode != 0:
        print(f"Claude Code 에러 ({result.returncode}):\n{result.stderr}")
        sys.exit(1)
    return result.stdout


def extract_json(text: str) -> dict:
    """Claude 출력에서 JSON 추출. 코드펜스/preamble 제거."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        text = text[first:last + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        with open("debug_raw_response.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print(f"JSON 파싱 실패: {e}")
        print(f"원본 응답을 debug_raw_response.txt에 저장")
        sys.exit(1)


def generate_curriculum(input_arg: str, cli_goal: str = None) -> dict:
    # 1. PDF 확보
    if input_arg.startswith("http"):
        pdf_path = download_arxiv_pdf(input_arg)
    else:
        if not os.path.exists(input_arg):
            raise FileNotFoundError(f"파일 없음: {input_arg}")
        arxiv_id_tmp = Path(input_arg).stem
        pdf_path = f"papers/{arxiv_id_tmp}.pdf"
        os.makedirs("papers", exist_ok=True)
        if input_arg != pdf_path and not os.path.exists(pdf_path):
            shutil.copy(input_arg, pdf_path)
    
    arxiv_id = Path(pdf_path).stem
    
    # 2. 텍스트 추출
    txt_path = pdf_path.replace(".pdf", ".txt")
    if not os.path.exists(txt_path):
        extract_pdf_text(pdf_path)
    
    # 3. Goal 결정 + 프롬프트 구성
    goal = get_goal(arxiv_id, cli_goal)
    print(f"\n학습 목표 (goal): {goal}")
    
    template = load_prompt()
    template = template.replace("{goal}", goal)  # placeholder 치환
    full_prompt = (
        template
        + f"\n\n## PAPER FILE\n"
        + f"The paper text is in: {txt_path}\n"
        + "Read that file using the Read tool, then output the JSON. "
        + "Output ONLY the JSON object, no other text, no markdown fences, no preamble."
    )
    
    # 4. Claude Code 호출
    print(f"\n[Claude Code 호출 중... 1-3분 걸릴 수 있음]")
    response = call_claude(full_prompt)
    
    # 5. JSON 파싱 + 메타데이터 주입
    curriculum = extract_json(response)
    curriculum["_meta"] = {
        "goal": goal,
        "generated_at": datetime.datetime.now().isoformat(),
        "source_pdf": pdf_path,
    }
    
    # 6. 저장
    os.makedirs(CURRICULA_DIR, exist_ok=True)
    output_path = os.path.join(CURRICULA_DIR, f"{arxiv_id}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(curriculum, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 커리큘럼 저장: {output_path}")
    day_count = len([k for k in curriculum if k.startswith("day_")])
    print(f"  Day 수: {day_count}")
    print(f"  Goal: {goal}")
    
    return curriculum


def parse_args(argv):
    """간단한 --goal 파싱."""
    input_arg = None
    goal = None
    i = 0
    while i < len(argv):
        if argv[i] == "--goal" and i + 1 < len(argv):
            goal = argv[i + 1]
            i += 2
        else:
            if input_arg is None:
                input_arg = argv[i]
            i += 1
    return input_arg, goal


if __name__ == "__main__":
    input_arg, cli_goal = parse_args(sys.argv[1:])
    if input_arg is None:
        input_arg = "https://arxiv.org/abs/2401.01339"
    
    curriculum = generate_curriculum(input_arg, cli_goal)
    
    if "day_1" in curriculum:
        d1 = curriculum["day_1"]
        print(f"\n--- Day 1 미리보기 ---")
        print(f"제목: {d1.get('title', '')}")
        print(f"내용:\n{d1.get('content', '')[:300]}...")