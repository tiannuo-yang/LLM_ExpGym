"""Tests for Phantom Wiki restricted search scenario."""
import json
import os
import unittest

from expgym.task_restricted_search import (
    CORPUS_DIR,
    PhantomSearchTools,
    QA_DIR,
    _extract_names,
    _load_corpus,
    _load_qa,
    _name_f1,
    _normalize_name,
    _parse_data_source,
    _stable_float,
    build_answer_evaluator,
    build_context,
    build_fake_plan,
    build_tools,
    get_source_count,
    SWEET_SPOT_TYPES,
    MAX_ANSWER_COUNT,
)

_HAS_PHANTOM_DATA = os.path.isdir(QA_DIR) and os.path.isdir(CORPUS_DIR)
_PHANTOM_SKIP_REASON = (
    "Phantom Wiki data not found at {}; set PHANTOM_WIKI_ROOT to enable these tests."
).format(QA_DIR)


# ---------------------------------------------------------------------------
# Data source parsing
# ---------------------------------------------------------------------------

class ParseDataSourceTest(unittest.TestCase):
    def test_seed1(self):
        self.assertEqual(_parse_data_source("phantom_seed1"), 1)

    def test_seed3(self):
        self.assertEqual(_parse_data_source("phantom_seed3"), 3)

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            _parse_data_source("musique_4hop")

    def test_no_seed_raises(self):
        with self.assertRaises(ValueError):
            _parse_data_source("phantom_seed")


# ---------------------------------------------------------------------------
# Data loading (requires data files)
# ---------------------------------------------------------------------------

@unittest.skipUnless(_HAS_PHANTOM_DATA, _PHANTOM_SKIP_REASON)
class DataLoadingTest(unittest.TestCase):
    def test_load_corpus_has_articles(self):
        corpus = _load_corpus(1)
        self.assertGreater(len(corpus), 4000)
        # Check an article has content
        first_title = next(iter(corpus))
        self.assertIn("#", corpus[first_title])

    def test_load_qa_filtered(self):
        qa = _load_qa(1)
        # All questions should be in sweet-spot types
        for row in qa:
            self.assertIn(row["type"], SWEET_SPOT_TYPES)
            self.assertLessEqual(len(row["answer"]), MAX_ANSWER_COUNT)

    def test_load_qa_sorted(self):
        qa = _load_qa(1)
        keys = [(r["type"], r["difficulty"]) for r in qa]
        self.assertEqual(keys, sorted(keys))

    def test_get_source_count(self):
        count = get_source_count("phantom_seed1")
        # Paper search set: seed 1, 3-hop whois+whatis questions.
        self.assertEqual(count, 35)

    def test_corpus_cached(self):
        c1 = _load_corpus(1)
        c2 = _load_corpus(1)
        self.assertIs(c1, c2)

    def test_qa_cached(self):
        q1 = _load_qa(1)
        q2 = _load_qa(1)
        self.assertIs(q1, q2)


# ---------------------------------------------------------------------------
# Name extraction & F1
# ---------------------------------------------------------------------------

class NormalizeNameTest(unittest.TestCase):
    def test_lowercase(self):
        self.assertEqual(_normalize_name("Alice Jones"), "alice jones")

    def test_extra_spaces(self):
        self.assertEqual(_normalize_name("  Alice   Jones  "), "alice jones")


class ExtractNamesTest(unittest.TestCase):
    def test_comma_separated(self):
        names = _extract_names("Alice Jones, Bob Smith, Carol Lee")
        self.assertEqual(names, {"alice jones", "bob smith", "carol lee"})

    def test_json_array(self):
        names = _extract_names('["Alice Jones", "Bob Smith"]')
        self.assertEqual(names, {"alice jones", "bob smith"})

    def test_newline_separated(self):
        names = _extract_names("Alice Jones\nBob Smith\nCarol Lee")
        self.assertEqual(names, {"alice jones", "bob smith", "carol lee"})

    def test_numbered_list(self):
        names = _extract_names("1. Alice Jones\n2. Bob Smith")
        self.assertEqual(names, {"alice jones", "bob smith"})

    def test_empty(self):
        self.assertEqual(_extract_names(""), set())
        self.assertEqual(_extract_names("   "), set())

    def test_single_name(self):
        names = _extract_names("Alice Jones")
        self.assertEqual(names, {"alice jones"})

    def test_filters_long_fragments(self):
        # More than 5 words should be filtered
        names = _extract_names(
            "Alice Jones, this is a very long sentence that is not a name"
        )
        self.assertIn("alice jones", names)


