"""Regression contracts for safe Zetaris evidence rendering in the web UI."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WebZetarisEvidenceTests(unittest.TestCase):
    def test_default_triage_call_to_action_is_mode_neutral(self) -> None:
        page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="triage" class="primary">Triage CI failure</button>', page)
        self.assertNotIn('id="triage" class="primary">Triage with Gemma 4</button>', page)
        self.assertNotIn("Press “Triage with Gemma 4”", script)
        self.assertNotIn("then triage with Gemma 4", script)
        self.assertIn("if (health.rules_only)", script)
        self.assertIn("Rules-only mode is active. No Gemma request is made", script)

    def test_result_panel_reserves_a_structured_zetaris_evidence_area(self) -> None:
        page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

        self.assertIn('id="zetarisEvidence"', page)
        self.assertIn('id="zetarisEvidenceDetails"', page)

    def test_renderer_uses_safe_dom_nodes_for_rows_and_sql(self) -> None:
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("function renderZetarisEvidence", script)
        start = script.index("function renderZetarisEvidence")
        renderer = script[start:script.index("function renderResult", start)]
        self.assertIn("document.createElement('details')", renderer)
        self.assertIn("textContent", renderer)
        self.assertIn("request_id", renderer)
        self.assertIn("synthetic-local-demo", renderer)
        self.assertNotIn("innerHTML", renderer)

    def test_frontend_script_has_valid_javascript_syntax(self) -> None:
        result = subprocess.run(
            ["node", "--check", "web/app.js"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_renderer_only_displays_rows_matching_the_diagnosed_step(self) -> None:
        probe = r'''
const fs = require('fs');
class Node {
  constructor(tag) { this.tag = tag; this.children = []; this.textContent = ''; this.className = ''; }
  replaceChildren(...items) { this.children = items; }
  append(...items) { this.children.push(...items); }
  appendChild(item) { this.children.push(item); }
}
const elements = { zetarisEvidence: new Node('span'), zetarisEvidenceDetails: new Node('div') };
global.document = {
  getElementById: (id) => elements[id],
  createElement: (tag) => new Node(tag),
  addEventListener: () => {},
};
eval(fs.readFileSync('web/app.js', 'utf8'));
renderZetarisEvidence({
  mode: 'live', source: 'zetaris-local-session', provenance: 'synthetic-local-demo', failing_step: 'Typecheck / tsc',
  result: {
    row_count: 2, request_id: 'request-123', sql: 'SELECT 1',
    data: [
      { failing_step: 'Typecheck / tsc', failure_signature: '<img src=x>', latest_recommendation: 'Use a safe fix', source: 'synthetic local demo' },
      { failing_step: 'Unrelated', failure_signature: 'do not show', latest_recommendation: 'do not show', source: 'unrelated' },
    ],
  },
});
const list = elements.zetarisEvidenceDetails.children.find((node) => node.tag === 'ol');
if (!list || list.children.length !== 1) process.exit(2);
if (!elements.zetarisEvidence.textContent.includes('live local read-only query')) process.exit(3);
if (!elements.zetarisEvidence.textContent.includes('synthetic local demo rows')) process.exit(4);
if (list.children[0].children[0].textContent !== '<img src=x>') process.exit(5);
'''
        result = subprocess.run(
            ["node", "-e", probe],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_renderer_redacts_bearer_and_jwt_like_values_from_evidence_copy(self) -> None:
        probe = r'''
const fs = require('fs');
global.document = { addEventListener: () => {} };
eval(fs.readFileSync('web/app.js', 'utf8'));
const bearer = evidenceText('Authorization: Bearer secret-value');
const jwt = evidenceText('eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJsb2NhbCJ9.signaturepart');
const marker = 'ghp_FAKEONLYabcdefghijklmnopqrstuvwx123456';
const quoted = evidenceText('{"token":"' + marker + '"}');
const bare = evidenceText('copy ' + marker + ' into CI');
if (bearer.includes('secret-value') || jwt.includes('eyJhbGciOiJIUzI1NiJ9') || quoted.includes(marker) || bare.includes(marker)) process.exit(2);
'''
        result = subprocess.run(
            ["node", "-e", probe],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fixture_label_stays_explicitly_synthetic_reference_data(self) -> None:
        probe = r'''
const fs = require('fs');
class Node { constructor(tag) { this.tag = tag; this.children = []; this.textContent = ''; } replaceChildren(...items) { this.children = items; } append(...items) { this.children.push(...items); } appendChild(item) { this.children.push(item); } }
const elements = { zetarisEvidence: new Node('span'), zetarisEvidenceDetails: new Node('div') };
global.document = { getElementById: (id) => elements[id], createElement: (tag) => new Node(tag), addEventListener: () => {} };
eval(fs.readFileSync('web/app.js', 'utf8'));
renderZetarisEvidence({ mode: 'fixture', provenance: 'unclassified', result: { row_count: 1, fixture: 'ci-failure-signatures.json', data: [] } });
if (!elements.zetarisEvidence.textContent.includes('recorded reference fixture')) process.exit(2);
if (!elements.zetarisEvidence.textContent.includes('synthetic reference data')) process.exit(3);
'''
        result = subprocess.run(
            ["node", "-e", probe],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unavailable_state_is_not_labeled_as_fixture_evidence(self) -> None:
        probe = r'''
const fs = require('fs');
class Node { constructor(tag) { this.tag = tag; this.children = []; this.textContent = ''; } replaceChildren(...items) { this.children = items; } append(...items) { this.children.push(...items); } appendChild(item) { this.children.push(item); } }
const elements = { zetarisEvidence: new Node('span'), zetarisEvidenceDetails: new Node('div') };
global.document = { getElementById: (id) => elements[id], createElement: (tag) => new Node(tag), addEventListener: () => {} };
eval(fs.readFileSync('web/app.js', 'utf8'));
renderZetarisEvidence({ mode: 'unavailable', result: { row_count: 0, data: [] } });
if (!elements.zetarisEvidence.textContent.includes('unavailable')) process.exit(2);
if (elements.zetarisEvidence.textContent.includes('recorded reference fixture')) process.exit(3);
'''
        result = subprocess.run(
            ["node", "-e", probe],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
