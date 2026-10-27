"""Regression contracts for the clearly bounded historic-CI case study."""
from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/mangeshraut712/actions-nurse"
FAILED_SHA = "8616b672c2b8ed186c8cb8a1f7e6d61f13eedb28"
FOLLOW_UP_SHA = "0d46c28706f5cfe0183c1c0f0db872ecf062224d"


class _Anchors(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: dict[str, str] = {}
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.anchors[self._href] = " ".join("".join(self._text).split())
            self._href = None
            self._text = []


class WebHistoricCiCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.page = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.case_study = (ROOT / "docs" / "historic-ci-case-study.md").read_text(encoding="utf-8")
        self.docs_map = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.case = json.loads(
            (ROOT / "demo" / "real-ci" / "historic-docker-smoke-incident.json").read_text(encoding="utf-8")
        )

    def test_static_case_card_is_separate_from_dynamic_zetaris_evidence(self) -> None:
        marker = 'id="historicCiCase"'
        self.assertIn(marker, self.page)
        historic_start = self.page.index(marker)
        historic_end = self.page.index("</section>", historic_start)
        card = self.page[historic_start:historic_end]

        result_start = self.page.index('id="result"')
        result_end = self.page.index("</section>", result_start)
        self.assertNotIn(marker, self.page[result_start:result_end])
        self.assertNotIn('id="zetarisEvidence"', card)
        self.assertNotIn('id="zetarisEvidenceDetails"', card)
        self.assertIn("Historic repository CI case", card)
        self.assertIn("not a live query", card.lower())
        self.assertIn("not a synthetic fixture", card.lower())
        self.assertIn("not production evidence", card.lower())
        self.assertIn("not a successful autonomous repair", card.lower())
        self.assertIn("unknown", card.lower())
        self.assertIn("unrecognized", card.lower())
        self.assertIn("does not establish the root cause", card.lower())

        expected_urls = [
            f"{REPOSITORY}/commit/{FAILED_SHA}",
            f"{REPOSITORY}/actions/runs/40328653045",
            f"{REPOSITORY}/actions/runs/40328653045/job/121591898621",
            f"{REPOSITORY}/actions/runs/40328858092",
            f"{REPOSITORY}/commit/{FOLLOW_UP_SHA}",
            f"{REPOSITORY}/actions/runs/40331404876",
        ]
        for url in expected_urls:
            self.assertIn(f'href="{url}"', card)

    def test_card_link_labels_stay_matched_to_the_canonical_timeline(self) -> None:
        parser = _Anchors()
        parser.feed(self.page)
        anchors = parser.anchors
        failed = self.case["failed_ci"]
        triage = self.case["actions_nurse_triage"]
        follow_up = self.case["documented_follow_up"]
        subsequent = self.case["subsequent_ci"]

        self.assertEqual(f"Run {failed['run_id']}", anchors[failed["run_url"]])
        self.assertEqual(f"job {failed['job_id']}", anchors[failed["job_url"]])
        self.assertEqual(f"commit {failed['display_sha']}", anchors[failed["commit_url"]])
        self.assertEqual(f"Same-commit triage run {triage['run_id']}", anchors[triage["run_url"]])
        self.assertEqual(f"Follow-up commit {follow_up['display_sha']}", anchors[follow_up["commit_url"]])
        self.assertEqual(f"subsequent green run {subsequent['run_id']}", anchors[subsequent["run_url"]])

    def test_case_study_and_navigation_preserve_the_evidence_boundary(self) -> None:
        normalized_case_study = " ".join(self.case_study.lower().split())
        self.assertIn("../demo/real-ci/historic-docker-smoke-incident.json", self.case_study)
        self.assertIn("not a live query", normalized_case_study)
        self.assertIn("not synthetic zetaris data", normalized_case_study)
        self.assertIn("not production evidence", normalized_case_study)
        self.assertIn("does not establish", normalized_case_study)
        self.assertIn("unknown", normalized_case_study)
        self.assertIn("unrecognized", normalized_case_study)
        self.assertIn("historic-ci-case-study.md", self.docs_map)
        self.assertIn("docs/historic-ci-case-study.md", self.readme)

        for url in (
            f"{REPOSITORY}/commit/{FAILED_SHA}",
            f"{REPOSITORY}/actions/runs/40328653045",
            f"{REPOSITORY}/actions/runs/40328653045/job/121591898621",
            f"{REPOSITORY}/actions/runs/40328858092",
            f"{REPOSITORY}/commit/{FOLLOW_UP_SHA}",
            f"{REPOSITORY}/actions/runs/40331404876",
        ):
            self.assertIn(url, self.case_study)

        expected_markdown_links = (
            (f"CI run {self.case['failed_ci']['run_id']}", self.case["failed_ci"]["run_url"]),
            (f"commit {self.case['failed_ci']['display_sha']}", self.case["failed_ci"]["commit_url"]),
            (f"job {self.case['failed_ci']['job_id']}", self.case["failed_ci"]["job_url"]),
            (f"Actions Nurse triage run {self.case['actions_nurse_triage']['run_id']}", self.case["actions_nurse_triage"]["run_url"]),
            (f"Follow-up commit {self.case['documented_follow_up']['display_sha']}", self.case["documented_follow_up"]["commit_url"]),
            (f"subsequent CI run {self.case['subsequent_ci']['run_id']}", self.case["subsequent_ci"]["run_url"]),
        )
        for label, url in expected_markdown_links:
            self.assertIn(f"[{label.lower()}]({url})", normalized_case_study)

        unsafe_claims = (
            "autonomously repaired",
            "proved root cause",
            "production incident",
            "time saved",
            "improved accuracy",
        )
        combined = self.case_study.lower()
        for claim in unsafe_claims:
            self.assertNotIn(claim, combined)


if __name__ == "__main__":
    unittest.main()
