from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scraper import Post
from subscribers import (
    add_subscriber,
    filter_posts_for_subscriber,
    get_subscriber,
    is_valid_email,
    load_subscribers,
    remove_subscriber,
    save_subscribers,
)


class TestSubscribers(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_sub_path = Path(self.temp_dir.name) / "test_subscribers.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_is_valid_email(self):
        self.assertTrue(is_valid_email("user@example.com"))
        self.assertTrue(is_valid_email("student.123@seoultech.ac.kr"))
        self.assertFalse(is_valid_email("invalid-email"))
        self.assertFalse(is_valid_email("@domain.com"))
        self.assertFalse(is_valid_email(""))

    def test_add_and_get_subscriber(self):
        ok, msg = add_subscriber(
            "student@seoultech.ac.kr",
            boards=["scholarship", "contest"],
            keywords=["장학금", "해커톤"],
            path=self.test_sub_path,
        )
        self.assertTrue(ok)
        self.assertIn("성공적으로 구독되었습니다", msg)

        sub = get_subscriber("student@seoultech.ac.kr", path=self.test_sub_path)
        self.assertIsNotNone(sub)
        self.assertEqual(sub["email"], "student@seoultech.ac.kr")
        self.assertEqual(sub["boards"], ["scholarship", "contest"])
        self.assertEqual(sub["keywords"], ["장학금", "해커톤"])

    def test_update_existing_subscriber(self):
        add_subscriber("user@gmail.com", boards=["academic"], keywords=[], path=self.test_sub_path)
        # Update settings
        ok, msg = add_subscriber(
            "user@gmail.com",
            boards=["academic", "contest"],
            keywords=["인턴"],
            path=self.test_sub_path,
        )
        self.assertTrue(ok)
        self.assertIn("갱신되었습니다", msg)

        sub = get_subscriber("user@gmail.com", path=self.test_sub_path)
        self.assertEqual(sub["boards"], ["academic", "contest"])
        self.assertEqual(sub["keywords"], ["인턴"])

    def test_remove_subscriber(self):
        add_subscriber("user@gmail.com", path=self.test_sub_path)
        ok, msg = remove_subscriber("user@gmail.com", path=self.test_sub_path)
        self.assertTrue(ok)

        # Re-check removal
        self.assertIsNone(get_subscriber("user@gmail.com", path=self.test_sub_path))

        # Try removing again
        ok, msg = remove_subscriber("user@gmail.com", path=self.test_sub_path)
        self.assertFalse(ok)

    def test_filter_posts_for_subscriber(self):
        sub = {
            "email": "user@gmail.com",
            "boards": ["scholarship", "contest"],
            "keywords": ["성적우수", "아이디어"],
        }

        posts = [
            Post("academic", "학사공지", "1", "학사 일정 공지", "http://a", "2026-08-25", "작성자"),
            Post("scholarship", "장학공지", "2", "2026 성적우수 장학금 신청", "http://b", "2026-08-25", "작성자"),
            Post("scholarship", "장학공지", "3", "일반 근로장학 모집", "http://c", "2026-08-25", "작성자"),
            Post("contest", "공모전", "4", "창업 아이디어 경진대회", "http://d", "2026-08-25", "작성자"),
        ]

        filtered = filter_posts_for_subscriber(sub, posts)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].post_id, "2")
        self.assertEqual(filtered[1].post_id, "4")


if __name__ == "__main__":
    unittest.main()
