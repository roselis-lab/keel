"""`keel recheck`: is each quoted line still where the report saw it?

A reassessment starts from the places the last report pinned. These tests build a small
git repository, record evidence against one commit, change the code, and check that the
command tells in place, moved and gone apart, keeps several repositories separate, and
never runs a command it finds in a report.
"""
import subprocess

import pytest
import yaml

from keel import recheck as rc
from keel.schemas.report import Evidence, Report

CODE = "import gateway\n\n\ndef refund(order_id, amount):\n    return gateway.refund(order_id, amount)\n"
QUOTE = "def refund(order_id, amount):\n    return gateway.refund(order_id, amount)"


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


def _repo(path, files):
    path.mkdir()
    _git(path, "init", "-q")
    _commit(path, files)
    return path


def _commit(repo, files):
    for name, text in files.items():
        target = repo / name
        if text is None:
            target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")


def _read(id, path="app/refunds.py", lines="4-5", quote=QUOTE, repo=None):
    return Evidence(id=id, kind="read", commit="4043f65", path=path, lines=lines, quote=quote, repo=repo)


def _status(ev, repos):
    return rc.check(ev, repos)


def test_unchanged_code_is_in_place(tmp_path):
    repo = _repo(tmp_path / "app", {"app/refunds.py": CODE})
    assert _status(_read(1), {None: repo})["status"] == rc.IN_PLACE


def test_reindented_code_is_still_in_place(tmp_path):
    repo = _repo(tmp_path / "app", {"app/refunds.py": CODE.replace("    return", "        return")})
    assert _status(_read(1), {None: repo})["status"] == rc.IN_PLACE


def test_lines_pushed_down_are_moved_with_the_new_range(tmp_path):
    repo = _repo(tmp_path / "app", {"app/refunds.py": CODE})
    _commit(repo, {"app/refunds.py": "# audit\n# log\n" + CODE})
    row = _status(_read(1), {None: repo})
    assert row["status"] == rc.MOVED
    assert row["now"] == ["6-7"]


def test_changed_lines_are_gone(tmp_path):
    repo = _repo(tmp_path / "app", {"app/refunds.py": CODE})
    _commit(repo, {"app/refunds.py": CODE.replace("amount)\n", "min(amount, 500))\n")})
    assert _status(_read(1), {None: repo})["status"] == rc.GONE


def test_deleted_file_is_gone(tmp_path):
    repo = _repo(tmp_path / "app", {"app/refunds.py": CODE, "README": "x\n"})
    _commit(repo, {"app/refunds.py": None})
    row = _status(_read(1), {None: repo})
    assert row["status"] == rc.GONE
    assert row["note"] == "file not found"


def test_head_is_read_not_the_working_tree(tmp_path):
    repo = _repo(tmp_path / "app", {"app/refunds.py": CODE})
    (repo / "app/refunds.py").write_text("nothing here\n", encoding="utf-8")
    assert _status(_read(1), {None: repo})["status"] == rc.IN_PLACE


def test_each_repository_is_read_from_its_own_checkout(tmp_path):
    api = _repo(tmp_path / "api", {"app/refunds.py": CODE})
    web = _repo(tmp_path / "web", {"app/refunds.py": "render(markdown)\n"})
    repos = rc._parse_repos([f"api={api}", f"web={web}"])
    assert _status(_read(1, repo="api"), repos)["status"] == rc.IN_PLACE
    assert _status(_read(2, repo="web"), repos)["status"] == rc.GONE


def test_a_repository_with_no_checkout_is_not_checked(tmp_path):
    repo = _repo(tmp_path / "app", {"app/refunds.py": CODE})
    row = _status(_read(1, repo="payments"), {None: repo})
    assert row["status"] == rc.NOT_CHECKED


def test_a_folder_that_is_not_a_checkout_is_not_checked(tmp_path):
    (tmp_path / "plain").mkdir()
    assert _status(_read(1), {None: tmp_path / "plain"})["status"] == rc.NOT_CHECKED


def test_commands_are_listed_and_never_run(tmp_path, monkeypatch):
    marker = tmp_path / "ran"
    ev = Evidence(id=1, kind="command", quote="ok", command=f"touch {marker}")
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: calls.append(a))
    row = _status(ev, {None: tmp_path})
    assert row["status"] == rc.BY_HAND
    assert row["command"] == f"touch {marker}"
    assert calls == [] and not marker.exists()


def test_windows_paths_are_the_default_checkout_not_a_name():
    assert rc._parse_repos([r"C:\code\app"]) == {None: rc.Path(r"C:\code\app")}


@pytest.mark.parametrize("bad", ["https://x.test/a?q=1", "-rf", "a b"])
def test_repo_name_is_a_plain_token(bad):
    with pytest.raises(ValueError):
        _read(1, repo=bad)


def test_cli_prints_one_line_per_entry(tmp_path, capsys):
    repo = _repo(tmp_path / "app", {"app/refunds.py": CODE})
    report = Report(system_id="halo", system_name="Halo", system_description="d", date="2026-11-07",
                    assessor="a", evidence=[_read(1), _read(2, lines="1"), Evidence(
                        id=3, kind="test", quote="1 passed", command="pytest -k refund")])
    path = tmp_path / "2026-11-07.yaml"
    path.write_text(yaml.safe_dump(report.model_dump(mode="json")), encoding="utf-8")
    rc.main([str(path), "--repo", str(repo)])
    out = capsys.readouterr().out
    assert "[1] in place" in out and "[2] moved" in out and "[3] run by hand" in out
    assert "1 in place, 1 moved, 1 run by hand" in out
