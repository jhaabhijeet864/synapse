"""
core/tools/file_patcher.py
──────────────────────────
Local workspace patch engine.

Applies unified diff patches to files in the current project.
Called when user clicks "Apply Fix" and a code diff is available.

Safety rules:
  - Always creates a .bak backup before patching
  - Only patches files within the detected project root
  - Refuses to patch files outside project boundary (path traversal guard)
"""

import re
import shutil
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PatchResult:
    success: bool
    patched_file: str
    backup_path: str
    lines_changed: int
    error: Optional[str] = None


class FilePatcher:
    """
    Applies unified diff patches safely to local files.

    Usage:
        patcher = FilePatcher(project_root="/path/to/project")
        result = patcher.apply(diff_text)
    """

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else None

    def apply(self, diff_text: str) -> list[PatchResult]:
        """
        Parse and apply a unified diff. Returns one PatchResult per file patched.
        """
        results = []
        file_patches = self._parse_diff(diff_text)
        for filepath, hunks in file_patches.items():
            result = self._apply_to_file(filepath, hunks)
            results.append(result)
        return results

    def _apply_to_file(self, filepath: str, hunks: list) -> PatchResult:
        target = Path(filepath)

        # Safety: resolve and ensure within project root
        if self.project_root:
            try:
                target.resolve().relative_to(self.project_root.resolve())
            except ValueError:
                return PatchResult(False, filepath, "", 0,
                                   error="Path traversal blocked — file outside project root")

        if not target.exists():
            return PatchResult(False, filepath, "", 0, error=f"File not found: {filepath}")

        # Backup
        backup_path = str(target) + f".bak.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(target, backup_path)

        lines = target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        changed = 0

        for hunk in hunks:
            lines, delta = self._apply_hunk(lines, hunk)
            changed += delta

        target.write_text("".join(lines), encoding="utf-8")
        return PatchResult(True, filepath, backup_path, changed)

    @staticmethod
    def _apply_hunk(lines: list[str], hunk: dict) -> tuple[list[str], int]:
        """Apply a single hunk to lines. Returns modified lines and change count."""
        start = max(0, hunk["old_start"] - 1)
        old_lines = hunk["old_lines"]
        new_lines = hunk["new_lines"]

        result = lines[:start] + new_lines + lines[start + len(old_lines):]
        changed = abs(len(new_lines) - len(old_lines))
        return result, changed

    @staticmethod
    def _parse_diff(diff_text: str) -> dict[str, list]:
        """
        Parse unified diff format into a dict of {filepath: [hunks]}.
        Supports the standard +++ / --- / @@ format.
        """
        file_patches: dict[str, list] = {}
        current_file = None
        current_hunks = []

        for line in diff_text.splitlines(keepends=True):
            if line.startswith("+++ "):
                if current_file and current_hunks:
                    file_patches[current_file] = current_hunks
                # Strip the "+++ " marker, then an optional git b/ prefix.
                # Handles both "+++ b/rel/path.py" and "+++ C:\abs\path.py".
                current_file = line[4:].strip()
                current_file = re.sub(r"^[ab]/", "", current_file).strip('"').strip("'")
                current_hunks = []
            elif line.startswith("@@"):
                # Parse hunk header: @@ -start,count +start,count @@
                m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
                if m:
                    current_hunks.append({
                        "old_start": int(m.group(1)),
                        "old_count": int(m.group(2) or 1),
                        "new_start": int(m.group(3)),
                        "new_count": int(m.group(4) or 1),
                        "old_lines": [],
                        "new_lines": [],
                    })
            elif current_hunks:
                hunk = current_hunks[-1]
                if line.startswith("-"):
                    hunk["old_lines"].append(line[1:])
                elif line.startswith("+"):
                    hunk["new_lines"].append(line[1:])
                elif line.startswith(" "):
                    hunk["old_lines"].append(line[1:])
                    hunk["new_lines"].append(line[1:])

        if current_file and current_hunks:
            file_patches[current_file] = current_hunks

        return file_patches