class NameF1Test(unittest.TestCase):
    def test_perfect_match(self):
        score = _name_f1("Alice Jones, Bob Smith", ["Alice Jones", "Bob Smith"])
        self.assertAlmostEqual(score, 1.0)

    def test_partial_recall(self):
        # pred=1, gold=2, tp=1 -> P=1.0, R=0.5, F1=2/3
        score = _name_f1("Alice Jones", ["Alice Jones", "Bob Smith"])
        self.assertAlmostEqual(score, 2 / 3, places=3)

    def test_partial_precision(self):
        # pred=2, gold=1, tp=1 -> P=0.5, R=1.0, F1=2/3
        score = _name_f1("Alice Jones, Carol Lee", ["Alice Jones"])
        self.assertAlmostEqual(score, 2 / 3, places=3)

    def test_zero_overlap(self):
        score = _name_f1("Charlie Brown", ["Alice Jones"])
        self.assertEqual(score, 0.0)

    def test_empty_prediction(self):
        score = _name_f1("", ["Alice Jones"])
        self.assertEqual(score, 0.0)

    def test_empty_gold(self):
        score = _name_f1("", [])
        self.assertEqual(score, 1.0)


# ---------------------------------------------------------------------------
# Search tool
# ---------------------------------------------------------------------------

class PhantomSearchToolsTest(unittest.TestCase):
    def setUp(self):
        self.corpus = {
            "Alice Jones": (
                "# Alice Jones\n\n## Family\n"
                "The father of Alice Jones is Bob Smith.\n"
                "## Friends\nThe friends of Alice Jones are Carol Lee."
            ),
            "Bob Smith": (
                "# Bob Smith\n\n## Family\n"
                "The daughter of Bob Smith is Alice Jones.\n"
                "## Attributes\nThe occupation of Bob Smith is teacher."
            ),
            "Carol Lee": (
                "# Carol Lee\n\n## Friends\n"
                "The friends of Carol Lee are Alice Jones."
            ),
        }
        self.tools = PhantomSearchTools(self.corpus)

    def test_exact_title_match(self):
        result, overhead = self.tools.search(json.dumps({"query": "Alice Jones"}))
        self.assertIn("Alice Jones", result)
        self.assertIn("Bob Smith", result)
        self.assertGreaterEqual(overhead, 280.0)
        self.assertLessEqual(overhead, 320.0)

    def test_case_insensitive(self):
        result, _ = self.tools.search(json.dumps({"query": "alice jones"}))
        self.assertIn("Alice Jones", result)

    def test_cached_query_free(self):
        _, oh1 = self.tools.search(json.dumps({"query": "Alice Jones"}))
        _, oh2 = self.tools.search(json.dumps({"query": "Alice Jones"}))
        self.assertGreater(oh1, 0)
        self.assertEqual(oh2, 0.0)

    def test_same_article_via_different_query_free(self):
        # First search by title
        _, oh1 = self.tools.search(json.dumps({"query": "Bob Smith"}))
        # Keyword search that also returns Bob Smith
        _, oh2 = self.tools.search(json.dumps({"query": "teacher occupation"}))
        self.assertGreater(oh1, 0)
        # Second should be free because Bob Smith article already seen
        self.assertEqual(oh2, 0.0)

    def test_keyword_search(self):
        result, overhead = self.tools.search(
            json.dumps({"query": "teacher occupation"})
        )
        self.assertIn("Bob Smith", result)
        # Overhead may be 0 if article already seen; test with fresh tools
        fresh = PhantomSearchTools(self.corpus)
        _, oh = fresh.search(json.dumps({"query": "teacher occupation"}))
        self.assertGreater(oh, 0)

    def test_no_results(self):
        result, overhead = self.tools.search(
            json.dumps({"query": "zzzznonexistent"})
        )
        self.assertIn("No matching", result)
        self.assertEqual(overhead, 0.0)

    def test_empty_query(self):
        result, overhead = self.tools.search(json.dumps({"query": ""}))
        self.assertIn("Error", result)
        self.assertEqual(overhead, 0.0)

    def test_deterministic_overhead(self):
        t1 = PhantomSearchTools(self.corpus)
        t2 = PhantomSearchTools(self.corpus)
        _, oh1 = t1.search(json.dumps({"query": "Alice Jones"}))
        _, oh2 = t2.search(json.dumps({"query": "Alice Jones"}))
        self.assertEqual(oh1, oh2)


