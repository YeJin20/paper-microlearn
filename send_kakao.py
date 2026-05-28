# python send_kakao.py --all

"""Day 메시지를 본인 카톡 '나와의 채팅방'으로 발송."""
import datetime
import json
import os
import sys

import requests
from dotenv import load_dotenv


load_dotenv()

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "").rstrip("/")
TOKEN_FILE = "tokens/kakao_tokens.json"
CURRICULA_DIR = "curricula"
GLOBAL_PROGRESS = "progress/_global.json"

def get_cumulative_day_count() -> int:
    """오늘 포함 누적 학습 일수. 오늘 날짜 자동 기록."""
    today = datetime.date.today().isoformat()
    if os.path.exists(GLOBAL_PROGRESS):
        with open(GLOBAL_PROGRESS, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"learning_dates": []}
    
    dates = set(data.get("learning_dates", []))
    if today not in dates:
        dates.add(today)
        data["learning_dates"] = sorted(dates)
        os.makedirs("progress", exist_ok=True)
        with open(GLOBAL_PROGRESS, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return len(dates)

def load_tokens() -> dict:
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tokens(tokens: dict):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)


def refresh_tokens(refresh_token: str) -> dict:
    """refresh_token으로 새 access_token 받기."""
    data = {
        "grant_type": "refresh_token",
        "client_id": KAKAO_REST_API_KEY,
        "refresh_token": refresh_token,
    }
    if KAKAO_CLIENT_SECRET:
        data["client_secret"] = KAKAO_CLIENT_SECRET
    
    response = requests.post("https://kauth.kakao.com/oauth/token", data=data)
    if response.status_code != 200:
        print(f"토큰 갱신 실패: {response.text}")
    response.raise_for_status()
    
    new_tokens = response.json()
    # refresh_token이 응답에 없으면 기존 거 유지
    if "refresh_token" not in new_tokens:
        new_tokens["refresh_token"] = refresh_token
    return new_tokens


def send_message(text: str, web_url: str, button_title: str = "학습 시작하기"):
    """카카오톡 '나에게 보내기' 발송. 토큰 만료 시 자동 갱신."""
    tokens = load_tokens()
    
    template = {
        "object_type": "text",
        "text": text,
        "link": {
            "web_url": web_url,
            "mobile_web_url": web_url,
        },
        "button_title": button_title,
    }
    
    def _post():
        return requests.post(
            "https://kapi.kakao.com/v2/api/talk/memo/default/send",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            data={"template_object": json.dumps(template, ensure_ascii=False)},
        )
    
    response = _post()
    
    # 토큰 만료 시 갱신 후 재시도
    if response.status_code == 401:
        print("access_token 만료 — 갱신 중...")
        new_tokens = refresh_tokens(tokens["refresh_token"])
        tokens.update(new_tokens)
        save_tokens(tokens)
        response = _post()
    
    if response.status_code != 200:
        print(f"발송 실패 ({response.status_code}): {response.text}")
    response.raise_for_status()
    return response.json()


def load_progress(arxiv_id: str) -> dict:
    path = f"progress/{arxiv_id}.json"
    if not os.path.exists(path):
        return {"current_day": 0, "last_sent_date": None}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(arxiv_id: str, progress: dict):
    os.makedirs("progress", exist_ok=True)
    with open(f"progress/{arxiv_id}.json", "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def send_day(arxiv_id: str, day_num: int = None):
    """특정 Day 발송. day_num이 None이면 진행도 기반 자동."""
    with open(f"{CURRICULA_DIR}/{arxiv_id}.json", "r", encoding="utf-8") as f:
        curriculum = json.load(f)
    
    total_days = len([k for k in curriculum if k.startswith("day_")])
    
    # 자동 모드 — 진행도 기반
    if day_num is None:
        progress = load_progress(arxiv_id)
        today = datetime.date.today().isoformat()
        last_sent = progress.get("last_sent_date")
        current = progress["current_day"]
        
        if last_sent == today:
            print(f"오늘은 이미 Day {current} 보냈어요.")
            print(f"수동 재발송: python send_kakao.py {current}")
            return
        
        current = 1 if last_sent is None else current + 1
        
        if current > total_days:
            print(f"Day {total_days}까지 다 보냈어요.")
            return
        
        day_num = current
        progress["current_day"] = current
        progress["last_sent_date"] = today
        save_progress(arxiv_id, progress)
    
    # 메시지 구성
    day_data = curriculum[f"day_{day_num}"]
    title = day_data.get("title", "")
    intent = day_data.get("intent", "")
    paper_title = curriculum.get("_meta", {}).get("paper_title", arxiv_id)
    get_cumulative_day_count()  # 누적 일자는 계속 기록만 (메시지엔 안 씀)
    text = f"{paper_title}\n\n{title}\n\n{intent}"
    if len(text) > 200:
        text = text[:197] + "..."
    
    web_url = f"{SITE_BASE_URL}/{arxiv_id}/?day={day_num}"
    
    print(f"발송 중...")
    print(f"  Day {day_num} / {total_days}: {title}")
    print(f"  URL: {web_url}")
    print(f"  메시지 ({len(text)}자):\n{text}")
    print()
    
    result = send_message(text, web_url)
    
    print("✓ 발송 완료. 카톡 '나와의 채팅방' 확인해보세요.")
    return result


if __name__ == "__main__":
    import glob
    
    args = sys.argv[1:]
    
    # --all 모드: curricula/ 안의 모든 논문 발송
    if "--all" in args:
        paper_files = sorted(glob.glob(f"{CURRICULA_DIR}/*.json"))
        if not paper_files:
            print("curricula/ 안에 논문이 없어요.")
            sys.exit(0)
        
        print(f"총 {len(paper_files)}개 논문 발송 시도\n")
        for path in paper_files:
            arxiv_id = os.path.basename(path).replace(".json", "")
            print(f"━━━ {arxiv_id} ━━━")
            try:
                send_day(arxiv_id)
            except Exception as e:
                print(f"  에러: {e}")
            print()
        sys.exit(0)
    
    # 단일 논문 모드
    arxiv_id = "2401.01339"
    day_num = None
    for arg in args:
        if arg.isdigit():
            day_num = int(arg)
        else:
            arxiv_id = arg
    
    send_day(arxiv_id, day_num)