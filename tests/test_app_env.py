import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nurse


class AppEnvTests(unittest.TestCase):
    def write(self, root: Path, name: str, text: str) -> None:
        (root / name).write_text(text, encoding="utf-8")

    def test_env_local_is_read_and_wins_over_env(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            self.write(root, ".env", "GEMINI_API_KEY=from-env\nNURSE_ONLY_IN_ENV=1\n")
            self.write(root, ".env.local", "GEMINI_API_KEY=from-env-local\n")
            nurse.load_app_env(root)
            self.assertEqual(os.environ["GEMINI_API_KEY"], "from-env-local")
            self.assertEqual(os.environ["NURSE_ONLY_IN_ENV"], "1")

    def test_process_env_and_zetaris_keys_are_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"GEMINI_API_KEY": "from-shell"}, clear=True
        ):
            root = Path(tmp)
            self.write(root, ".env.local", "GEMINI_API_KEY=from-file\nZETARIS_REST_URL=https://x/api/v1.0\n")
            nurse.load_app_env(root)
            self.assertEqual(os.environ["GEMINI_API_KEY"], "from-shell")
            self.assertNotIn("ZETARIS_REST_URL", os.environ)


if __name__ == "__main__":
    unittest.main()
