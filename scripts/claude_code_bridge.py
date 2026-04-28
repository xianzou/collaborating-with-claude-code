import importlib.util
import unittest
from pathlib import Path
from unittest import mock


BRIDGE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "claude_code_bridge.py"


def load_bridge_module():
    spec = importlib.util.spec_from_file_location("claude_code_bridge", BRIDGE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BuildClaudeCmdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = load_bridge_module()

    def test_stream_json_forces_verbose_for_claude_print_mode(self):
        cmd = self.bridge._build_claude_cmd(
            claude_bin="claude",
            prompt="test prompt",
            output_format="stream-json",
            model="claude-opus-4-6",
            permission_mode="plan",
            tools="Read",
            allowed_tools="Read",
            session_id="",
            continue_session=False,
            claude_settings={},
            max_turns=None,
            verbose=False,
        )

        self.assertIn("--verbose", cmd)

    def test_json_output_keeps_verbose_optional(self):
        cmd = self.bridge._build_claude_cmd(
            claude_bin="claude",
            prompt="test prompt",
            output_format="json",
            model="claude-opus-4-6",
            permission_mode="plan",
            tools="Read",
            allowed_tools="Read",
            session_id="",
            continue_session=False,
            claude_settings={},
            max_turns=None,
            verbose=False,
        )

        self.assertNotIn("--verbose", cmd)

    def test_windows_popen_kwargs_hide_console_window(self):
        startupinfo = type("StartupInfo", (), {"dwFlags": 0, "wShowWindow": 1})()

        with (
            mock.patch.object(self.bridge.os, "name", "nt"),
            mock.patch.object(self.bridge.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200),
            mock.patch.object(self.bridge.subprocess, "CREATE_NO_WINDOW", 0x8000000),
            mock.patch.object(self.bridge.subprocess, "STARTF_USESHOWWINDOW", 0x1),
            mock.patch.object(self.bridge.subprocess, "SW_HIDE", 0),
            mock.patch.object(self.bridge.subprocess, "STARTUPINFO", return_value=startupinfo),
        ):
            kwargs = self.bridge._build_popen_kwargs()

        self.assertEqual(kwargs["creationflags"], 0x200 | 0x8000000)
        self.assertIs(kwargs["startupinfo"], startupinfo)
        self.assertEqual(startupinfo.dwFlags, 0x1)
        self.assertEqual(startupinfo.wShowWindow, 0)

    def test_extract_exact_text_from_standalone_line(self):
        extracted = self.bridge._extract_exact_text(
            "WINDOW_PATCH_OK\n\nExtra explanation below.",
            "WINDOW_PATCH_OK",
        )

        self.assertEqual(extracted, "WINDOW_PATCH_OK")

    def test_extract_exact_text_from_backticked_line(self):
        extracted = self.bridge._extract_exact_text(
            "I already returned `WINDOW_PATCH_OK`.\n`WINDOW_PATCH_OK`\nMore context.",
            "WINDOW_PATCH_OK",
        )

        self.assertEqual(extracted, "WINDOW_PATCH_OK")

    def test_extract_exact_text_returns_none_when_missing(self):
        extracted = self.bridge._extract_exact_text(
            "The result was WINDOW_PATCH_OK with more trailing text on the same line.",
            "WINDOW_PATCH_OK",
        )

        self.assertIsNone(extracted)


if __name__ == "__main__":
    unittest.main()
