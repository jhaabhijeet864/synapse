"""tests/test_patcher.py — FilePatcher unit tests (offline, tmp dirs)."""
from pathlib import Path
from core.tools.file_patcher import FilePatcher


def test_parse_git_style_diff():
    diff = "--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
    parsed = FilePatcher._parse_diff(diff)
    assert "a.py" in parsed
    assert len(parsed["a.py"]) == 1


def test_parse_absolute_windows_path():
    diff = "--- a/a.py\n+++ C:\\proj\\a.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
    parsed = FilePatcher._parse_diff(diff)
    assert "C:\\proj\\a.py" in parsed


def test_apply_absolute_path_in_project(tmp_path):
    target = tmp_path / "a.py"
    target.write_text("x = 1\n")
    diff = f"--- a/a.py\n+++ {target}\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
    results = FilePatcher(project_root=str(tmp_path)).apply(diff)
    assert len(results) == 1 and results[0].success
    assert target.read_text() == "x = 2\n"
    assert list(tmp_path.glob("a.py.bak.*"))


def test_path_traversal_blocked(tmp_path):
    diff = "--- a/evil.py\n+++ C:\\Windows\\evil.py\n@@ -1 +1 @@\n-a\n+b\n"
    results = FilePatcher(project_root=str(tmp_path)).apply(diff)
    assert len(results) == 1 and not results[0].success
    assert "outside project root" in (results[0].error or "")
