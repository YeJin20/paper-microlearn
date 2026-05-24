# generate_curriculum.py
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import shutil

from paper_download import download_arxiv_pdf
from pdf_extract import extract_pdf_text


CLAUDE_EXE = r"C:\Users\g1415\.local\bin\claude.exe"
PROMPT_FILE = "prompts/v2.txt"
CURRICULA_DIR = "curricula"


def load_prompt() -> str:
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def call_claude(prompt: str) -> str:
    """Claude Code 비대화형 호출."""
    result = subprocess.run(
        [
            CLAUDE_EXE,
            "-p", prompt,
            "--allowedTools", "Read",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=900,  # 15분
    )
    
    if result.returncode != 0:
        print(f"Claude Code 에러 (returncode {result.returncode}):")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    
    return result.stdout


def extract_json(text: str) -> dict:
    """Claude 출력에서 JSON 추출. 코드펜스/preamble 제거."""
    text = text.strip()
    # 마크다운 코드펜스 제거
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    
    # 첫 { 부터 마지막 } 까지만 추출 (앞뒤 preamble/후기 제거)
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


def generate_curriculum(input_arg: str) -> dict:
    # 1. PDF 확보 (URL 또는 로컬 경로)
    if input_arg.startswith("http"):
        pdf_path = download_arxiv_pdf(input_arg)
    else:
        # 로컬 파일 모드
        if not os.path.exists(input_arg):
            raise FileNotFoundError(f"파일 없음: {input_arg}")
        arxiv_id = Path(input_arg).stem  # 파일명 → ID
        pdf_path = f"papers/{arxiv_id}.pdf"
        os.makedirs("papers", exist_ok=True)
        if input_arg != pdf_path and not os.path.exists(pdf_path):
            shutil.copy(input_arg, pdf_path)
    
    # 2. 텍스트 추출 (없으면)
    txt_path = pdf_path.replace(".pdf", ".txt")
    if not os.path.exists(txt_path):
        extract_pdf_text(pdf_path)
    
    # 3. 프롬프트 + 파일 참조 구성
    template = load_prompt()
    full_prompt = (
        template
        + f"\n\n## PAPER FILE\n"
        + f"The paper text is in: {txt_path}\n"
        + "Read that file using the Read tool, then output the JSON. "
        + "Output ONLY the JSON object, no other text, no markdown fences."
    )
    
    # 4. Claude Code 호출
    print(f"\n[Claude Code 호출 중... 1-3분 걸릴 수 있음]")
    response = call_claude(full_prompt)
    
    # 5. JSON 파싱
    curriculum = extract_json(response)
    
    # 6. 저장
    arxiv_id = Path(pdf_path).stem
    os.makedirs(CURRICULA_DIR, exist_ok=True)
    output_path = os.path.join(CURRICULA_DIR, f"{arxiv_id}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(curriculum, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 커리큘럼 저장: {output_path}")
    day_count = len([k for k in curriculum if k.startswith("day_")])
    print(f"  Day 수: {day_count}")
    
    return curriculum


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://arxiv.org/abs/2401.01339"
    curriculum = generate_curriculum(url)
    
    # Day 1 미리보기
    if "day_1" in curriculum:
        d1 = curriculum["day_1"]
        print(f"\n--- Day 1 미리보기 ---")
        print(f"제목: {d1.get('title', '')}")
        print(f"내용:\n{d1.get('content', '')[:300]}...")