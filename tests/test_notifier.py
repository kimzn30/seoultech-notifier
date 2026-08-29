from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from notifier import build_email_body, send_email
from scraper import Post


class TestNotifier(unittest.TestCase):
    def setUp(self):
        self.sample_posts = [
            Post(
                board_id="academic",
                board_name="학사공지",
                post_id="101",
                title="수강신청 일정 변경 안내",
                url="https://www.seoultech.ac.kr/service/info/matters/?bidx=101",
                date="2026-08-25",
                writer="교무처",
            ),
            Post(
                board_id="scholarship",
                board_name="장학공지",
                post_id="202",
                title="우수장학금 지급 대상자 발표",
                url="https://www.seoultech.ac.kr/service/info/janghak/?bidx=202",
                date="2026-08-26",
                writer="장학복지팀",
            ),
        ]

    def test_build_email_body(self):
        body = build_email_body(self.sample_posts)
        self.assertIn("[학사공지] 수강신청 일정 변경 안내", body)
        self.assertIn("작성자: 교무처  |  날짜: 2026-08-25", body)
        self.assertIn("https://www.seoultech.ac.kr/service/info/matters/?bidx=101", body)
        self.assertIn("[장학공지] 우수장학금 지급 대상자 발표", body)

    @patch("notifier.smtplib.SMTP_SSL")
    def test_send_email_empty_posts(self, mock_smtp):
        send_email([])
        mock_smtp.assert_not_called()

    @patch.dict(
        os.environ,
        {
            "EMAIL_ADDRESS": "test@gmail.com",
            "EMAIL_APP_PASSWORD": "app-password-secret",
            "EMAIL_TO": "receiver@gmail.com",
        },
        clear=True,
    )
    @patch("notifier.smtplib.SMTP_SSL")
    def test_send_email_success(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        send_email(self.sample_posts)

        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 465, timeout=15)
        mock_server.login.assert_called_once_with("test@gmail.com", "app-password-secret")
        self.assertTrue(mock_server.sendmail.called)
        args, kwargs = mock_server.sendmail.call_args
        self.assertEqual(args[0], "test@gmail.com")
        self.assertEqual(args[1], ["receiver@gmail.com"])
        raw_email = args[2]
        self.assertIn("Subject:", raw_email)
        self.assertIn("From:", raw_email)
        self.assertIn("To: receiver@gmail.com", raw_email)

    @patch.dict(os.environ, {}, clear=True)
    def test_send_email_missing_env(self):
        with self.assertRaises(KeyError):
            send_email(self.sample_posts)


if __name__ == "__main__":
    unittest.main()
