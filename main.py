"""서울과학기술대학교 공지 알림 서비스 — 1회 실행 진입점.

boards.json에 등록된 각 게시판을 스캔해 처음 보는 글만 골라
등록된 다중 구독자(subscribers.json) 또는 기본 수신자에게 이메일로 보내고,
보낸 글의 id를 seen_posts.json에 기록한다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from notifier import send_email, send_notifications_to_subscribers
from scraper import Post, fetch_board
from store import DEFAULT_PATH, load_seen, save_seen
from subscribers import load_subscribers

BOARDS_PATH = Path(__file__).parent / "boards.json"


def load_boards() -> list[dict]:
    with BOARDS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    load_dotenv()

    first_run = not DEFAULT_PATH.exists()

    boards = load_boards()
    seen = load_seen()
    new_posts: list[Post] = []

    for board in boards:
        try:
            posts = fetch_board(board)
        except Exception as e:
            print(f"[경고] {board['name']} 스캔 실패: {e}", file=sys.stderr)
            continue

        for post in posts:
            if post.key not in seen:
                new_posts.append(post)

    if not new_posts:
        print("새 게시글 없음.")
        return

    if first_run:
        # 최초 실행 시 기존 글을 전부 메일로 보내면 스팸이 되므로,
        # 현재 게시판 상태를 기준선으로만 저장하고 알림은 다음 실행부터 보낸다.
        print(f"최초 실행: 기존 게시글 {len(new_posts)}건을 기준선으로 저장 (메일 발송 없음).")
    else:
        print(f"새 게시글 {len(new_posts)}건 발견, 이메일 발송 중...")
        try:
            subscribers = load_subscribers()
            if subscribers:
                sent = send_notifications_to_subscribers(new_posts, subscribers)
                print(f"다중 구독자 {len(subscribers)}명 중 {sent}명에게 발송 완료.")
            else:
                send_email(new_posts)
                print("기본 수신자에게 발송 완료.")
        except KeyError as e:
            print(
                f"[오류] 환경변수 {e}가 설정되지 않았습니다. "
                ".env 파일에 EMAIL_ADDRESS / EMAIL_APP_PASSWORD를 설정하세요.",
                file=sys.stderr,
            )
            return
        except Exception as e:
            print(f"[오류] 메일 발송 실패: {e}", file=sys.stderr)
            return

    seen.update(p.key for p in new_posts)
    save_seen(seen)


if __name__ == "__main__":
    main()