# ---------------------------------------------------------------------------
# SCENARIO hooks
# ---------------------------------------------------------------------------

@unittest.skipUnless(_HAS_PHANTOM_DATA, _PHANTOM_SKIP_REASON)
class BuildContextTest(unittest.TestCase):
    def test_contains_question(self):
        ctx = build_context(False, row_index=0, data_source="phantom_seed1")
        self.assertIn("Question:", ctx)
        self.assertIn("search", ctx)

    def test_overhead_flag_ignored(self):
        """V16+: include_overhead no longer injects budget hints into context."""
        ctx_true = build_context(True, row_index=0, data_source="phantom_seed1")
        ctx_false = build_context(False, row_index=0, data_source="phantom_seed1")
        # Both should produce identical context (no overhead note injected)
        self.assertEqual(ctx_true, ctx_false)
        self.assertNotIn("300s", ctx_true)


@unittest.skipUnless(_HAS_PHANTOM_DATA, _PHANTOM_SKIP_REASON)
class BuildToolsTest(unittest.TestCase):
    def test_returns_search_tool(self):
        tools = build_tools(data_source="phantom_seed1")
        self.assertIn("search", tools)
        self.assertEqual(len(tools), 1)

    def test_tool_callable(self):
        tools = build_tools(data_source="phantom_seed1")
        # Just verify it's callable
        self.assertTrue(callable(tools["search"]))


@unittest.skipUnless(_HAS_PHANTOM_DATA, _PHANTOM_SKIP_REASON)
class BuildAnswerEvaluatorTest(unittest.TestCase):
    def test_returns_callable(self):
        evaluator = build_answer_evaluator(0, data_source="phantom_seed1")
        self.assertTrue(callable(evaluator))

    def test_returns_float(self):
        evaluator = build_answer_evaluator(0, data_source="phantom_seed1")
        score = evaluator("nonexistent person xyz")
        self.assertIsInstance(score, float)
        self.assertEqual(score, 0.0)

    def test_correct_answer_scores_positive(self):
        qa = _load_qa(1)
        gold = qa[0]["answer"]
        evaluator = build_answer_evaluator(0, data_source="phantom_seed1")
        # Provide one correct answer
        score = evaluator(gold[0])
        self.assertGreater(score, 0.0)


@unittest.skipUnless(_HAS_PHANTOM_DATA, _PHANTOM_SKIP_REASON)
class BuildFakePlanTest(unittest.TestCase):
    def test_returns_list(self):
        plan = build_fake_plan(3, row_index=0, data_source="phantom_seed1")
        self.assertIsInstance(plan, list)
        self.assertEqual(len(plan), 1)
        tool_name, payload = plan[0]
        self.assertEqual(tool_name, "search")
        data = json.loads(payload)
        self.assertIn("query", data)


# ---------------------------------------------------------------------------
# Integration test with FakeLLM
# ---------------------------------------------------------------------------

@unittest.skipUnless(_HAS_PHANTOM_DATA, _PHANTOM_SKIP_REASON)
class FakeLLMIntegrationTest(unittest.TestCase):
    def test_react_loop_completes(self):
        from expgym.react_loop import FakeLLM, run_react_loop

        tools = build_tools(data_source="phantom_seed1")
        plan = build_fake_plan(2, row_index=0, data_source="phantom_seed1")

        qa = _load_qa(1)
        # Use first gold answer as the fake answer
        fake_answer = qa[0]["answer"][0]
        llm = FakeLLM(plan=plan, final_answer=fake_answer)

        context = build_context(False, row_index=0, data_source="phantom_seed1")
        evaluator = build_answer_evaluator(0, data_source="phantom_seed1")
        result = run_react_loop(
            llm=llm,
            tools=tools,
            max_steps=5,
            context=context,
            answer_evaluator=evaluator,
        )
        self.assertIsNotNone(result["answer"])
        # The fake answer should match at least one gold answer
        self.assertGreater(result["answer_perf"], 0.0)


if __name__ == "__main__":
    unittest.main()
