# Graphify and Global Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in-by-install global Claude Code auto-memory plus local per-project session notes, and a manual `/graphify` skill, without replacing existing settings or repo changes.

**Architecture:** Claude Code's native `autoMemoryEnabled` is enabled in the user's settings. A `SessionEnd` command hook invokes a small Python-standard-library script which reads the supplied transcript and writes a filtered, minimal session note under the user's `.claude` data directory, partitioned by project. The toolkit installs a separate `/graphify` skill; graph generation remains manual and AST-only by default.

**Tech Stack:** PowerShell 5.1-compatible installer, Python 3 standard library, Claude Code skill Markdown, JSON settings, Python `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-28-graphify-native-integration-design.md`

## Global Constraints

- Enable `autoMemoryEnabled: true` in user settings for all projects, unless user later sets it to false.
- The global `SessionEnd` hook stores only a filtered session summary, at most 20 file paths and 10 commands; never copy full transcript, file contents, or tool output.
- Hook failures must not block session termination; no API calls, API keys, network access, or extra Python packages.
- Partition logs by project; keep the log directory outside repositories so notes are not committed.
- `/graphify` defaults to AST-only and does not run automatically; semantic extraction only after explicit user request.
- Installer reruns must not duplicate the toolkit hook or overwrite unrelated settings/hooks; uninstall removes only toolkit-owned files/configuration.
- Preserve all pre-existing working tree changes; do not commit or push.

## Review Focus

- Existing settings with unrelated hooks: test that merge keeps every hook and only adds one toolkit-owned `SessionEnd` entry.
- Existing malformed settings JSON: installer must stop before writing, and the test/manual check must confirm source bytes remain unchanged.
- Repeated install/uninstall: test idempotent install and removal limited to the owned entry; restore `autoMemoryEnabled` only if it still has the value set by this installer and ownership metadata proves toolkit changed it.
- Transcript with secrets or tool output: test secret filtering and ensure no tool output/file contents are written.
- Missing/malformed transcript, short session, or path with spaces: test graceful skip and correct project partition without blocking exit.

---

### Task 1: Build the local session autosave script

**Files:**
- Create: `scripts/session_autosave.py`
- Create: `tests/test_session_autosave.py`

**Interfaces:**
- Consumes stdin JSON fields `transcript_path`, `cwd`, `session_id`, and `reason` from the `SessionEnd` hook.
- Produces a Markdown note under `~/.claude/ai-company-base-memory/sessions/<project-id>/` and diagnostic messages without prompt text.

- [ ] Write `unittest` cases for valid transcript serialization, no raw tool output/file content, secret redaction, max 20 file paths/10 commands, invalid or missing transcript no-op, and project IDs that avoid path traversal.
- [ ] Run `python -I -m unittest discover -s tests -v` and confirm tests fail because the script is absent/incomplete.
- [ ] Implement a standard-library-only script with bounded JSONL parsing, filtered first user prompt, edit/write file paths, bounded Bash command samples, and safe project ID derived from canonical cwd; skip sessions with fewer than two non-empty user text prompts.
- [ ] Run the same unittest command and confirm all tests pass.

### Task 2: Add `/graphify` skill and output ignore rule

**Files:**
- Create: `.claude/skills/graphify/SKILL.md`
- Modify: `.gitignore`

**Interfaces:**
- Skill uses the user's `$ARGUMENTS`, working directory, and `graphify` CLI.
- Output convention is `<project>/graphify-out/`; ignore only `graphify-out/cache/`.

- [ ] Add a manual skill flow that checks CLI availability, asks the user to install `graphifyy` if missing, defaults to `graphify extract . --out ./graphify-out --no-cluster`, reports generated artifacts, supports graph update/tree only when requested, and never invokes semantic extraction without explicit request.
- [ ] Add `graphify-out/cache/` to `.gitignore` without ignoring `graph.json` or reports.
- [ ] Inspect the skill for exact CLI arguments, safe handling of user-supplied scope, and no automatic API-key use.

### Task 3: Make the installer safely configure global memory

**Files:**
- Modify: `install.ps1`
- Test: manual PowerShell isolated-profile checks (see steps)

**Interfaces:**
- Install copies scripts to `$HOME\.claude\ai-company-base\scripts\` and skills to existing user skill destinations.
- User settings target: `$HOME\.claude\settings.json`.
- Toolkit hook command is an absolute Python script path, correctly quoted for Windows PowerShell.
- Ownership metadata: `$HOME\.claude\ai-company-base\memory-install-state.json`, recording whether `autoMemoryEnabled` existed and its original value.

- [ ] Add a PowerShell isolated-profile test procedure using a temporary HOME/config directory and seed `settings.json` with unrelated keys plus an unrelated `SessionEnd` hook; capture expected merged output.
- [ ] Run the procedure against current installer and confirm it fails to install memory/script or merge the hook.
- [ ] Extend install to parse existing JSON before any writes, abort on malformed JSON, preserve all fields and hooks, enable `autoMemoryEnabled`, add exactly one uniquely identifiable toolkit hook, copy the script, and record original setting state only on first installation.
- [ ] Extend uninstall to remove only the uniquely identifiable toolkit hook and its installed skill/script/state files; restore the prior `autoMemoryEnabled` state only when current value is still `true` and ownership metadata shows installer changed it.
- [ ] Run isolated-profile checks for clean install, install with existing hooks, second install, malformed JSON no-write, uninstall, and uninstall with user-edited autoMemoryEnabled; validate resulting JSON with `ConvertFrom-Json`.
- [ ] Verify Python availability is reported clearly when absent; native auto-memory remains enabled and session termination is unaffected.

### Task 4: Document global memory and Graphify

**Files:**
- Modify: `README.md`

**Interfaces:**
- README documents install/uninstall commands, memory storage and privacy limits, `autoMemoryEnabled` opt-out, Python prerequisite/behavior, and `/graphify` usage.

- [ ] Document native auto-memory as project-scoped, SessionEnd notes as local and per-project, what fields can be stored, how to opt out, and that logs are not full transcripts.
- [ ] Document `/graphify`, the `graphifyy` prerequisite, AST-only default, and explicit semantic mode caveat.
- [ ] Correct installer completion output to include `/graphify` and explain missing Python behavior.

### Task 5: Verify the integrated installation

**Files:**
- Verify: all files above; no unrelated files should be reverted.

- [ ] Run `python -I -m unittest discover -s tests -v`.
- [ ] Run PowerShell isolated-profile installer checks and validate JSON structure/idempotency/uninstall behavior.
- [ ] Run `git diff --check` and review `git status --short` plus focused diffs; confirm pre-existing edits remain untouched.
- [ ] Report test results and clearly state that this changes the repository installer but does not write the live `$HOME\.claude\settings.json` unless the installer is run.
