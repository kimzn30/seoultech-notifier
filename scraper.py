"""서울과학기술대학교 공지 게시판 스크레이퍼.

세 개의 기본 게시판(학사공지/장학공지/공모·외부행사)은 학교 홈페이지의
같은 게시판 템플릿(tr.body_tr / td.tit.dn2)을 공유하므로 하나의 파서로
처리한다. 다른 도메인(예: 링커리어 등)을 추가하려면 boards.json에 항목을
추가하고, 필요하면 이 파일에 전용 파서 함수를 만들어 연결하면 된다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SeoultechNotifier/1.0)"}
TIMEOUT = 15


@dataclass
class Post:
    board_id: str
    board_name: str
    post_id: str
    title: str
    url: str
    date: str
    writer: str

    @property
    def key(self) -> str:
        return f"{self.board_id}:{self.post_id}"


def fetch_seoultech_board(board: dict) -> list[Post]:
    resp = requests.get(board["url"], headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    posts: list[Post] = []
    for row in soup.select("tr.body_tr"):
        link = row.select_one("td.tit a[href]")
        if not link:
            continue
        title = link.get_text(strip=True)
        href = link["href"]
        full_url = urljoin(board["url"], href)

        m = re.search(r"bidx=(\d+)", href)
        post_id = m.group(1) if m else href

        date_cell = row.select_one("td.dn5")
        writer_cell = row.select_one("td.dn4")
        date = date_cell.get_text(strip=True) if date_cell else ""
        writer = writer_cell.get_text(strip=True) if writer_cell else ""

        posts.append(
            Post(
                board_id=board["id"],
                board_name=board["name"],
                post_id=post_id,
                title=title,
                url=full_url,
                date=date,
                writer=writer,
            )
        )
    return posts


# 사이트마다 파서가 다를 수 있으므로 board별로 파서를 매핑한다.
# boards.json 항목에 "parser": "seoultech" 를 지정하지 않으면 기본값으로 이 파서를 쓴다.
PARSERS = {
    "seoultech": fetch_seoultech_board,
}


def fetch_board(board: dict) -> list[Post]:
    parser_name = board.get("parser", "seoultech")
    parser = PARSERS.get(parser_name)
    if parser is None:
        raise ValueError(f"알 수 없는 parser: {parser_name} (board={board['id']})")
    return parser(board)
