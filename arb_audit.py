#!/usr/bin/env python3
"""Check Flutter ARB translations for missing keys and placeholder drift."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PLACEHOLDER = re.compile(r"(?<!\{)\{([A-Za-z][A-Za-z0-9_]*)\}(?!\})")


def load_arb(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: cannot read ARB: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: ARB root must be an object")
    return data


def messages(data: dict[str, object], path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in data.items():
        if key.startswith("@") or key == "@@locale":
            continue
        if not isinstance(value, str):
            raise ValueError(f"{path}: message {key!r} must be a string")
        result[key] = value
    return result


def audit(reference: Path, targets: list[Path]) -> list[dict[str, str]]:
    source = messages(load_arb(reference), reference)
    issues: list[dict[str, str]] = []
    for target in targets:
        translated = messages(load_arb(target), target)
        for key in sorted(source.keys() - translated.keys()):
            issues.append({"file": str(target), "key": key, "kind": "missing-key", "detail": ""})
        for key in sorted(translated.keys() - source.keys()):
            issues.append({"file": str(target), "key": key, "kind": "extra-key", "detail": ""})
        for key in sorted(source.keys() & translated.keys()):
            expected = set(PLACEHOLDER.findall(source[key]))
            actual = set(PLACEHOLDER.findall(translated[key]))
            if expected != actual:
                issues.append({
                    "file": str(target),
                    "key": key,
                    "kind": "placeholder-mismatch",
                    "detail": f"expected {sorted(expected)}, found {sorted(actual)}",
                })
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="source locale ARB file")
    parser.add_argument("targets", nargs="+", type=Path, help="translated ARB files")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args(argv)
    try:
        issues = audit(args.reference, args.targets)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(issues, ensure_ascii=False, indent=2))
    else:
        for issue in issues:
            print(f"{issue['file']}: {issue['key']}: {issue['kind']} {issue['detail']}".rstrip())
        print(f"{len(issues)} issue(s) in {len(args.targets)} file(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
