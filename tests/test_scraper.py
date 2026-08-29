from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scraper import Post, fetch_board, fetch_seoultech_board

FIXTURE_HTML = (Path(__file__).parent / "sample_board.html").read_text(encoding="utf-8")


class TestScraper(unittest.TestCase):
    def test_post_dataclass_and_key(self):
        p = Post(
            board_id="academic",
            board_name="학사공지",
            post_id="12345",
            title="수강신청 안내",
            url="https://www.seoultech.ac.kr/service/info/matters/?bidx=12345",
            date="2026-08-25",
            writer="교무처",
        )
        self.assertEqual(p.key, "academic:12345")

    @patch("scraper.requests.get")
    def test_fetch_seoultech_board(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = FIXTURE_HTML
        mock_resp.apparent_encoding = "utf-8"
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        board = {
            "id": "scholarship",
            "name": "장학공지",
            "url": "https://www.seoultech.ac.kr/service/info/janghak/",
        }

        posts = fetch_seoultech_board(board)

        self.assertEqual(len(posts), 2)

        # 1번째 글 검증
        p1 = posts[0]
        self.assertEqual(p1.board_id, "scholarship")
        self.assertEqual(p1.board_name, "장학공지")
        self.assertEqual(p1.post_id, "894350")
        self.assertEqual(p1.title, "2026학년도 2학기 교내장학금 신청 안내")
        self.assertEqual(p1.writer, "학생지원팀")
        self.assertEqual(p1.date, "2026-08-25")
        self.assertEqual(p1.key, "scholarship:894350")
        self.assertIn("bidx=894350", p1.url)

        # 2번째 글 검증
        p2 = posts[1]
        self.assertEqual(p2.post_id, "894351")
        self.assertEqual(p2.title, "[공모전] 2026 AI 공공서비스 아이디어 경진대회")
        self.assertEqual(p2.writer, "취창업지원처")
        self.assertEqual(p2.date, "2026-08-26")

    def test_fetch_board_default_parser(self):
        mock_parser = MagicMock(return_value=[])
        with patch.dict("scraper.PARSERS", {"seoultech": mock_parser}):
            board = {"id": "test", "name": "테스트", "url": "https://example.com"}
            fetch_board(board)
            mock_parser.assert_called_once_with(board)

    def test_fetch_board_custom_parser(self):
        mock_custom_parser = MagicMock(return_value=[])
        with patch.dict("scraper.PARSERS", {"custom": mock_custom_parser}):
            board = {"id": "test", "name": "테스트", "url": "https://example.com", "parser": "custom"}
            fetch_board(board)
            mock_custom_parser.assert_called_once_with(board)

    def test_fetch_board_unknown_parser(self):
        board = {"id": "test", "name": "테스트", "url": "https://example.com", "parser": "unknown"}
        with self.assertRaises(ValueError):
            fetch_board(board)


if __name__ == "__main__":
    unittest.main()
