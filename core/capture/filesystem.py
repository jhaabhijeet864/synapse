"""
core/capture/filesystem.py
──────────────────────────
Async directory delta caching via watchdog.

Detects:
  - Active project root (by presence of .git, pyproject.toml, package.json, etc.)
  - Recently modified files (rolling 10-file buffer per project)
  - Project language/framework fingerprint

Architecture role: SLOW LANE — passive background enrichment, low CPU.
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from watchdog.events import FileModifiedEvent, FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer


# Project marker files that identify a project root
PROJECT_MARKERS = {
    ".git":            "git",
    "pyproject.toml":  "python",
    "requirements.txt":"python",
    "package.json":    "node",
    "Cargo.toml":      "rust",
    "go.mod":          "go",
    "pom.xml":         "java",
    "*.sln":           "csharp",
}

# File extensions to track (ignore media, binaries, etc.)
TRACKED_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java",
    ".cs", ".cpp", ".c", ".h", ".hpp", ".md", ".toml", ".json",
    ".yaml", ".yml", ".env", ".sh", ".bat",
}

# Directories to always ignore
IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "target", ".cache",
}


@dataclass
class ProjectContext:
    root_path: str
    language: str
    framework: str = ""
    recent_files: list[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.utcnow)

    def add_recent(self, path: str, max_files: int = 10) -> None:
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:max_files]


class SynapseFileEventHandler(FileSystemEventHandler):
    """Watchdog event handler — routes file events to the project context."""

    def __init__(self, project: ProjectContext, on_change):
        super().__init__()
        self.project = project
        self.on_change = on_change

    def on_modified(self, event: FileModifiedEvent) -> None:
        if not event.is_directory:
            self._handle(event.src_path)

    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory:
            self._handle(event.src_path)

    def _handle(self, path: str) -> None:
        p = Path(path)
        # Skip untracked extensions and ignored dirs
        if p.suffix not in TRACKED_EXTENSIONS:
            return
        if any(part in IGNORED_DIRS for part in p.parts):
            return
        self.project.add_recent(str(p))
        if self.on_change:
            self.on_change(self.project)


class FilesystemWatcher:
    """
    Watches the filesystem for project activity.

    Automatically detects the active project root from the currently
    focused window's process working directory, then starts a watchdog
    observer on that root.

    Usage:
        watcher = FilesystemWatcher(on_change=handler)
        await watcher.start()
    """

    def __init__(self, on_change=None):
        self.on_change = on_change
        self._observer: Optional[Observer] = None
        self._current_project: Optional[ProjectContext] = None
        self._watched_path: Optional[str] = None

    async def start(self) -> None:
        """Start the watchdog observer."""
        self._observer = Observer()
        self._observer.start()

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()

    def watch_path(self, path: str) -> Optional[ProjectContext]:
        """
        Switch to watching a new path (e.g., when user switches projects).
        Returns the detected ProjectContext.
        """
        if path == self._watched_path:
            return self._current_project

        # Find project root upward from path
        root = self._find_project_root(path)
        if not root:
            return None

        # Unschedule previous watch
        if self._observer:
            self._observer.unschedule_all()

        project = self._build_project_context(root)
        handler = SynapseFileEventHandler(project, self.on_change)

        if self._observer:
            self._observer.schedule(handler, str(root), recursive=True)

        self._current_project = project
        self._watched_path = path
        return project

    def get_current_project(self) -> Optional[ProjectContext]:
        return self._current_project

    # ──────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _find_project_root(start_path: str) -> Optional[Path]:
        """Walk up from start_path to find a project root."""
        p = Path(start_path)
        if p.is_file():
            p = p.parent
        for ancestor in [p, *p.parents]:
            for marker in PROJECT_MARKERS:
                if (ancestor / marker).exists():
                    return ancestor
        return None

    @staticmethod
    def _build_project_context(root: Path) -> ProjectContext:
        """Detect language/framework from project root markers."""
        language = "unknown"
        framework = ""

        for marker, lang in PROJECT_MARKERS.items():
            if (root / marker).exists():
                language = lang
                break

        # Framework detection
        pkg_json = root / "package.json"
        if pkg_json.exists():
            try:
                import json
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "react" in deps:
                    framework = "React"
                elif "vue" in deps:
                    framework = "Vue"
                elif "next" in deps:
                    framework = "Next.js"
            except Exception:
                pass

        return ProjectContext(root_path=str(root), language=language, framework=framework)
