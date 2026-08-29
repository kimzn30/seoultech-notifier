from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from store import load_seen, save_seen


class TestStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name) / "test_seen.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_seen_nonexistent_file(self):
        seen = load_seen(self.test_path)
        self.assertEqual(seen, set())

    def test_save_and_load_seen(self):
        sample_keys = {"academic:100", "scholarship:200", "contest:300"}
        save_seen(sample_keys, self.test_path)

        loaded = load_seen(self.test_path)
        self.assertEqual(loaded, sample_keys)

    def test_save_seen_json_format_sorted(self):
        sample_keys = {"z_board:1", "a_board:2", "m_board:3"}
        save_seen(sample_keys, self.test_path)

        with self.test_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, list)
        self.assertEqual(data, ["a_board:2", "m_board:3", "z_board:1"])


if __name__ == "__main__":
    unittest.main()
