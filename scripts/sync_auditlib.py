from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent.parent
VENDOR_DIR = TOOL_ROOT / "scripts" / "auditlib"
MANIFEST_PATH = VENDOR_DIR / "_vendor_manifest.json"
UPSTREAM_URL = "https://github.com/lucas-lima-s/claude-skill-repo-audit"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _iter_vendored_files() -> list[Path]:
    return sorted(
        p
        for p in VENDOR_DIR.rglob("*")
        if p.is_file() and p.name != "_vendor_manifest.json" and "__pycache__" not in p.parts
    )


def _relative_name(path: Path) -> str:
    return str(path.relative_to(VENDOR_DIR)).replace("\\", "/")


def _git_head(repo: Path) -> str:
    import subprocess

    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return "0" * 40
    return result.stdout.strip()


def sync_from(source_repo: Path) -> int:
    source_vendor = source_repo / "scripts" / "auditlib"
    if not source_vendor.is_dir():
        print(f"sync_auditlib: source has no scripts/auditlib/: {source_vendor}", file=sys.stderr)
        return 2

    for entry in _iter_vendored_files():
        entry.unlink()
    for entry in list(VENDOR_DIR.rglob("*")):
        if entry.is_dir() and not any(entry.iterdir()):
            entry.rmdir()

    files: dict[str, str] = {}
    for source_file in sorted(p for p in source_vendor.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        rel = source_file.relative_to(source_vendor)
        dest = VENDOR_DIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_file, dest)
        files[str(rel).replace("\\", "/")] = _sha256(dest)

    manifest = {
        "upstream": UPSTREAM_URL,
        "upstream_commit": _git_head(source_repo),
        "synced_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": dict(sorted(files.items())),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"sync_auditlib: vendored {len(files)} file(s) from {source_repo}")
    return 0


def check() -> int:
    if not MANIFEST_PATH.exists():
        print(f"sync_auditlib: manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    recorded: dict[str, str] = manifest.get("files", {})

    actual_files = {_relative_name(p) for p in _iter_vendored_files()}
    recorded_files = set(recorded.keys())

    drifted: list[str] = []

    for rel in sorted(recorded_files & actual_files):
        actual_hash = _sha256(VENDOR_DIR / rel)
        if actual_hash != recorded[rel]:
            drifted.append(f"scripts/auditlib/{rel}")

    for rel in sorted(actual_files - recorded_files):
        drifted.append(f"scripts/auditlib/{rel} (untracked by manifest)")

    for rel in sorted(recorded_files - actual_files):
        drifted.append(f"scripts/auditlib/{rel} (missing on disk)")

    if drifted:
        for line in drifted:
            print(f"drift: {line}")
        return 1

    print("auditlib: 0 drifted files")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sync_auditlib.py",
        description="Vendor scripts/auditlib/ from claude-skill-repo-audit and check for drift.",
    )
    parser.add_argument("--from", dest="source", default=None, help="path to a claude-skill-repo-audit clone")
    parser.add_argument("--check", action="store_true", help="verify the vendored copy matches the manifest")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.source:
        rc = sync_from(Path(args.source).resolve())
        if rc != 0 or not args.check:
            return rc
        return check()

    if args.check:
        return check()

    print("sync_auditlib: nothing to do (pass --from <path> or --check)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
