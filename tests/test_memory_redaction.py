"""Synthetic credential regressions for both sides of the H-MEM bridge."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import memory_bridge


ROOT = Path(__file__).resolve().parents[1]
METERLESS = ROOT / "meterless"
# These are inert, deliberately fake markers. No account credentials are used.


def _synthetic_slack_webhook_token() -> str:
    """Alphabet segment for the synthetic Slack webhook fixtures."""
    return 'abcdefghijklmnopqrstuvwx'


def _synthetic_slack_webhook(with_scheme: bool) -> str:
    """Join an inert Slack incoming-webhook fixture when the test runs.

    A contiguous URL literal in this file matches GitHub secret scanning.
    The team id, channel id, and alphabet segment stay separate until then.
    """
    url = ''.join((
        'hooks',
        '.slack.com',
        '/services/',
        'T01234567',
        '/',
        'B01234567',
        '/',
        _synthetic_slack_webhook_token(),
    ))
    if with_scheme:
        return 'https://' + url
    return url


CASES = (
    ('Authorization: Bearer SYNTHETIC_BEARER_CANARY', 'SYNTHETIC_BEARER_CANARY'),
    ('authorization: Basic SYNTHETIC_BASIC_CANARY', 'SYNTHETIC_BASIC_CANARY'),
    ('{"api_key":"SYNTHETIC_JSON_CANARY"}', 'SYNTHETIC_JSON_CANARY'),
    ("{'password': 'SYNTHETIC_QUOTED_CANARY with spaces'}", 'with spaces'),
    ('token="SYNTHETIC_ESCAPED_CANARY \\"quoted\\" tail"', 'tail'),
    ('{"client_secret": "SYNTHETIC_CLIENT_CANARY"}', 'SYNTHETIC_CLIENT_CANARY'),
    ('access_token=SYNTHETIC_ACCESS_CANARY', 'SYNTHETIC_ACCESS_CANARY'),
    ('refresh_token=SYNTHETIC_REFRESH_CANARY', 'SYNTHETIC_REFRESH_CANARY'),
    ('{"api_key":"SYNTHETIC_TRUNCATED_CANARY', 'SYNTHETIC_TRUNCATED_CANARY'),
    ('Bearer SYNTHETIC_STANDALONE_CANARY', 'SYNTHETIC_STANDALONE_CANARY'),
    ('ghp_SYNTHETIC_GITHUB_CANARY', 'SYNTHETIC_GITHUB_CANARY'),
    ('gho_SYNTHETIC_GITHUB_OAUTH_CANARY', 'SYNTHETIC_GITHUB_OAUTH_CANARY'),
    ('ghu_SYNTHETIC_GITHUB_USER_CANARY', 'SYNTHETIC_GITHUB_USER_CANARY'),
    ('ghs_SYNTHETIC_GITHUB_SERVER_CANARY', 'SYNTHETIC_GITHUB_SERVER_CANARY'),
    ('ghr_SYNTHETIC_GITHUB_REFRESH_CANARY', 'SYNTHETIC_GITHUB_REFRESH_CANARY'),
    ('token=SYNTHETIC_LEGACY_CANARY', 'SYNTHETIC_LEGACY_CANARY'),
    ('password=SYNTHETIC_PREFIX}SYNTHETIC_BRACE_SUFFIX', 'SYNTHETIC_BRACE_SUFFIX'),
    ('password=SYNTHETIC_PREFIX]SYNTHETIC_BRACKET_SUFFIX', 'SYNTHETIC_BRACKET_SUFFIX'),
    ("password=SYNTHETIC_PREFIX'SYNTHETIC_QUOTE_SUFFIX", 'SYNTHETIC_QUOTE_SUFFIX'),
    ('password="SYNTHETIC_TRAILING_SLASH\\', 'SYNTHETIC_TRAILING_SLASH'),
    ('Bearer "SYNTHETIC_BEARER_PREFIX QUOTED_SUFFIX"', 'QUOTED_SUFFIX'),
    ('Authorization: Bearer "SYNTHETIC_AUTH_PREFIX AUTH_SUFFIX"', 'AUTH_SUFFIX'),
    ('Authorization: Basic "SYNTHETIC_BASIC_PREFIX BASIC_SUFFIX"', 'BASIC_SUFFIX'),
    ('password="SYNTHETIC_ESCAPED_LINE\\\nSYNTHETIC_LINE_REMAINDER"', 'SYNTHETIC_LINE_REMAINDER'),
    ('password="SYNTHETIC_PREFIX"SYNTHETIC_CONCAT_SUFFIX', 'SYNTHETIC_CONCAT_SUFFIX'),
    ("password='SYNTHETIC_PREFIX'SYNTHETIC_SINGLE_SUFFIX", 'SYNTHETIC_SINGLE_SUFFIX'),
    ('AKIAIOSFODNN7EXAMPLE', 'AKIAIOSFODNN7EXAMPLE'),
    ('AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE', 'AKIAIOSFODNN7EXAMPLE'),
    ('AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'),
    ('npm_abcdefghijklmnopqrstuvwxyz0123456789abcd', 'npm_abcdefghijklmnopqrstuvwxyz0123456789abcd'),
    ('hf_abcdefghijklmnopqrstuvwxyz012345', 'hf_abcdefghijklmnopqrstuvwxyz012345'),
    ('glpat-abcdefghijklmnopqrstuv', 'glpat-abcdefghijklmnopqrstuv'),
    ('sk-abcdefghijklmnopqrstuvwxyz0123456789', 'sk-abcdefghijklmnopqrstuvwxyz0123456789'),
    ('xoxb-SYNTHETIC_SLACK_BOT_CANARY', 'xoxb-SYNTHETIC_SLACK_BOT_CANARY'),
    ('xoxe-SYNTHETIC_SLACK_EXCHANGE_CANARY', 'xoxe-SYNTHETIC_SLACK_EXCHANGE_CANARY'),
    ('xoxc-SYNTHETIC_SLACK_CONFIG_CANARY', 'xoxc-SYNTHETIC_SLACK_CONFIG_CANARY'),
    ('gsk_abcdefghijklmnopqrstuvwxyzABCDEF0123456789', 'gsk_abcdefghijklmnopqrstuvwxyzABCDEF0123456789'),
    ('xai-abcdefghijklmnopqrstuvwxyz0123456789', 'xai-abcdefghijklmnopqrstuvwxyz0123456789'),
    ('sk_live_SYNTHETIC_STRIPE_LIVE_CANARY', 'sk_live_SYNTHETIC_STRIPE_LIVE_CANARY'),
    ('dop_v1_SYNTHETIC_DIGITALOCEAN_CANARY', 'dop_v1_SYNTHETIC_DIGITALOCEAN_CANARY'),
    ('pypi-SYNTHETIC_PYPI_CANARY', 'pypi-SYNTHETIC_PYPI_CANARY'),
    ('sntrys_SYNTHETIC_SENTRY_CANARY', 'sntrys_SYNTHETIC_SENTRY_CANARY'),
    ('whsec_SYNTHETIC_STRIPE_WEBHOOK_CANARY', 'whsec_SYNTHETIC_STRIPE_WEBHOOK_CANARY'),
    ('rk_live_SYNTHETIC_STRIPE_RESTRICTED_CANARY', 'rk_live_SYNTHETIC_STRIPE_RESTRICTED_CANARY'),
    ('xoxs-SYNTHETIC_SLACK_SESSION_CANARY', 'xoxs-SYNTHETIC_SLACK_SESSION_CANARY'),
    ('xapp-SYNTHETIC_SLACK_APP_CANARY', 'xapp-SYNTHETIC_SLACK_APP_CANARY'),
    (_synthetic_slack_webhook(True), _synthetic_slack_webhook_token()),
    (_synthetic_slack_webhook(False), _synthetic_slack_webhook_token()),
    ('password=\'SYNTHETIC_PREFIX\'"SYNTHETIC_MIXED suffix"', 'suffix'),
)


class MemoryRedactionTests(unittest.TestCase):
    def test_python_redacts_common_credential_forms(self) -> None:
        for text, marker in CASES:
            with self.subTest(text=text):
                redacted = memory_bridge._redact(text)
                self.assertNotIn(marker, redacted)
                self.assertIn('[redacted]', redacted)

    def test_slack_webhook_fixtures_are_complete_urls(self) -> None:
        token = _synthetic_slack_webhook_token()
        urls = [text for text, marker in CASES if marker == token]
        self.assertEqual(
            urls,
            [_synthetic_slack_webhook(True), _synthetic_slack_webhook(False)],
        )
        host = 'hooks' + '.slack.com'
        service = '/'.join(('services', 'T01234567', 'B01234567', token))
        self.assertEqual(urls[0], 'https://' + host + '/' + service)
        self.assertEqual(urls[1], host + '/' + service)
        for index, url in enumerate(urls):
            with self.subTest(index=index):
                redacted = memory_bridge._redact(url)
                self.assertNotIn(token, redacted)
                self.assertNotIn(host, redacted)
                self.assertIn('[redacted]', redacted)

    def test_redacts_before_truncation_and_preserves_nonsecret_context(self) -> None:
        value = 'CI failed: password="SYNTHETIC_START sensitive tail"; inspect checkout'
        self.assertEqual(memory_bridge._redact(value), 'CI failed: [redacted]; inspect checkout')
        self.assertEqual(memory_bridge._redact(value, 20), 'CI failed: [redacted')
        for value in ('token counts differ', 'password validation failed', 'api key missing', 'npm ci failed'):
            with self.subTest(value=value):
                self.assertEqual(memory_bridge._redact(value), value)

    def test_python_remember_redacts_every_payload_field(self) -> None:
        text = '{"api_key":"SYNTHETIC_PAYLOAD_CANARY"}'
        with patch('memory_bridge._invoke', return_value={'ok': True}) as invoke:
            memory_bridge.remember({
                'failing_step': text, 'root_cause': text,
                'patterns': [text], 'fixture': text,
            })
        payload = invoke.call_args.args[1]
        self.assertNotIn('SYNTHETIC_PAYLOAD_CANARY', json.dumps(payload))
        self.assertTrue(payload['provenance']['fixture'])

    def test_python_ask_redacts_query(self) -> None:
        with patch('memory_bridge._invoke', return_value={'ok': True}) as invoke:
            memory_bridge.ask('Authorization: Bearer SYNTHETIC_QUERY_CANARY')
        self.assertNotIn('SYNTHETIC_QUERY_CANARY', json.dumps(invoke.call_args.args[1]))

    def test_python_error_response_redacts_stderr(self) -> None:
        completed = subprocess.CompletedProcess([], 1, '', '{"password":"SYNTHETIC_ERROR_CANARY"}')
        with patch('memory_bridge.status', return_value={'ready': True}), patch(
            'memory_bridge.subprocess.run', return_value=completed,
        ):
            result = memory_bridge._invoke('ask')
        self.assertNotIn('SYNTHETIC_ERROR_CANARY', json.dumps(result))
        self.assertFalse(result['ok'])


@unittest.skipUnless(
    shutil.which('node')
    and (METERLESS / 'node_modules' / 'tsx').is_dir()
    and (METERLESS / 'vendor' / 'hmem' / 'src' / 'index.ts').is_file(),
    'real H-MEM integration needs Node, npm ci, and npm run setup',
)
class HmemPersistenceRedactionTests(unittest.TestCase):
    def run_cli(self, command: str, payload: dict, state: str) -> dict:
        # Invoke the installed tsx loader without its optional CLI IPC server.
        environment = {
            'PATH': os.environ.get('PATH', ''),
            'NURSE_HMEM_DIR': state,
            'NO_COLOR': '1',
        }
        completed = subprocess.run(
            ['node', '--import', 'tsx', 'nurse-memory.ts', command, '--json'],
            cwd=METERLESS, input=json.dumps(payload), capture_output=True,
            text=True, timeout=20, check=False, env=environment,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result['ok'])
        self.assertEqual(result['engine_source'], 'vendor/hmem')
        return result

    def test_cli_redacts_before_memory_and_ledger_persistence(self) -> None:
        for text, marker in CASES:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as state:
                # Content and source labels are both durable H-MEM fields.
                result = self.run_cli('remember', {
                    'content': f'Always review CI diagnosis {text}',
                    'fixture': text,
                }, state)
                self.assertTrue(result['stored'])
                self.assertNotIn(marker, json.dumps(result))
                for filename in ('state.json', 'ledger.jsonl'):
                    stored = Path(state, filename).read_text(encoding='utf-8')
                    self.assertIn('[redacted]', stored)
                    self.assertNotIn(marker, stored)

    def test_cli_redacts_structured_diagnosis_and_query(self) -> None:
        with tempfile.TemporaryDirectory() as state:
            result = self.run_cli('remember', {
                'failing_step': 'Checkout',
                'root_cause': 'Always review {"api_key":"SYNTHETIC_CAUSE_CANARY"}',
                'patterns': ['token="SYNTHETIC_PATTERN_CANARY with spaces"'],
            }, state)
            self.assertNotIn('SYNTHETIC_CAUSE_CANARY', json.dumps(result))
            self.assertNotIn('SYNTHETIC_PATTERN_CANARY', json.dumps(result))
            for filename in ('state.json', 'ledger.jsonl'):
                stored = Path(state, filename).read_text(encoding='utf-8')
                self.assertNotIn('SYNTHETIC_CAUSE_CANARY', stored)
                self.assertNotIn('SYNTHETIC_PATTERN_CANARY', stored)
            recall = self.run_cli('ask', {'query': '{"api_key":"SYNTHETIC_ASK_CANARY"}'}, state)
            self.assertNotIn('SYNTHETIC_ASK_CANARY', json.dumps(recall))

    def test_cli_redacts_credentials_in_store_parse_errors(self) -> None:
        malformed = (
            ('ghp_FAKE', 'ghp_FAKE'),
            ('{"password": FAKE12345}', 'FAKE12345'),
            ('{"client_secret": FAKE12345}', 'FAKE12345'),
            ('{"access_token": FAKE12345}', 'FAKE12345'),
        )
        for filename in ('state.json', 'ledger.jsonl'):
            for raw, marker in malformed:
                with self.subTest(filename=filename, raw=raw), tempfile.TemporaryDirectory() as state:
                    # Short inert markers remain visible even when JSON.parse
                    # abbreviates the key/context in its error message.
                    Path(state, filename).write_text(raw, encoding='utf-8')
                    completed = subprocess.run(
                        ['node', '--import', 'tsx', 'nurse-memory.ts', 'ask', '--json'],
                        cwd=METERLESS, input='{"query":"checkout"}', capture_output=True,
                        text=True, timeout=20, check=False,
                        env={'PATH': os.environ.get('PATH', ''), 'NURSE_HMEM_DIR': state, 'NO_COLOR': '1'},
                    )
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn('H-MEM bridge error:', completed.stderr)
                    self.assertNotIn(marker, completed.stderr + completed.stdout)
                    # Feed the actual CLI result through the Python boundary
                    # without launching a second npm process.
                    with patch('memory_bridge.status', return_value={'ready': True}), patch(
                        'memory_bridge.subprocess.run', return_value=completed,
                    ):
                        result = memory_bridge._invoke('ask')
                    self.assertFalse(result['ok'])
                    self.assertNotIn(marker, json.dumps(result))


if __name__ == '__main__':
    unittest.main()
