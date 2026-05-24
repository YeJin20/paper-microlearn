# paper_download.py
import os
import re
import requests


def extract_arxiv_id(url: str) -> str:
    """arXiv URL에서 paper ID 추출.
    
    예: https://arxiv.org/abs/2401.01339 → 2401.01339
    """
    match = re.search(r'(\d{4}\.\d{4,5})', url)
    if not match:
        raise ValueError(f"arXiv ID를 추출할 수 없음: {url}")
    return match.group(1)


def download_arxiv_pdf(url: str, output_dir: str = "papers") -> str:
    """arXiv URL을 받아 PDF 다운로드, 저장 경로 반환."""
    arxiv_id = extract_arxiv_id(url)
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{arxiv_id}.pdf")
    
    if os.path.exists(output_path):
        print(f"이미 다운로드됨: {output_path}")
        return output_path
    
    print(f"다운로드 중: {pdf_url}")
    response = requests.get(pdf_url, timeout=60)
    response.raise_for_status()
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    size_kb = len(response.content) / 1024
    print(f"저장 완료: {output_path} ({size_kb:.1f} KB)")
    return output_path


if __name__ == "__main__":
    # Street Gaussians로 테스트
    pdf_path = download_arxiv_pdf("https://arxiv.org/abs/2401.01339")
    print(f"\n✓ 다음 단계용 PDF 경로: {pdf_path}")