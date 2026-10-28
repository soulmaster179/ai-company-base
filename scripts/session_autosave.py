"""
Claude Code SessionEnd hook — minimal session note writer.

Reads hook JSON from stdin (transcript_path, cwd, session_id, reason).
Writes a filtered Markdown note to $CLAUDE_MEMORY_ROOT/<project-id>/sessions/.
Falls back to ~/.claude/ai-company-base-memory when CLAUDE_MEMORY_ROOT is not set.
Uses only Python standard library. Failures are logged to stderr; exit 0 always.
"""
import hashlib
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ── Safety limits ──────────────────────────────────────────────────────────────
MAX_FILES = 20
MAX_CMDS = 10
MAX_PROMPT_CHARS = 400
MAX_COMMAND_CHARS = 400

# ── Secret-pattern redaction ───────────────────────────────────────────────────
_SECRET_PATTERNS = re.compile(
    r"""(?xi)
    (
        (?:password|passwd|secret|token|apikey|api_key|auth|credential)[=:\s\"']+\S+
        | ghp_[A-Za-z0-9]{36,}
        | xox[bpoa]-[A-Za-z0-9-]+
        | AKIA[0-9A-Z]{16}
        | Bearer\s+\S{8,}
        | (?:Authorization:\s*)\S+\s+\S+
    )
    """,
    re.IGNORECASE,
)


def redact(text: str) -> str:
    return _SECRET_PATTERNS.sub("[REDACTED]", text)


def safe_project_id(cwd: str) -> str:
    normalized = Path(os.path.normpath(cwd)).resolve()
    slug = re.sub(r"[^A-Za-z0-9._-]", "_", normalized.name or "root")[:40]
    digest = hashlib.sha1(str(normalized).encode()).hexdigest()[:8]
    return f"{slug}_{digest}"


def extract_entries(transcript_path: str):
    path = Path(transcript_path)
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries


def parse_transcript(entries):
    user_prompts = []
    file_paths = []
    commands = []
    for entry in entries:
        msg = entry.get("message") or entry
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            if isinstance(content, str) and content.strip():
                user_prompts.append(content.strip())
        elif role == "assistant":
            items = content if isinstance(content, list) else []
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "tool_use":
                    continue
                name = item.get("name", "")
                inp = item.get("input") or {}
                if name in ("Edit", "Write", "NotebookEdit"):
                    fp = inp.get("file_path") or inp.get("path", "")
                    if fp:
                        file_paths.append(str(fp))
                elif name == "Bash":
                    cmd = inp.get("command", "")
                    if cmd:
                        commands.append(cmd)
    return user_prompts, file_paths, commands


def build_note(session_id, reason, cwd, user_prompts, file_paths, commands):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# Session {session_id}",
        f"",
        f"**Timestamp:** {ts}",
        f"**Session ID:** `{session_id}`",
        f"**End reason:** {reason}",
        f"**Working directory:** `{cwd}`",
        f"",
    ]
    first_prompt = user_prompts[0] if user_prompts else ""
    if first_prompt:
        snippet = redact(first_prompt[:MAX_PROMPT_CHARS])
        if len(first_prompt) > MAX_PROMPT_CHARS:
            snippet += " …"
        lines += ["## Opening prompt", "", snippet, ""]
    kept_files = list(dict.fromkeys(file_paths))[:MAX_FILES]
    if kept_files:
        lines += ["## Files touched", ""]
        for fp in kept_files:
            lines.append(f"- `{redact(fp)}`")
        lines.append("")
    kept_cmds = list(dict.fromkeys(commands))[:MAX_CMDS]
    if kept_cmds:
        lines += ["## Commands run", ""]
        for cmd in kept_cmds:
            safe_cmd = redact(cmd)
            if len(safe_cmd) > MAX_COMMAND_CHARS:
                safe_cmd = safe_cmd[:MAX_COMMAND_CHARS] + " …"
            lines.append(f"- `{safe_cmd}`")
        lines.append("")
    return "\n".join(lines)


def get_session_dir(cwd_str: str) -> Path:
    memory_root_env = os.environ.get("CLAUDE_MEMORY_ROOT")
    if memory_root_env:
        project_id = safe_project_id(cwd_str)
        target = Path(memory_root_env) / "sessions" / project_id
        target.mkdir(parents=True, exist_ok=True)
        return target

    cwd_path = Path(os.path.normpath(cwd_str)).resolve()
    # 1. Nếu dự án có project-docs (chuẩn công ty AI), ghi trực tiếp vào project-docs/sessions/
    project_docs = cwd_path / "project-docs"
    if project_docs.exists() and project_docs.is_dir():
        target = project_docs / "sessions"
        try:
            target.mkdir(parents=True, exist_ok=True)
            return target
        except Exception:
            pass

    # 2. Mặc định lưu trực tiếp vào .claude/sessions/ ngay trong thư mục project để đi theo git/máy mới
    try:
        target = cwd_path / ".claude" / "sessions"
        target.mkdir(parents=True, exist_ok=True)
        return target
    except Exception:
        # 3. Fallback về thư mục trung tâm nếu cwd là read-only
        home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
        project_id = safe_project_id(cwd_str)
        target = home / ".claude" / "ai-company-base-memory" / "sessions" / project_id
        target.mkdir(parents=True, exist_ok=True)
        return target


def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except Exception:
        print("autosave: invalid stdin JSON", file=sys.stderr)
        return
    cwd = payload.get("cwd") or os.getcwd()
    session_id = payload.get("session_id", "unknown")
    reason = payload.get("reason", "unknown")
    transcript_path = payload.get("transcript_path", "")
    try:
        entries = extract_entries(transcript_path) if transcript_path else []
        user_prompts, file_paths, commands = parse_transcript(entries)
        if len(user_prompts) < 2:
            print("autosave: session too short, skipping", file=sys.stderr)
            return
        session_dir = get_session_dir(cwd)
        ts_file = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        note_path = session_dir / f"{ts_file}-{session_id[:8]}.md"
        note_path.write_text(build_note(session_id, reason, cwd, user_prompts, file_paths, commands), encoding="utf-8")
        print(f"autosave: wrote {note_path}", file=sys.stderr)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print("autosave: error during save (session not blocked)", file=sys.stderr)


if __name__ == "__main__":
    main()
