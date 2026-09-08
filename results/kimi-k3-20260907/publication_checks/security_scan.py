#!/usr/bin/env python3
"""Read-only publication credential review; never emit matched values."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import tarfile
from datetime import datetime, timezone


ROOTS = [
    'reports', 'runs', 'dumps', 'provenance', 'protocol', 'patches',
    'harness', 'logs', 'serving/runs', 'serving/reports', 'serving/logs',
    'serving/manifests', 'serving/patches', 'data_runtime/validation_v2',
    'data_runtime/validation_v3', 'data_runtime/logs',
    'serving/accounting', 'serving/independent/logs',
    'serving/independent/manifests', 'data_runtime/diagnostic_adult',
    'data_runtime/fake_expgym_paramnet', 'data_runtime/fake_hpo_validation',
    'data_runtime/fake_poolact_paramnet', 'data_runtime/hpobench_config',
]
TOP_LEVEL_ROOTS = ['serving', 'data_runtime', 'serving/independent']
KNOWN_PLACEHOLDERS = {
    '', 'none', 'null', 'dummy', 'empty', 'unused', 'fake', 'test',
    'test-key', 'dummy-key', 'fake-key', 'placeholder', 'local-no-auth',
    'local', 'your_api_key', 'your-api-key', 'your_api_key_here',
    'sk-test', 'sk-placeholder', 'secret', 'test-secret', 'redacted',
    'not-required', 'noauth', 'no-auth',
    'expgym_local_noauth_placeholder_20260907',
}
STRONG_PATTERNS = {
    'private_key_pem_header': re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    'github_classic_token': re.compile(r'(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9]{30,255}'),
    'github_fine_grained_token': re.compile(r'github_pat_[A-Za-z0-9_]{50,255}'),
    'aws_access_key_id': re.compile(r'(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])'),
    'slack_token': re.compile(r'xox[baprs]-[A-Za-z0-9-]{20,255}'),
    'google_api_key': re.compile(r'AIza[0-9A-Za-z_-]{35}'),
    'huggingface_token': re.compile(r'(?<![A-Za-z0-9_])hf_[A-Za-z0-9]{30,100}'),
    'openai_style_token': re.compile(r'(?<![A-Za-z0-9_-])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,255}'),
    'jwt_three_segments': re.compile(r'(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{16,}'),
}
LITERAL_PATTERNS = {
    'credential_literal_assignment': re.compile(
        r'''(?i)["']?(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|client[_-]?secret|secret[_-]?key|aws[_-]?secret[_-]?access[_-]?key)["']?\s*[:=]\s*["']([^"'\r\n]{1,1024})["']'''),
    'authorization_literal': re.compile(
        r'''(?i)["']?(?:authorization|proxy-authorization|x-api-key)["']?\s*[:=]\s*(?:f)?["']([^"'\r\n]{1,1024})["']'''),
    'url_query_credential': re.compile(
        r'''(?i)[?&](?:access_token|auth_token|api_key|apikey|token|key|client_secret)=([^&\s"'<>\\]{1,1024})'''),
    'url_userinfo_password': re.compile(
        r'''(?i)https?://[^\s/:@"'<>]+:([^\s/@"'<>]{1,1024})@'''),
    'shell_credential_assignment': re.compile(
        r'''(?m)^\s*(?:export\s+)?[A-Z0-9_]*(?:API_KEY|ACCESS_TOKEN|AUTH_TOKEN|CLIENT_SECRET|SECRET_KEY|PASSWORD|PASSWD)\s*=\s*([^\s#;]{1,1024})'''),
    'unquoted_http_authorization': re.compile(
        r'''(?i)\b(?:Authorization|Proxy-Authorization)\s*:\s*(?:Bearer|Basic)\s+([A-Za-z0-9+/=._-]{8,1024})'''),
}
SECURITY_FIELD = re.compile(
    r'(?i)^(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|client[_-]?secret|secret[_-]?key|authorization|proxy-authorization|x-api-key|aws[_-]?secret[_-]?access[_-]?key)$')

# Manual review is bound to the complete immutable file, not merely its name.
# Every candidate in these exact source files is a unittest/mock fixture.
# The patch candidates were additionally compared in memory with the same
# fixture literal values; no values are emitted by the scan or this allowlist.
REVIEWED_TEST_FIXTURE_FILES = {
    '99060cc02f43c9ef4020a8f3d97904962495cfca1bb9fc0afea3acc889e1f396': 'Client provenance unittest: deliberately non-operational API-key sentinel.',
    '03c90cec062e234755530cb01a7def0ec186802f0642a4011ebe06b4785bbbd4': 'Mocked client unittests: single-character/provider placeholders and deliberate redaction sentinels in API-key, userinfo, and URL-query test cases.',
    '5525cc9740fa637f5e43a739df5d2882d0bcd2ef58efcd7c6fdac9b4cfd3c587': 'Backend environment selection unittest: synthetic provider-specific key placeholders.',
    '9b065f4a61ec776581a0e42a42c44f68a4373a949772c9293d5ce2f1a9ed9c5f': 'Source patch containing the same reviewed mocked-client/redaction fixture literals; all candidates matched the unittest fixture values in memory.',
    'cd99c8276020e6774c7a5a49ba9eec5b7e064aea06f95c55f3fb819284955d5d': 'Source patch containing the same reviewed mocked-client/redaction fixture literals; all candidates matched the unittest fixture values in memory.',
    '81fcadb0c90a1a9ffc0da0cf52cf15537e7f1e8807372a065e4a8d9a27cf1d78': 'Source patch containing the same reviewed mocked-client/redaction fixture literals; all candidates matched the unittest fixture values in memory.',
    '2df601d32f665d4bb81bad9bf7360114b761a888ede8e3c601330da58a457e60': 'Source patch containing the same reviewed mocked-client/redaction fixture literals; all candidates matched the unittest fixture values in memory.',
}


def relevant_rule(rule, lower):
    gates = {
        'private_key_pem_header': ('private key-----',),
        'github_classic_token': ('ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_'),
        'github_fine_grained_token': ('github_pat_',),
        'aws_access_key_id': ('akia', 'asia'),
        'slack_token': ('xox',), 'google_api_key': ('aiza',),
        'huggingface_token': ('hf_',), 'openai_style_token': ('sk-',),
        'jwt_three_segments': ('eyj',),
        'credential_literal_assignment': ('api_key', 'api-key', 'apikey', 'token', 'password', 'passwd', 'secret'),
        'authorization_literal': ('authorization', 'x-api-key'),
        'url_query_credential': ('?', '&'),
        'url_userinfo_password': ('@',),
        'shell_credential_assignment': ('api_key', 'access_token', 'auth_token', 'client_secret', 'secret_key', 'password', 'passwd'),
        'unquoted_http_authorization': ('authorization',),
    }
    return any(marker in lower for marker in gates[rule])


def classification(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    low = value.lower()
    if low.startswith(('bearer ', 'basic ')):
        value = value.split(None, 1)[1].strip()
        low = value.lower()
    if low in KNOWN_PLACEHOLDERS:
        return 'known_placeholder'
    if (re.fullmatch(r'\$?\{[A-Za-z_][A-Za-z0-9_., ()\[\]"\'/-]*\}', value)
            or re.fullmatch(r'\$[A-Za-z_][A-Za-z0-9_]*', value)
            or value.startswith(('os.environ', 'getenv(', 'self.', 'args.', 'config.'))):
        return 'source_expression_or_template'
    if low in ('api_key', 'apikey', 'token', 'access_token', 'password', 'api key'):
        return 'source_name_or_placeholder'
    if low.startswith(('your-', 'your_', '<your', '<redacted', '[redacted')):
        return 'source_name_or_placeholder'
    return 'needs_review'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--all-files', action='store_true',
                        help='Scan all regular files below --base instead of the fixed source-workspace allowlist.')
    args = parser.parse_args()
    base = Path(args.base).resolve()
    output = Path(args.output).resolve()
    if output.exists():
        raise SystemExit('Refusing to overwrite an existing security report')
    hits = []
    suppressed = collections.Counter()
    counts = collections.Counter()
    scopes = {}
    errors = []
    inventory = []

    def scan_text(label, raw, sha):
        if b'\0' in raw[:8192]:
            counts['binary_items_skipped'] += 1
            return
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            text = raw.decode('utf-8', errors='replace')
            counts['replacement_decoded_items'] += 1
        counts['text_items_scanned'] += 1
        counts['text_bytes_scanned'] += len(raw)
        local = collections.Counter()
        lower = text.lower()
        for rule, pattern in STRONG_PATTERNS.items():
            if relevant_rule(rule, lower):
                local[rule] += sum(1 for _ in pattern.finditer(text))
        for rule, pattern in LITERAL_PATTERNS.items():
            if not relevant_rule(rule, lower):
                continue
            for match in pattern.finditer(text):
                status = classification(match.group(1))
                if status == 'needs_review':
                    local[rule] += 1
                else:
                    suppressed[rule + ':' + status] += 1
        if label.endswith('.json') and any(x in lower for x in ('api_key', 'api-key', 'apikey', 'token', 'password', 'passwd', 'secret', 'authorization')):
            try:
                parsed = json.loads(text)
            except (ValueError, RecursionError):
                counts['json_parse_failures'] += 1
            else:
                stack = [parsed]
                while stack:
                    item = stack.pop()
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if SECURITY_FIELD.match(key) and isinstance(value, str):
                                status = classification(value)
                                if status == 'needs_review':
                                    local['json_credential_field_literal'] += 1
                                else:
                                    suppressed['json_credential_field_literal:' + status] += 1
                            if isinstance(value, (dict, list)):
                                stack.append(value)
                    elif isinstance(item, list):
                        stack.extend(v for v in item if isinstance(v, (dict, list)))
        for rule, count in sorted(local.items()):
            if count:
                review = REVIEWED_TEST_FIXTURE_FILES.get(sha)
                hits.append({'path': label, 'rule': rule, 'count': count, 'file_sha256': sha,
                             'review_status': 'reviewed_non_secret_test_fixture' if review else 'needs_review',
                             'review_reason': review})

    def scan_file(path, scope):
        if path.resolve() == output:
            counts['own_output_files_skipped'] += 1
            return
        label = path.relative_to(base).as_posix()
        try:
            raw = path.read_bytes()
        except OSError:
            errors.append({'path': label, 'error_type': 'read_error'})
            return
        sha = hashlib.sha256(raw).hexdigest()
        inventory.append((label, len(raw), sha))
        counts['files_scanned'] += 1
        counts['file_bytes'] += len(raw)
        scopes.setdefault(scope, {'files': 0, 'bytes': 0})
        scopes[scope]['files'] += 1
        scopes[scope]['bytes'] += len(raw)
        if label.endswith(('.tar.gz', '.tgz', '.tar')):
            counts['archives_scanned'] += 1
            try:
                with tarfile.open(path, 'r:*') as archive:
                    for member in archive:
                        if not member.isfile():
                            continue
                        member_label = label + '::' + member.name
                        if member.size > 64 * 1024 * 1024:
                            errors.append({'path': member_label, 'error_type': 'archive_member_too_large'})
                            continue
                        handle = archive.extractfile(member)
                        member_raw = handle.read()
                        counts['archive_members_scanned'] += 1
                        member_sha = hashlib.sha256(member_raw).hexdigest()
                        inventory.append((member_label, len(member_raw), member_sha))
                        scan_text(member_label, member_raw, member_sha)
            except (OSError, tarfile.TarError):
                errors.append({'path': label, 'error_type': 'archive_error'})
        elif path.suffix == '.pyc':
            counts['bytecode_files_skipped'] += 1
        else:
            scan_text(label, raw, sha)

    for scope in (['.'] if args.all_files else ROOTS):
        root = base / scope
        if not root.is_dir():
            errors.append({'path': scope, 'error_type': 'missing_scope'})
            continue
        stack = [root]
        while stack:
            for entry in os.scandir(stack.pop()):
                if entry.is_symlink():
                    counts['symlinks_skipped'] += 1
                elif entry.is_dir(follow_symlinks=False):
                    if entry.name not in ('__pycache__', '.git'):
                        stack.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    scan_file(Path(entry.path), scope)
        print(json.dumps({'completed_scope': scope, 'files_scanned': counts['files_scanned']}), flush=True)
    for top in ([] if args.all_files else TOP_LEVEL_ROOTS):
        for entry in os.scandir(base / top):
            if entry.is_file(follow_symlinks=False):
                if entry.stat().st_size > 64 * 1024 * 1024:
                    errors.append({'path': top + '/' + entry.name, 'error_type': 'top_level_file_too_large'})
                else:
                    scan_file(Path(entry.path), top + '/[top-level files]')

    inventory_bytes = ''.join('%s\t%d\t%s\n' % row for row in sorted(inventory)).encode()
    report = {
        'schema_version': 2,
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'review_type': 'read_only_publication_credential_scan',
        'scanner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope_roots': ['.'] if args.all_files else ROOTS,
        'top_level_only_roots': [] if args.all_files else TOP_LEVEL_ROOTS,
        'all_files_mode': args.all_files,
        'scope_totals': scopes,
        'counts': dict(counts),
        'inventory_sha256': hashlib.sha256(inventory_bytes).hexdigest(),
        'candidate_count': sum(hit['count'] for hit in hits),
        'candidate_file_count': len({hit['path'] for hit in hits}),
        'reviewed_non_secret_candidate_count': sum(hit['count'] for hit in hits if hit['review_status'] != 'needs_review'),
        'unreviewed_candidate_count': sum(hit['count'] for hit in hits if hit['review_status'] == 'needs_review'),
        'candidates': sorted(hits, key=lambda x: (x['path'], x['rule'])),
        'suppressed_counts_by_rule_and_reason': dict(sorted(suppressed.items())),
        'errors': errors,
        'complete': not errors,
        'no_unreviewed_candidates': not any(hit['review_status'] == 'needs_review' for hit in hits),
        'limitations': [
            'Heuristic credential scan; absence of candidates is not a mathematical guarantee of absence of secrets.',
            'Matched values are never emitted or saved; candidates contain only paths, rule names, counts, and full-file SHA256.',
            'No external network operations; no archive extraction or original-file edits.',
            'Fixed-scope mode excludes checkpoints, virtual environments, caches, wheels, image_source, and external dataset trees; all-files mode scans the explicitly supplied publication bundle.',
            'Known placeholders and source interpolation expressions are counted separately from candidates.',
            'Absolute local paths and historical internal service endpoints are provenance metadata, not automatically treated as credentials.',
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    report_display = str(output.relative_to(base)) if output.is_relative_to(base) else str(output)
    print(json.dumps({'report': report_display, 'complete': report['complete'],
                      'files_scanned': counts['files_scanned'], 'archive_members_scanned': counts['archive_members_scanned'],
                      'candidate_count': report['candidate_count'], 'candidate_file_count': report['candidate_file_count'],
                      'unreviewed_candidate_count': report['unreviewed_candidate_count'],
                      'errors_count': len(errors)}))


if __name__ == '__main__':
    main()
