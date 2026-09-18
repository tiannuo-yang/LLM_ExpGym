#!/usr/bin/env python3
"""Static/fake Docker endpoint checks; never starts Docker or touches repo data."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DockerEndpointRewriteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="expgym-docker-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        scripts = self.root / "scripts"
        scripts.mkdir()
        self.wrapper = scripts / "run_hpobench_docker.sh"
        shutil.copyfile(ROOT / "scripts" / self.wrapper.name, self.wrapper)
        self.docker = self.root / "docker-stub"
        # This module doubles as an executable fake Docker below; no separate
        # generated shell source, real daemon, model request, or network access.
        shutil.copyfile(Path(__file__).resolve(), self.docker)
        self.docker.chmod(0o755)
        self.log = self.root / "docker-calls.jsonl"

    def run_wrapper(self, args, env=None):
        # Deliberately do not inherit credentials, .env, or backend overrides
        # from the developer's environment.
        process_env = {
            "PATH": os.pathsep.join((str(Path(sys.executable).parent), os.defpath)),
            "DOCKER": str(self.docker),
            "EXPGYM_DOCKER_STUB_LOG": str(self.log),
        }
        process_env.update(env or {})
        result = subprocess.run(
            ["bash", str(self.wrapper), "--no-build"] + args,
            cwd=str(self.root),
            env=process_env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual([call[0] for call in calls], ["info", "run"])
        command = calls[-1]
        docker_env = {}
        for index, argument in enumerate(command[:-1]):
            if argument == "-e":
                name, _, value = command[index + 1].partition("=")
                docker_env[name] = value
        runner_start = command.index("python") + 1
        return command[runner_start:], docker_env

    def test_sampling_arguments_are_preserved_for_both_runners(self):
        for poolact in (False, True):
            for flags in (["--top-p", "0.95", "--top-k", "-1"],
                          ["--top-p=0.95", "--top-k=40"]):
                with self.subTest(poolact=poolact, flags=flags):
                    self.log.unlink(missing_ok=True)
                    args = (["--poolact"] if poolact else []) + ["--backend=fake"] + flags
                    runner, _ = self.run_wrapper(args)
                    self.assertEqual(runner[-len(flags):], flags)

    def test_cli_rewrites_hostname_only_in_both_forms_and_both_runners(self):
        urls = (
            ("http://localhost:8000/v1", "http://host.docker.internal:8000/v1"),
            ("https://127.0.0.1/v1?next=localhost#127.0.0.1",
             "https://host.docker.internal/v1?next=localhost#127.0.0.1"),
            ("HTTP://LOCALHOST:80/localhost/127.0.0.1?x=localhost&y=127.0.0.1",
             "HTTP://host.docker.internal:80/localhost/127.0.0.1?x=localhost&y=127.0.0.1"),
            ("http://localhost:unit-test-placeholder@127.0.0.1:3000/v1",
             "http://localhost:unit-test-placeholder@host.docker.internal:3000/v1"),
        )
        for poolact in (False, True):
            for equals in (False, True):
                for original, expected in urls:
                    with self.subTest(poolact=poolact, equals=equals, url=original):
                        self.log.unlink(missing_ok=True)
                        args = ["--poolact"] if poolact else []
                        args += ["--backend=fake", "--output-dir", "runs/localhost"]
                        args += (["--base-url=" + original] if equals else
                                 ["--base-url", original])
                        runner, env = self.run_wrapper(args)
                        self.assertEqual(runner[0], "scripts/run_poolact.py" if poolact
                                         else "scripts/run_paper_sweep.py")
                        self.assertEqual(runner[-1], "--base-url=" + expected if equals
                                         else expected)
                        self.assertIn("runs/localhost", runner)
                        self.assertFalse(any(name.endswith("BASE_URL") for name in env))

    def test_remote_hosts_and_non_authority_text_remain_unchanged(self):
        for original in (
            "https://localhost.example/v1?proxy=127.0.0.1",
            "https://127.0.0.1.example/v1/localhost",
            "https://example.test/localhost/127.0.0.1?host=localhost",
            "https://localhost:unit-test-placeholder@example.test/v1",
            "http://[::1]:8000/v1",
            "localhost:8000/v1",
        ):
            with self.subTest(url=original):
                self.log.unlink(missing_ok=True)
                runner, _ = self.run_wrapper(["--backend=fake", "--base-url", original])
                self.assertEqual(runner[-1], original)

    def test_backend_environment_url_is_rewritten_and_isolated(self):
        all_urls = {
            "SUB2API_BASE_URL": "http://localhost:3100/localhost?x=127.0.0.1",
            "OPENAI_BASE_URL": "http://127.0.0.1:3200/v1?x=localhost",
            "OPENROUTER_BASE_URL": "http://localhost:3300/v1",
        }
        for backend in ("sub2api", "openai", "openrouter"):
            with self.subTest(backend=backend):
                self.log.unlink(missing_ok=True)
                supplied = dict(all_urls)
                supplied.update({name + "_API_KEY": "unit-test-placeholder"
                                 for name in ("SUB2API", "OPENAI", "OPENROUTER")})
                _, env = self.run_wrapper(["--backend=" + backend], supplied)
                name = backend.upper() + "_BASE_URL"
                expected = {
                    "sub2api": "http://host.docker.internal:3100/localhost?x=127.0.0.1",
                    "openai": "http://host.docker.internal:3200/v1?x=localhost",
                    "openrouter": "http://host.docker.internal:3300/v1",
                }[backend]
                self.assertEqual({k: v for k, v in env.items() if k.endswith("BASE_URL")},
                                 {name: expected})
                self.assertEqual([k for k in env if k.endswith("API_KEY")],
                                 [backend.upper() + "_API_KEY"])

    def test_generic_url_overrides_backend_environment(self):
        _, env = self.run_wrapper(["--backend", "openai"], {
            "OPENAI_API_KEY": "unit-test-placeholder",
            "EXPGYM_BASE_URL": "http://localhost:4000/custom?keep=localhost",
            "OPENAI_BASE_URL": "http://localhost:5000/wrong",
            "SUB2API_BASE_URL": "http://localhost:6000/unrelated",
        })
        self.assertEqual({k: v for k, v in env.items() if k.endswith("BASE_URL")}, {
            "EXPGYM_BASE_URL": "http://host.docker.internal:4000/custom?keep=localhost",
        })

    def test_cli_url_overrides_all_environment_urls(self):
        runner, env = self.run_wrapper([
            "--backend=openai", "--base-url", "http://localhost:4000/first",
            "--base-url=http://127.0.0.1:5000/last",
        ], {
            "OPENAI_API_KEY": "unit-test-placeholder",
            "EXPGYM_BASE_URL": "http://localhost:6000/ignored",
            "OPENAI_BASE_URL": "http://localhost:7000/ignored",
            "SUB2API_BASE_URL": "http://localhost:8000/unrelated",
        })
        self.assertEqual(runner[-3:], [
            "--base-url", "http://host.docker.internal:4000/first",
            "--base-url=http://host.docker.internal:5000/last",
        ])
        self.assertFalse(any(name.endswith("BASE_URL") for name in env))

    def test_last_backend_cli_wins_and_only_matching_auth_is_required(self):
        for poolact in (False, True):
            with self.subTest(poolact=poolact):
                self.log.unlink(missing_ok=True)
                args = ["--poolact"] if poolact else []
                args += ["--backend", "sub2api", "--backend=openai", "--backend", "fake"]
                _, env = self.run_wrapper(args, {
                    "EXPGYM_BACKEND": "openrouter",
                    "OPENAI_BASE_URL": "http://localhost:1000/not-selected",
                })
                self.assertEqual(env["EXPGYM_BACKEND"], "fake")
                self.assertFalse(any(name.endswith(("BASE_URL", "API_KEY")) for name in env))

    def test_environment_backend_is_forwarded_to_sequential_runner(self):
        _, env = self.run_wrapper(["--models", "test-model"], {
            "EXPGYM_BACKEND": "openai",
            "OPENAI_API_KEY": "unit-test-placeholder",
            "OPENAI_BASE_URL": "http://localhost:4000/v1",
        })
        self.assertEqual(env["EXPGYM_BACKEND"], "openai")
        self.assertEqual(env["OPENAI_BASE_URL"], "http://host.docker.internal:4000/v1")


if __name__ == "__main__":
    if os.environ.get("EXPGYM_DOCKER_STUB_LOG"):
        with open(os.environ["EXPGYM_DOCKER_STUB_LOG"], "a", encoding="utf-8") as stream:
            stream.write(json.dumps(sys.argv[1:]) + "\n")
    else:
        unittest.main()
