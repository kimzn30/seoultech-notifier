from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from notifier import (
    build_html_email,
    send_notifications_to_subscribers,
    send_welcome_digest,
)
from scraper import Post


class TestHtmlNotifier(unittest.TestCase):
    def setUp(self):
        self.sample_posts = [
            Post("academic", "학사공지", "101", "2학기 수강신청 일정 안내", "https://example.com/101", "2026-08-25", "교무처"),
            Post("scholarship", "장학공지", "202", "국가장학금 신청 안내", "https://example.com/202", "2026-08-26", "장학복지팀"),
        ]

    def test_build_html_email_contains_elements(self):
        html_text = build_html_email(self.sample_posts, title_text="맞춤 공지 브리핑")
        self.assertIn("맞춤 공지 브리핑", html_text)
        self.assertIn("2학기 수강신청 일정 안내", html_text)
        self.assertIn("국가장학금 신청 안내", html_text)
        self.assertIn("학사공지", html_text)
        self.assertIn("장학공지", html_text)
        self.assertIn("원문 보기", html_text)
        self.assertIn("교무처", html_text)

    @patch("notifier._send_raw_smtp")
    def test_send_welcome_digest(self, mock_send):
        ok = send_welcome_digest("user@test.com", self.sample_posts)
        self.assertTrue(ok)
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        self.assertEqual(args[0], "user@test.com")
        self.assertIn("[서울과기대 알림] 구독 완료!", args[1])

    @patch("notifier._send_raw_smtp")
    def test_send_notifications_to_subscribers(self, mock_send):
        subscribers = [
            {"email": "student1@test.com", "boards": ["academic"], "keywords": []},
            {"email": "student2@test.com", "boards": ["scholarship"], "keywords": ["국가장학금"]},
            {"email": "student3@test.com", "boards": ["contest"], "keywords": []},  # 공모전만 구독 -> 일치하는 글 없음
        ]

        sent_count = send_notifications_to_subscribers(self.sample_posts, subscribers)
        self.assertEqual(sent_count, 2)
        self.assertEqual(mock_send.call_count, 2)


if __name__ == "__main__":
    unittest.main()
