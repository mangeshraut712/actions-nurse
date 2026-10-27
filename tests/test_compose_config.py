"""Regression checks for runtime configuration exposed by Docker Compose."""
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ComposeConfigurationTests(unittest.TestCase):
    def test_compose_passes_only_zetaris_values_selected_from_env_file(self) -> None:
        lines = set((ROOT / "docker-compose.yml").read_text(encoding="utf-8").splitlines())
        expected = {
            "      ZETARIS_REST_URL: ${ZETARIS_REST_URL:-}",
            "      ZETARIS_ORG_ID: ${ZETARIS_ORG_ID:-}",
            "      ZETARIS_API_KEY: ${ZETARIS_API_KEY:-}",
        }
        self.assertTrue(expected <= lines)
        self.assertNotIn("    env_file:", lines)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docker compose --env-file .env.local up --build", readme)


if __name__ == "__main__":
    unittest.main()
