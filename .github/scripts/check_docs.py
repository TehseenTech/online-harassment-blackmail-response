"""Validate required documentation and local Markdown links."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    Path("README.md"),
    Path("SECURITY.md"),
    Path("CONTRIBUTING.md"),
    Path("docs/seo-metadata.md"),
)
IGNORED_PARTS = {".git", ".venv", "venv", "env", "node_modules"}
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]*)\)")
URI_SCHEME_PATTERN = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)


def link_target(raw: str) -> str:
    """Return the file component of a Markdown link target."""
    value = raw.strip()
    if not value:
        return ""
    if value.startswith("<") and ">" in value:
        value = value[1 : value.index(">")]
    else:
        value = value.split(maxsplit=1)[0]
    return unquote(value.split("#", 1)[0].split("?", 1)[0])


def main() -> int:
    """Validate required files and repository-local Markdown links."""
    errors: list[str] = []

    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file():
            errors.append(
                f"missing required file: {relative} "
                "(restore the file or update REQUIRED)"
            )

    markdown_files = sorted(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in IGNORED_PARTS for part in path.parts)
    )
    if not markdown_files:
        errors.append("no Markdown files found")

    for path in markdown_files:
        relative = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"unable to read {relative}: {exc}")
            continue

        if not text.strip():
            errors.append(f"empty Markdown file: {relative}")
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in LINK_PATTERN.finditer(line):
                raw = match.group(1).strip()
                if raw.startswith("#") or URI_SCHEME_PATTERN.match(raw):
                    continue

                target = link_target(raw)
                if not target:
                    errors.append(
                        f"{relative}:{line_number}: empty relative link target "
                        "(add a path or remove the link)"
                    )
                    continue

                if target.startswith("/"):
                    resolved = (ROOT / target.lstrip("/")).resolve()
                else:
                    resolved = (path.parent / target).resolve()

                try:
                    resolved.relative_to(ROOT)
                except ValueError:
                    errors.append(
                        f"{relative}:{line_number}: link escapes repository: "
                        f"{raw} (use a path inside the repository)"
                    )
                    continue

                if not resolved.exists():
                    errors.append(
                        f"{relative}:{line_number}: broken relative link: {raw} "
                        "(check the target path and filename)"
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
