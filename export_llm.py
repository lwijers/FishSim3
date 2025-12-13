from __future__ import annotations
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "project_llm_dump.txt"

# Folders and files we don't want to walk/dump at all
IGNORE_DIRS = {
    ".git",
    ".idea",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
}

IGNORE_SUFFIXES = {
    ".pyc",
    ".pyo",
}

IGNORE_FILES = {
    "export_llm.py",
    "project_llm_dump.txt",
    OUTPUT.name,
}

# Directories for which we still show files in TREE but skip their content
SKIP_CONTENT_DIR_PREFIXES = {
    "engine/tests",   # tests: keep in TREE, no FILE block
}

# Media / binary-ish stuff: we *list* them in TREE, but do NOT dump contents
MEDIA_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tga",
    ".psd",
    ".svg",
    ".ico",
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".m4a",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
}

# "Safe" text-like files we actually dump content for
TEXT_SUFFIXES = {
    ".py",
    ".txt",
    ".md",
    ".rst",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".yaml",
    ".yml",
    ".csv",
}

ALWAYS_INCLUDE_BY_NAME = {
    "pyproject.toml",
    "requirements.txt",
    ".gitignore",
    "README",
    "README.md",
    "README-dev.md",
    "LICENSE",
}

# Optional per-file character cap (None = no cap).
# You can lower this if dumps ever get giant.
MAX_CHARS_PER_FILE: int | None = None


def list_files() -> list[Path]:
    """
    Prefer tracked files via git ls-files.
    Fallback: walk the tree, skipping ignored dirs/suffixes.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        files: list[Path] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            path = ROOT / line
            if path.is_file():
                files.append(path)
        return files
    except Exception:
        files: list[Path] = []
        for path in ROOT.rglob("*"):
            if path.is_dir():
                continue
            rel = path.relative_to(ROOT)
            if any(part in IGNORE_DIRS for part in rel.parts):
                continue
            if path.suffix in IGNORE_SUFFIXES:
                continue
            files.append(path)
        return files


def is_media(path: Path) -> bool:
    return path.suffix.lower() in MEDIA_SUFFIXES


def is_in_skip_content_dir(rel_posix: str) -> bool:
    return any(
        rel_posix == prefix or rel_posix.startswith(prefix + "/")
        for prefix in SKIP_CONTENT_DIR_PREFIXES
    )


def should_dump_content(path: Path) -> bool:
    rel_posix = path.relative_to(ROOT).as_posix()

    # Test / skipped-content dirs: only TREE, no FILE content
    if is_in_skip_content_dir(rel_posix):
        return False

    # Important meta-files always included
    if path.name in ALWAYS_INCLUDE_BY_NAME:
        return True

    suffix = path.suffix.lower()
    if suffix in MEDIA_SUFFIXES:
        return False
    if suffix in IGNORE_SUFFIXES:
        return False
    if suffix in TEXT_SUFFIXES:
        return True

    # Default: skip weird/binary stuff to keep file small
    return False


def build_tree(files: list[Path]) -> list[str]:
    """
    Build a simple flat TREE listing of *both* directories and files.

    Example:
        TREE
        .
        assets
        assets/sprites
        assets/sprites/fish_idle.png
        engine
        engine/ecs
        engine/ecs/world.py
        ...
    """
    entries: set[str] = {"."}
    for f in files:
        rel = f.relative_to(ROOT)
        parts = rel.parts

        # Add all parent dirs
        for i in range(1, len(parts)):
            entries.add(Path(*parts[:i]).as_posix())

        # Add the file itself
        entries.add(rel.as_posix())

    return ["TREE"] + sorted(entries)


def main() -> None:
    files = sorted(list_files(), key=lambda p: p.as_posix())

    files_for_tree: list[Path] = []
    files_for_content: list[Path] = []

    for path in files:
        if path.name in IGNORE_FILES:
            continue
        rel = path.relative_to(ROOT)
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue
        if path.suffix in IGNORE_SUFFIXES:
            continue

        files_for_tree.append(path)
        if should_dump_content(path):
            files_for_content.append(path)

    lines: list[str] = []

    # 1) TREE section with dirs + *all* files (including media & tests)
    lines.extend(build_tree(files_for_tree))
    lines.append("")  # blank line after TREE

    # 2) FILE sections (only runtime-ish code / configs / docs)
    for path in files_for_content:
        rel = path.relative_to(ROOT).as_posix()
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            lines.append(f"\nFILE {rel}\n[omitted non-text content]")
            continue

        if MAX_CHARS_PER_FILE is not None and len(content) > MAX_CHARS_PER_FILE:
            content = (
                content[:MAX_CHARS_PER_FILE]
                + "\n\n[... TRUNCATED BY export_llm.py ...]\n"
            )

        lines.append(f"\nFILE {rel}\n{content}")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
