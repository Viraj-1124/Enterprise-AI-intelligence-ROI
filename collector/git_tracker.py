"""
Reads legitimate, locally-available Git evidence (commits made during the
session, files/lines changed) via the `git` CLI. Never touches any AI
tool's internals -- this only looks at the developer's own git history.
"""
import subprocess
from dataclasses import dataclass


@dataclass
class GitActivity:
    commits: int
    files_changed: int
    lines_added: int
    lines_removed: int
    commit_hashes: list[str]


def _run(args: list[str], cwd: str, allow_fail: bool = False) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        if allow_fail:
            return ""
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def is_git_repo(path: str) -> bool:
    try:
        out = _run(["rev-parse", "--is-inside-work-tree"], cwd=path)
        return out.strip() == "true"
    except Exception:
        return False


def get_activity_since(path: str, since_iso: str) -> GitActivity:
    """Summarize commits made in `path` since `since_iso` (an ISO-8601 timestamp)."""
    if not is_git_repo(path):
        return GitActivity(0, 0, 0, 0, [])

    log_out = _run(["log", f"--since={since_iso}", "--pretty=format:%H"], cwd=path, allow_fail=True)
    hashes = [h for h in log_out.splitlines() if h.strip()]

    files_changed = 0
    lines_added = 0
    lines_removed = 0
    if hashes:
        stat_out = _run(["log", f"--since={since_iso}", "--numstat", "--pretty=format:"], cwd=path, allow_fail=True)
        seen_files = set()
        for line in stat_out.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            added, removed, filename = parts
            seen_files.add(filename)
            if added.isdigit():
                lines_added += int(added)
            if removed.isdigit():
                lines_removed += int(removed)
        files_changed = len(seen_files)

    return GitActivity(
        commits=len(hashes),
        files_changed=files_changed,
        lines_added=lines_added,
        lines_removed=lines_removed,
        commit_hashes=hashes,
    )
