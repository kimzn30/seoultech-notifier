from __future__ import annotations

import io
import sys
import unittest
from unittest.mock import MagicMock, patch

from main import main
from scraper import Post


class TestMain(unittest.TestCase):
    @patch("main.load_dotenv")
    @patch("main.load_boards")
    @patch("main.fetch_board")
    @patch("main.save_seen")
    @patch("main.load_seen")
    @patch("main.DEFAULT_PATH")
    @patch("main.send_email")
    def test_first_run_saves_baseline_only(
        self,
        mock_send_email,
        mock_default_path,
        mock_load_seen,
        mock_save_seen,
        mock_fetch_board,
        mock_load_boards,
        mock_load_dotenv,
    ):
        mock_default_path.exists.return_value = False
        mock_load_boards.return_value = [{"id": "academic", "name": "학사공지"}]
        mock_load_seen.return_value = set()

        sample_post = Post(
            board_id="academic",
            board_name="학사공지",
            post_id="101",
            title="기존 공지",
            url="https://example.com/101",
            date="2026-08-25",
            writer="교무처",
        )
        mock_fetch_board.return_value = [sample_post]

        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            main()

        # 최초 실행 시 메일은 발송되지 않고, baseline으로 저장되어야 함
        mock_send_email.assert_not_called()
        mock_save_seen.assert_called_once_with({"academic:101"})
        self.assertIn("최초 실행: 기존 게시글 1건을 기준선으로 저장", captured_stdout.getvalue())

    @patch("main.load_dotenv")
    @patch("main.load_boards")
    @patch("main.fetch_board")
    @patch("main.save_seen")
    @patch("main.load_seen")
    @patch("main.DEFAULT_PATH")
    @patch("main.send_email")
    def test_subsequent_run_with_new_post(
        self,
        mock_send_email,
        mock_default_path,
        mock_load_seen,
        mock_save_seen,
        mock_fetch_board,
        mock_load_boards,
        mock_load_dotenv,
    ):
        mock_default_path.exists.return_value = True
        mock_load_boards.return_value = [{"id": "academic", "name": "학사공지"}]
        mock_load_seen.return_value = {"academic:100"}

        p_old = Post("academic", "학사공지", "100", "오래된 공지", "https://example.com/100", "2026-08-20", "교무처")
        p_new = Post("academic", "학사공지", "101", "새로운 공지", "https://example.com/101", "2026-08-25", "교무처")
        mock_fetch_board.return_value = [p_old, p_new]

        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            main()

        mock_send_email.assert_called_once_with([p_new])
        mock_save_seen.assert_called_once_with({"academic:100", "academic:101"})
        self.assertIn("새 게시글 1건 발견, 이메일 발송 중...", captured_stdout.getvalue())

    @patch("main.load_dotenv")
    @patch("main.load_boards")
    @patch("main.fetch_board")
    @patch("main.save_seen")
    @patch("main.load_seen")
    @patch("main.DEFAULT_PATH")
    @patch("main.send_email")
    def test_no_new_posts(
        self,
        mock_send_email,
        mock_default_path,
        mock_load_seen,
        mock_save_seen,
        mock_fetch_board,
        mock_load_boards,
        mock_load_dotenv,
    ):
        mock_default_path.exists.return_value = True
        mock_load_boards.return_value = [{"id": "academic", "name": "학사공지"}]
        mock_load_seen.return_value = {"academic:100"}

        p_old = Post("academic", "학사공지", "100", "오래된 공지", "https://example.com/100", "2026-08-20", "교무처")
        mock_fetch_board.return_value = [p_old]

        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            main()

        mock_send_email.assert_not_called()
        mock_save_seen.assert_not_called()
        self.assertIn("새 게시글 없음.", captured_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
