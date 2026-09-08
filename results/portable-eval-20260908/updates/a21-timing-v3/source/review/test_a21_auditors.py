"""Pure CPU tests for the new independent A21 audit helpers; never runs an LLM."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("a21_raw_test_subject", HERE / "audit_a21_attempts_v3.py")
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class OrderedHistory(unittest.TestCase):
    def setUp(self):
        self.base = [{"role": "system", "content": "native"}, {"role": "user", "content": "Action: is literal data"}]
        self.assistants = [{"role": "assistant", "content": None, "reasoning_content": str(index),
                            "tool_calls": [{"id": "opaque:" + str(index), "function": {"name": "tool", "arguments": "{}"}}]}
                           for index in range(2)]
        self.tools = [{"role": "tool", "tool_call_id": "opaque:" + str(index), "content": "feedback " + str(index)} for index in range(2)]
        self.previous = self.base + [self.assistants[0], self.tools[0], self.assistants[1]]
        self.messages = self.previous + [self.tools[1], {"role": "user", "content": "final"}]

    def check(self, messages):
        return subject.ordered_native_history(messages, self.assistants, self.previous)

    def test_legal_chain(self):
        self.assertTrue(self.check(self.messages))

    def test_deleted_complete_pair_rejected(self):
        self.assertFalse(self.check(self.messages[:2] + self.messages[4:]))

    def test_reordered_complete_pairs_rejected(self):
        self.assertFalse(self.check(self.messages[:2] + self.messages[4:6] + self.messages[2:4] + self.messages[6:]))

    def test_duplicated_complete_pair_rejected(self):
        self.assertFalse(self.check(self.messages[:4] + self.messages[2:4] + self.messages[4:]))

    def test_changed_old_feedback_rejected(self):
        messages = copy.deepcopy(self.messages)
        messages[3]["content"] = "mutated"
        self.assertFalse(self.check(messages))

    def test_orphan_tool_id_rejected(self):
        messages = copy.deepcopy(self.messages)
        messages[5]["tool_call_id"] = "other"
        self.assertFalse(self.check(messages))

    def test_pending_call_before_user_rejected(self):
        self.assertFalse(self.check(self.previous + [{"role": "user", "content": "skip tool result"}]))

    def test_natural_early_answer_needs_no_forced_call(self):
        self.assertTrue(subject.ordered_native_history(self.base, [], []))

    def test_duplicate_json_and_nonfinite_rejected(self):
        for text in ('{"key":1,"key":2}', '{"key":NaN}', '{"key":Infinity}'):
            with self.assertRaises(ValueError):
                subject.strict_json(text)

    def test_no_final_execution_rejected_before_model_or_inputs(self):
        with self.assertRaises(ValueError):
            subject.audit(HERE / "does_not_exist", HERE / "no_authorization")


class DumpInventory(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="a21-dump-inventory-test-")
        self.addCleanup(temporary.cleanup)
        self.parent = Path(temporary.name)
        self.run = self.parent / "run"
        self.flat = self.run / "dumps" / "job" / "request.json"
        self.flat.parent.mkdir(parents=True)
        self.flat.write_text("{}")

    def test_complete_flat_inventory_accepted(self):
        self.assertEqual(subject.strict_dump_inventory(self.run), [self.flat])

    def test_root_orphan_json_rejected(self):
        (self.run / "dumps" / "orphan.json").write_text("{}")
        with self.assertRaises(ValueError):
            subject.strict_dump_inventory(self.run)

    def test_deeper_json_rejected(self):
        nested = self.flat.parent / "nested"
        nested.mkdir()
        (nested / "orphan.json").write_text("{}")
        with self.assertRaises(ValueError):
            subject.strict_dump_inventory(self.run)

    def test_symlink_ancestor_rejected(self):
        alias = self.parent / "run-alias"
        alias.symlink_to(self.run, target_is_directory=True)
        with self.assertRaises(ValueError):
            subject.strict_dump_inventory(alias)

    def test_symlink_descendant_even_nonjson_rejected(self):
        (self.flat.parent / "alias.txt").symlink_to(self.flat)
        with self.assertRaises(ValueError):
            subject.strict_dump_inventory(self.run)

    def test_symlink_job_directory_rejected(self):
        (self.run / "dumps" / "alias-job").symlink_to(self.flat.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            subject.strict_dump_inventory(self.run)

    def test_main_audit_rejects_alias_before_any_evidence_read(self):
        spec = importlib.util.spec_from_file_location("a21_main_entry_test_subject", HERE / "audit_a21_v3.py")
        main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main)
        alias = self.parent / "run-alias"
        alias.symlink_to(self.run, target_is_directory=True)
        with mock.patch.object(main, "read", side_effect=AssertionError("Evidence read before lexical path check")) as reader:
            with self.assertRaises(ValueError):
                main.audit(alias, self.parent / "not_read_auth.json", self.parent / "not_read_raw.json")
            reader.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
