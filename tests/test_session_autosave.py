import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "session_autosave.py"


class SessionAutosaveTests(unittest.TestCase):
    def run_hook(self, root, payload, transcript=None):
        env = os.environ.copy()
        env["HOME"] = str(root / "home")
        env["USERPROFILE"] = str(root / "home")
        env["CLAUDE_MEMORY_ROOT"] = str(root / "memory")
        (root / "home").mkdir(exist_ok=True)
        if transcript is not None:
            transcript_path = root / "transcript.jsonl"
            transcript_path.write_text("\n".join(json.dumps(row) for row in transcript), encoding="utf-8")
            payload["transcript_path"] = str(transcript_path)
        result = subprocess.run(
            [sys.executable, "-I", str(SCRIPT)],
            input=json.dumps(payload), text=True, capture_output=True, env=env, check=False,
        )
        return result, list((root / "memory").rglob("*.md")) if (root / "memory").exists() else []

    def valid_transcript(self):
        return [
            {"timestamp": "2026-10-28T10:00:00Z", "message": {"role": "user", "content": "Implement feature"}},
            {"timestamp": "2026-10-28T10:01:00Z", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "src/app.py"}},
                {"type": "tool_use", "name": "Bash", "input": {"command": "pytest -q"}},
                {"type": "tool_result", "content": "PRIVATE_TOOL_OUTPUT"},
            ]}},
            {"timestamp": "2026-10-28T10:02:00Z", "message": {"role": "user", "content": "Also add tests"}},
        ]

    def test_writes_minimal_session_note_without_tool_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result, notes = self.run_hook(root, {"cwd": str(root / "sample project"), "session_id": "abc", "reason": "exit"}, self.valid_transcript())
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(notes), 1)
            content = notes[0].read_text(encoding="utf-8")
            self.assertIn("Implement feature", content)
            self.assertIn("src/app.py", content)
            self.assertIn("pytest -q", content)
            self.assertNotIn("PRIVATE_TOOL_OUTPUT", content)
            self.assertIn("abc", content)
            self.assertIn("exit", content)

    def test_redacts_secret_values_from_prompt_and_commands(self):
        transcript = self.valid_transcript()
        transcript[0]["message"]["content"] = "Use token ghp_abcdefghijklmnopqrstuvwxyz123456 and password=supersecret"
        transcript[1]["message"]["content"][0]["input"]["file_path"] = "config/token=ghp_abcdefghijklmnopqrstuvwxyz123456.json"
        transcript[1]["message"]["content"][1]["input"]["command"] = "curl -H 'Authorization: Bearer secret-token' https://example.invalid"
        with tempfile.TemporaryDirectory() as tmp:
            result, notes = self.run_hook(Path(tmp), {"cwd": tmp}, transcript)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = notes[0].read_text(encoding="utf-8")
            self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz123456", content)
            self.assertNotIn("supersecret", content)
            self.assertNotIn("secret-token", content)
            self.assertIn("[REDACTED]", content)

    def test_truncates_overly_long_commands(self):
        transcript = self.valid_transcript()
        long_cmd = "echo " + ("a" * 1000)
        transcript[1]["message"]["content"][1]["input"]["command"] = long_cmd
        with tempfile.TemporaryDirectory() as tmp:
            result, notes = self.run_hook(Path(tmp), {"cwd": tmp}, transcript)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = notes[0].read_text(encoding="utf-8")
            self.assertNotIn("a" * 1000, content)
            self.assertIn(" …", content)

    def test_limits_file_paths_and_commands(self):
        rows = [{"message": {"role": "user", "content": "start"}}]
        for i in range(25):
            rows.append({"message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": f"file-{i}.txt"}},
                {"type": "tool_use", "name": "Bash", "input": {"command": f"cmd-{i}"}},
            ]}})
        rows.append({"message": {"role": "user", "content": "finish"}})
        with tempfile.TemporaryDirectory() as tmp:
            result, notes = self.run_hook(Path(tmp), {"cwd": tmp}, rows)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = notes[0].read_text(encoding="utf-8")
            self.assertEqual(sum(f"file-{i}.txt" in content for i in range(25)), 20)
            self.assertEqual(sum(f"cmd-{i}" in content for i in range(25)), 10)

    def test_skips_missing_or_malformed_transcript_and_short_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result, notes = self.run_hook(root, {"cwd": tmp, "transcript_path": str(root / "missing.jsonl")})
            self.assertEqual(result.returncode, 0)
            self.assertEqual(notes, [])
            result, notes = self.run_hook(root, {"cwd": tmp}, [
                {"message": {"role": "user", "content": "only one prompt"}},
                {"message": {"role": "assistant", "content": "done"}},
            ])
            self.assertEqual(result.returncode, 0)
            self.assertEqual(notes, [])

    def test_project_directory_is_safe_and_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside"
            outside.mkdir()
            project = root / ".." / "outside"
            result, notes = self.run_hook(root, {"cwd": str(project)}, self.valid_transcript())
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(notes), 1)
            self.assertTrue(notes[0].resolve().is_relative_to((root / "memory").resolve()))

    def test_saves_directly_in_project_docs_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "my-ai-project"
            docs_dir = project_dir / "project-docs"
            docs_dir.mkdir(parents=True)
            env = os.environ.copy()
            # Clear CLAUDE_MEMORY_ROOT to test in-project resolution
            env.pop("CLAUDE_MEMORY_ROOT", None)
            transcript_path = project_dir / "transcript.jsonl"
            transcript_path.write_text("\n".join(json.dumps(row) for row in self.valid_transcript()), encoding="utf-8")
            payload = {"cwd": str(project_dir), "session_id": "test1234", "reason": "exit", "transcript_path": str(transcript_path)}
            result = subprocess.run([sys.executable, "-I", str(SCRIPT)], input=json.dumps(payload), text=True, capture_output=True, env=env, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            saved_notes = list((docs_dir / "sessions").glob("*.md"))
            self.assertEqual(len(saved_notes), 1)
            self.assertIn("Implement feature", saved_notes[0].read_text(encoding="utf-8"))

    def test_saves_in_dot_claude_sessions_for_regular_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "regular-repo"
            project_dir.mkdir(parents=True)
            env = os.environ.copy()
            env.pop("CLAUDE_MEMORY_ROOT", None)
            transcript_path = project_dir / "transcript.jsonl"
            transcript_path.write_text("\n".join(json.dumps(row) for row in self.valid_transcript()), encoding="utf-8")
            payload = {"cwd": str(project_dir), "session_id": "reg5678", "reason": "exit", "transcript_path": str(transcript_path)}
            result = subprocess.run([sys.executable, "-I", str(SCRIPT)], input=json.dumps(payload), text=True, capture_output=True, env=env, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            saved_notes = list((project_dir / ".claude" / "sessions").glob("*.md"))
            self.assertEqual(len(saved_notes), 1)
            self.assertIn("Implement feature", saved_notes[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
