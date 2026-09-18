"""Freeze existing metadata-only selection; additional seeds stay opt-in."""
import importlib.util
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from expgym import task_restricted_search as search


class SearchSnapshotSelectionTest(unittest.TestCase):
    def test_default_and_explicit_seed_parsing(self):
        self.assertEqual(search._resolve_seed(None), 1)
        for seed in (1, 2, 3):
            self.assertEqual(search._resolve_seed("phantom_seed{}".format(seed)), seed)
        for invalid in ("seed2", "phantom_seed1,phantom_seed2", "phantom_seed-1"):
            with self.assertRaises(ValueError):
                search._parse_data_source(invalid)

    def test_original_filter_and_stable_order_do_not_depend_on_scores(self):
        rows = [
            {"question": "last", "type": 28, "difficulty": 8, "answer": ["x"]},
            {"question": "first tie", "type": 11, "difficulty": 3, "answer": ["x"]},
            {"question": "excluded type", "type": 10, "difficulty": 3, "answer": ["x"]},
            {"question": "excluded count", "type": 12, "difficulty": 3, "answer": ["x"] * 21},
            {"question": "second tie", "type": 11, "difficulty": 3, "answer": ["x"] * 20},
            {"question": "type 27", "type": 27, "difficulty": 10, "answer": ["x"]},
        ]
        with patch.dict(search._QA_CACHE, {}, clear=True), patch.object(
            search, "_read_parquet_table", return_value=SimpleNamespace(to_pylist=lambda: rows)
        ) as read:
            selected = search._load_qa(1)
        self.assertEqual([r["question"] for r in selected], ["first tie", "second tie", "type 27", "last"])
        self.assertEqual(read.call_args[1]["columns"], ["question", "answer", "type", "difficulty"])
        self.assertIn("depth_20_size_5000_seed_1-", read.call_args[0][0])

    def test_seed_caches_are_separate_and_require_no_default_selector_change(self):
        def read(path, columns):
            seed = 2 if "seed_2-" in path else 1
            rows = [{"question": "seed{}".format(seed), "type": 11, "difficulty": 3, "answer": ["x"]}]
            return SimpleNamespace(to_pylist=lambda: rows)

        with patch.dict(search._QA_CACHE, {}, clear=True), patch.object(search, "_read_parquet_table", side_effect=read) as load:
            first = search._load_qa(1)
            second = search._load_qa(2)
            self.assertIs(search._load_qa(1), first)
            self.assertEqual(search.get_source_count("phantom_seed2"), 1)
            self.assertEqual(load.call_count, 2)
        self.assertEqual(first[0]["question"], "seed1")
        self.assertEqual(second[0]["question"], "seed2")

    def test_all_scenario_hooks_use_the_explicit_seed(self):
        rows = [{"question": "Who is Alice?", "answer": ["Alice Example"]}]
        with patch.object(search, "_load_qa", return_value=rows) as qa, patch.object(search, "_load_corpus", return_value={}) as corpus:
            search.build_tools(data_source="phantom_seed2")
            context = search.build_context(False, data_source="phantom_seed2")
            search.build_fake_plan(1, data_source="phantom_seed2")
            evaluator = search.build_answer_evaluator(0, data_source="phantom_seed2")
        corpus.assert_called_once_with(2)
        self.assertTrue(all(call[0] == (2,) for call in qa.call_args_list))
        self.assertEqual(qa.call_count, 3)
        self.assertIn("Who is Alice?", context)
        self.assertEqual(evaluator("Alice Example"), 1.0)

    @unittest.skipUnless(importlib.util.find_spec("pyarrow") is not None and all(
        os.path.isfile(os.path.join(search.QA_DIR, "depth_20_size_5000_seed_{}-00000-of-00001.parquet".format(seed)))
        for seed in (1, 2, 3)
    ), "Pinned local PhantomWiki snapshot and pyarrow unavailable")
    def test_pinned_local_seed_counts_and_default_paper_subset_stay_unchanged(self):
        self.assertEqual(search.get_source_count("phantom_seed1"), 35)
        self.assertEqual(search.get_source_count("phantom_seed2"), 36)
        self.assertEqual(search.get_source_count("phantom_seed3"), 37)
        rows = search._load_qa(search._resolve_seed(None))
        self.assertTrue(all(row["type"] in (11, 12) for row in rows[:18]))
        self.assertTrue(all(row["type"] in (27, 28) for row in rows[18:]))


if __name__ == "__main__":
    unittest.main()
