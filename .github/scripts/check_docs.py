"""Validate required documentation and local Markdown links."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path.cwd().resolve()
REQUIRED = (
    Path("README.md"),
    Path("SECURITY.md"),
    Path("CONTRIBUTING.md"),
    Path("docs/seo-metadata.md"),
)
LINK_PATTERN = re.compile(r"!?[[^]]*](([^)]+))")


def link_target(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        value = value[1 : value.index(">")]
    else:
        value = value.split(maxsplit=1)[0]
    return unquote(value.split("#", 1)[0])


def main() -> int:
    errors: list[str] = []

    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")

    markdown_files = sorted(
        path for path in ROOT.rglob("*.md") if ".git" not in path.parts
    )
    if not markdown_files:
        errors.append("no Markdown files found")

    for path in markdown_files:
        relative = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")

        if not text.strip():
            errors.append(f"empty Markdown file: {relative}")
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in LINK_PATTERN.finditer(line):
                raw = match.group(1).strip()
                if raw.startswith(("http://", "https://", "mailto:", "tel:", "#")):
                    continue

                target = link_target(raw)
                if not target:
                    continue

                resolved = (path.parent / target).resolve()
                try:
                    resolved.relative_to(ROOT)
                except ValueError:
                    errors.append(
                        f"{relative}:{line_number}: link escapes repository: {raw}"
                    )
                    continue

                if not resolved.exists():
                    errors.append(
                        f"{relative}:{line_number}: broken relative link: {raw}"
                    )

    if errors:
        print("Documentation checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Documentation checks passed for {len(markdown_files)} Markdown files."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
