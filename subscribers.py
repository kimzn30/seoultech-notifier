"""다중 사용자 이메일 구독 및 맞춤 알림(게시판·키워드 필터) 관리 모듈."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scraper import Post

DEFAULT_SUBSCRIBERS_PATH = Path(__file__).parent / "subscribers.json"
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def is_valid_email(email: str) -> bool:
    """간단한 이메일 형식 유효성 검사."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def load_subscribers(path: Path = DEFAULT_SUBSCRIBERS_PATH) -> list[dict]:
    """등록된 구독자 목록 로드."""
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_subscribers(subscribers: list[dict], path: Path = DEFAULT_SUBSCRIBERS_PATH) -> None:
    """구독자 목록을 JSON 파일로 저장."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(subscribers, f, ensure_ascii=False, indent=2)


def add_subscriber(
    email: str,
    boards: list[str] | None = None,
    keywords: list[str] | None = None,
    path: Path = DEFAULT_SUBSCRIBERS_PATH,
) -> tuple[bool, str]:
    """신규 구독자 추가 또는 기존 구독자 설정 갱신.

    Args:
        email: 사용자 이메일 주소
        boards: 수신할 게시판 ID 목록 (None이면 전체 수신)
        keywords: 관심 키워드 목록 (None이면 모든 글 수신)
        path: 저장 파일 경로

    Returns:
        (성공여부, 메시지)
    """
    clean_email = email.strip().lower()
    if not is_valid_email(clean_email):
        return False, "올바른 이메일 형식이 아닙니다."

    if boards is None or len(boards) == 0:
        boards = ["academic", "scholarship", "contest"]

    clean_keywords = [k.strip() for k in (keywords or []) if k.strip()]

    subscribers = load_subscribers(path)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 기존 구독자인 경우 설정 갱신
    for sub in subscribers:
        if sub["email"] == clean_email:
            sub["boards"] = boards
            sub["keywords"] = clean_keywords
            sub["updated_at"] = now_str
            save_subscribers(subscribers, path)
            return True, f"구독 설정이 갱신되었습니다. ({clean_email})"

    # 신규 등록
    new_sub = {
        "email": clean_email,
        "boards": boards,
        "keywords": clean_keywords,
        "created_at": now_str,
    }
    subscribers.append(new_sub)
    save_subscribers(subscribers, path)
    return True, f"성공적으로 구독되었습니다! ({clean_email})"


def remove_subscriber(email: str, path: Path = DEFAULT_SUBSCRIBERS_PATH) -> tuple[bool, str]:
    """구독 해지."""
    clean_email = email.strip().lower()
    subscribers = load_subscribers(path)
    filtered = [s for s in subscribers if s["email"] != clean_email]

    if len(filtered) == len(subscribers):
        return False, "등록되지 않은 이메일 주소입니다."

    save_subscribers(filtered, path)
    return True, f"구독이 정상적으로 해지되었습니다. ({clean_email})"


def get_subscriber(email: str, path: Path = DEFAULT_SUBSCRIBERS_PATH) -> dict | None:
    """특정 구독자 정보 조회."""
    clean_email = email.strip().lower()
    subscribers = load_subscribers(path)
    for s in subscribers:
        if s["email"] == clean_email:
            return s
    return None


def filter_posts_for_subscriber(subscriber: dict, posts: list[Post]) -> list[Post]:
    """구독자의 게시판 및 키워드 설정에 맞게 공지 목록 필터링."""
    allowed_boards = set(subscriber.get("boards", ["academic", "scholarship", "contest"]))
    keywords = [k.lower() for k in subscriber.get("keywords", []) if k]

    matched: list[Post] = []
    for post in posts:
        # 1. 게시판 필터
        if allowed_boards and post.board_id not in allowed_boards:
            continue

        # 2. 키워드 필터 (키워드가 등록되어 있는 경우에만 필터링, 없으면 해당 게시판 전체 수신)
        if keywords:
            title_lower = post.title.lower()
            if not any(k in title_lower for k in keywords):
                continue

        matched.append(post)

    return matched
