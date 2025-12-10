from __future__ import annotations
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "project_llm_dump.txt"

IGNORE_DIRS = {".git", ".idea", ".venv", "venv", "__pycache__", "build", "dist"}
IGNORE_SUFFIXES = {".pyc", ".pyo"}
IGNORE_FILES = {"export_llm.py", "project_llm.txt", OUTPUT.name}


def list_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        return [ROOT / line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        files: list[Path] = []
        for path in ROOT.rglob("*"):
            if path.is_dir():
                if path.name in IGNORE_DIRS:
                    continue
                if any(part in IGNORE_DIRS for part in path.relative_to(ROOT).parts):
                    continue
            else:
                rel = path.relative_to(ROOT)
                if rel.name in IGNORE_FILES:
                    continue
                if path.suffix in IGNORE_SUFFIXES:
                    continue
                if any(part in IGNORE_DIRS for part in rel.parts):
                    continue
                files.append(path)
        return files


def build_tree(files: list[Path]) -> list[str]:
    dirs = set(["."])
    for f in files:
        rel_parts = f.relative_to(ROOT).parts
        for i in range(1, len(rel_parts)):
            dirs.add(Path(*rel_parts[:i]).as_posix())
    return ["TREE"] + sorted(dirs)


def main() -> None:
    files = sorted(list_files(), key=lambda p: p.as_posix())
    lines = build_tree(files)
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        lines.append(f"\nFILE {rel}")
        if not path.exists():
            lines.append("[MISSING FILE]")
            continue
        lines.append(path.read_text(encoding="utf-8", errors="replace").rstrip("\n"))
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
