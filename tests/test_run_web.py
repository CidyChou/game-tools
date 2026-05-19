from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

import run_web


class RunWebTests(TestCase):
    def test_ensure_dependencies_installs_when_multipart_is_missing(self) -> None:
        imported: list[str] = []

        def import_module(name: str) -> object:
            imported.append(name)
            if name == "multipart" and imported.count("multipart") == 1:
                raise ModuleNotFoundError("No module named 'multipart'", name="multipart")
            return object()

        with patch.object(run_web.importlib, "import_module", side_effect=import_module):
            with patch.object(run_web, "run_setup_command") as run_setup_command:
                run_web.ensure_dependencies()

        run_setup_command.assert_called_once()
        self.assertIn("uvicorn", imported)
        self.assertEqual(imported.count("multipart"), 2)


if __name__ == "__main__":
    unittest.main()
