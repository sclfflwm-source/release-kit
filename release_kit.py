#!/usr/bin/env python3
"""Five dependency-free checks for a software release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checksums(root: Path, files: list[Path]) -> list[str]:
    return [f"{sha256(root / name)}  {name.as_posix()}" for name in sorted(files)]


def verify(root: Path, manifest: Path) -> list[str]:
    issues = []
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            issues.append(f"line {line_number}: malformed checksum")
            continue
        expected, relative = match.groups()
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
            issues.append(f"{relative}: missing or outside root")
        elif sha256(candidate) != expected:
            issues.append(f"{relative}: checksum mismatch")
    return issues


def env_keys(path: Path) -> set[str]:
    keys = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        if not match:
            raise ValueError(f"{path}:{line_number}: invalid environment entry")
        keys.add(match.group(1))
    return keys


def env_diff(example: Path, actual: Path) -> list[str]:
    expected, found = env_keys(example), env_keys(actual)
    return ([f"missing environment key: {key}" for key in sorted(expected - found)] +
            [f"undocumented environment key: {key}" for key in sorted(found - expected)])


def changelog(path: Path, version: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    escaped = re.escape(version)
    pattern = rf"^##\s+(?:\[)?{escaped}(?:\])?(?:\s+-\s+\d{{4}}-\d{{2}}-\d{{2}})?\s*$"
    return [] if re.search(pattern, text, re.MULTILINE) else [f"missing changelog heading: {version}"]


def local_links(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues = []
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        target = target.split("#", 1)[0]
        if not target or "://" in target or target.startswith(("mailto:", "#")):
            continue
        if not (path.parent / target).exists():
            issues.append(f"missing local link: {target}")
    return issues


def json_files(files: list[Path]) -> list[str]:
    issues = []
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(f"{path}: {exc}")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("checksums", help="print SHA-256 manifest")
    make.add_argument("root", type=Path)
    make.add_argument("files", nargs="+", type=Path)
    check = commands.add_parser("verify", help="verify a SHA-256 manifest")
    check.add_argument("root", type=Path)
    check.add_argument("manifest", type=Path)
    env = commands.add_parser("env", help="compare environment variable names")
    env.add_argument("example", type=Path)
    env.add_argument("actual", type=Path)
    log = commands.add_parser("changelog", help="require a release heading")
    log.add_argument("file", type=Path)
    log.add_argument("version")
    links = commands.add_parser("links", help="check local Markdown link targets")
    links.add_argument("files", nargs="+", type=Path)
    js = commands.add_parser("json", help="parse JSON files")
    js.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "checksums":
            issues = checksums(args.root, args.files)
            print("\n".join(issues))
            return 0
        if args.command == "verify":
            issues = verify(args.root, args.manifest)
        elif args.command == "env":
            issues = env_diff(args.example, args.actual)
        elif args.command == "changelog":
            issues = changelog(args.file, args.version)
        elif args.command == "links":
            issues = [f"{path}: {issue}" for path in args.files for issue in local_links(path)]
        else:
            issues = json_files(args.files)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print("\n".join(issues) if issues else "OK")
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
