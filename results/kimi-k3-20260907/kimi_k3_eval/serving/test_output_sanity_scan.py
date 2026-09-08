"""Offline fixture tests; no temporary files, service requests, or GPU imports."""

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import output_sanity_scan as scan


MARKERS = [
    {"text": "[PAD]", "token_id": 163839, "role": "sequence_padding", "special": True},
    {"text": "<|media_pad|>", "token_id": 163605, "role": "media_placeholder", "special": True},
]


class OutputSanityTests(unittest.TestCase):
    def run_fixture(self, message, *, duplicate=False, complete=True, allow_incomplete=False):
        manifest = {"progress_path": "/fixture/progress.json", "source_tree_sha256": "test-source",
                    "stage": "test", "run_namespace": "fixture", "jobs": [{"id": "case", "dump_dir": "/fixture/dumps"}]}
        progress = {"all_selected_jobs_complete": complete, "finished_at": "finished" if complete else None}
        dump = {"request_id": "request-1", "attempt": 1, "generation_id": "generation-1", "state": "success",
                "context": {"fixture": True}, "request_payload": {"messages": [{"content": "[PAD][PAD]<|media_pad|>"}]},
                "response_json": {"id": "response-1", "choices": [{"index": 0, "finish_reason": "stop", "message": message}]}}

        def read(path):
            if path.name == "manifest.json":
                return manifest, "manifest-hash"
            if path.name == "progress.json":
                return progress, "progress-hash"
            return dump, "dump-hash"

        argv = ["scan", "--manifest", "/fixture/a/manifest.json"]
        if duplicate:
            argv.extend(["--manifest", "/fixture/b/manifest.json"])
        if allow_incomplete:
            argv.append("--allow-incomplete")
        stdout = io.StringIO()
        with patch.object(sys, "argv", argv), patch.object(scan, "read_json", read), \
             patch.object(scan, "load_padding_tokens", return_value=(MARKERS, {})), \
             patch.object(Path, "glob", return_value=[Path("/fixture/dumps/request-1.json")]), \
             contextlib.redirect_stdout(stdout):
            scan.main()
        return json.loads(stdout.getvalue())

    def test_real_checkpoint_padding_identity(self):
        markers, evidence = scan.load_padding_tokens(scan.DEFAULT_CKPT)
        self.assertCountEqual(markers, MARKERS)
        self.assertEqual(evidence["pad_token"], "[PAD]")
        self.assertEqual(evidence["pad_token_id"], 163839)

    def test_request_history_not_counted(self):
        result = self.run_fixture({"content": "Action: valid", "reasoning_content": ""})
        self.assertEqual(result["counts"]["choices_with_padding_marker"], 0)
        self.assertEqual(result["counts"]["response_choices"], 1)
        self.assertEqual(result["findings"], [])

    def test_fields_and_marker_roles_counted_separately(self):
        result = self.run_fixture({"content": "[PAD] x [PAD]", "reasoning_content": "<|media_pad|>[PAD]"})
        counts = result["counts"]
        self.assertEqual(counts["choices_with_padding_marker"], 1)
        self.assertEqual(counts["sequence_padding_choices"], 1)
        self.assertEqual(counts["media_placeholder_choices"], 1)
        self.assertEqual(counts["sequence_padding_content_occurrences"], 2)
        self.assertEqual(counts["sequence_padding_reasoning_content_occurrences"], 1)
        self.assertEqual(counts["media_placeholder_reasoning_content_occurrences"], 1)
        self.assertEqual(result["findings"][0]["context"], {"fixture": True})
        self.assertEqual(result["findings"][0]["dump_sha256"], "dump-hash")

    def test_empty_tool_only_content_is_recorded(self):
        result = self.run_fixture({"content": None, "tool_calls": [{"id": "t1"}]})
        self.assertEqual(result["counts"]["empty_content"], 1)
        self.assertEqual(result["findings"][0]["tool_call_count"], 1)

    def test_whitespace_content_is_empty(self):
        result = self.run_fixture({"content": " \n\t", "reasoning_content": "reason"})
        self.assertEqual(result["counts"]["empty_content"], 1)

    def test_promoted_duplicate_is_counted_once(self):
        result = self.run_fixture({"content": "[PAD]"}, duplicate=True)
        self.assertEqual(result["counts"]["response_choices"], 1)
        self.assertEqual(result["counts"]["sequence_padding_content_occurrences"], 1)
        self.assertEqual(len(result["duplicates_skipped"]), 1)

    def test_unfinished_snapshot_requires_explicit_flag(self):
        with self.assertRaises(SystemExit):
            self.run_fixture({"content": "ok"}, complete=False)
        result = self.run_fixture({"content": "ok"}, complete=False, allow_incomplete=True)
        self.assertFalse(result["manifests"][0]["complete_at_snapshot"])

    def test_unknown_content_type_is_not_silently_empty(self):
        result = self.run_fixture({"content": {"unexpected": "[PAD]"}})
        self.assertEqual(result["counts"]["unsupported_field_types"], 1)
        self.assertEqual(result["counts"]["empty_content"], 0)
        self.assertEqual(len(result["findings"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
