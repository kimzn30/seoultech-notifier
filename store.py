"""이미 알림을 보낸 게시글 id를 로컬 JSON 파일에 기록해 중복 알림을 막는다."""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent / "seen_posts.json"


def load_seen(path: Path = DEFAULT_PATH) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        return set(json.load(f))


def save_seen(keys: set[str], path: Path = DEFAULT_PATH) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(sorted(keys), f, ensure_ascii=False, indent=2)
