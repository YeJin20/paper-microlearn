# pdf_extract.py
import fitz  # pymupdf


def extract_pdf_text(pdf_path: str, output_path: str = None) -> str:
    """PDF에서 텍스트 추출, .txt 파일로 저장하고 텍스트 반환."""
    if output_path is None:
        output_path = pdf_path.replace(".pdf", ".txt")
    
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    
    text_parts = []
    for page_num, page in enumerate(doc):
        text_parts.append(f"\n--- Page {page_num + 1} ---\n")
        text_parts.append(page.get_text())
    doc.close()
    
    full_text = "\n".join(text_parts)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    print(f"추출 완료: {output_path}")
    print(f"  페이지 수: {num_pages}")
    print(f"  글자 수: {len(full_text):,}")
    
    return full_text


if __name__ == "__main__":
    pdf_path = "papers/2401.01339.pdf"
    text = extract_pdf_text(pdf_path)
    
    # 첫 500자 미리보기 — 추출이 제대로 됐는지 눈으로 확인
    print("\n--- 첫 500자 미리보기 ---")
    print(text[:500])