import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from event_schema import NormalizedEvent
from git_tracker import get_activity_since, is_git_repo
from session_tracker import SessionState, save_state, load_state, clear_state, now_iso


def test_normalized_event_rejects_unsupported_type():
    with pytest.raises(ValueError):
        NormalizedEvent(employee_id="e1", task_id="t1", timestamp=NormalizedEvent.now_iso(),
                         event_type="not_a_real_type", source="observed")


def test_normalized_event_roundtrip():
    ev = NormalizedEvent(employee_id="e1", task_id="t1", timestamp=NormalizedEvent.now_iso(),
                          event_type="commit", source="observed", tool="git", metadata={"sha": "abc"})
    d = ev.to_dict()
    assert d["event_type"] == "commit"
    assert d["metadata"]["sha"] == "abc"


def test_session_state_save_load_clear(tmp_path):
    path = str(tmp_path / "state.json")
    state = SessionState(employee_id="e1", task_id="t1", tool="antigravity", repo_path="/tmp", started_at=now_iso())
    save_state(state, path=path)
    loaded = load_state(path=path)
    assert loaded.employee_id == "e1"
    assert loaded.tool == "antigravity"
    clear_state(path=path)
    assert load_state(path=path) is None


def test_is_git_repo_false_for_non_repo(tmp_path):
    assert is_git_repo(str(tmp_path)) is False


def test_git_activity_counts_commits(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    def run(*args):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

    run("init", "-q")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Test")

    since = now_iso()

    (repo / "file1.txt").write_text("hello\nworld\n")
    run("add", "file1.txt")
    run("commit", "-q", "-m", "first commit")

    activity = get_activity_since(str(repo), since)
    assert activity.commits == 1
    assert activity.files_changed == 1
    assert activity.lines_added == 2
    assert activity.lines_removed == 0


def test_git_activity_empty_repo_no_commits_since(tmp_path):
    repo = tmp_path / "repo2"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True, capture_output=True)

    # No commits at all -> no activity, and it must not crash on an empty repo.
    activity = get_activity_since(str(repo), now_iso())
    assert activity.commits == 0
    assert activity.files_changed == 0
