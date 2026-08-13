#!/usr/bin/env python3
"""Course content validator for the GitHub Actions Enablement Course.

Author: Pandiyaraj Karuppasamy
Date: Aug-13-2026

This script is the single source of truth for the action-version pin table that
``CLAUDE.md`` documents in prose. ``.github/workflows/validate.yml`` runs it on every
push so course content cannot drift from the versions it claims to teach.

Checks
------
``pins``
    Every ``uses:`` reference to an action in :data:`PINNED_ACTIONS` uses the pinned
    major version.
``mutable``
    No action is referenced by a mutable ref (``@main``, ``@master``, ``@HEAD``, or a
    bare branch name), unless allowlisted in :data:`MUTABLE_REF_ALLOWLIST`. Version
    tags and full SHAs are both acceptable.
``links``
    Every relative markdown link resolves to a file that exists. External URLs are
    skipped -- network flakiness in CI says nothing about the content.
``structure``
    Every ``modules/module-NN-*.md`` file contains all of :data:`REQUIRED_SECTIONS`
    as level-2 headings.
``pairing``
    Every module has a paired ``examples/`` workflow and ``solutions/`` answer file.

Usage
-----
::

    python scripts/validate_course.py                    # all checks
    python scripts/validate_course.py --check pins       # one check
    python scripts/validate_course.py --print-pins       # emit the table as markdown
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------------------
# Policy tables
# --------------------------------------------------------------------------------------

#: Actions whose major version is fixed course-wide. Keyed by the full action path
#: (including any sub-path, e.g. ``github/codeql-action/init``) mapped to the required
#: major version tag. Mirrored in prose in ``CLAUDE.md`` -- update both together.
PINNED_ACTIONS: dict[str, str] = {
    # First-party
    "actions/checkout": "v7",
    "actions/setup-python": "v7",
    "actions/upload-artifact": "v7",
    "actions/download-artifact": "v8",
    "actions/cache": "v6",
    "actions/github-script": "v9",
    "actions/configure-pages": "v6",
    "actions/upload-pages-artifact": "v5",
    "actions/deploy-pages": "v5",
    # Third-party
    "docker/login-action": "v4",
    "docker/setup-buildx-action": "v4",
    "docker/setup-qemu-action": "v4",
    "docker/metadata-action": "v6",
    "docker/build-push-action": "v7",
}

#: Refs that are mutable and therefore unacceptable for any action. A course that tells
#: learners to pin must not itself float on a branch.
MUTABLE_REFS: frozenset[str] = frozenset({"main", "master", "HEAD", "develop", "latest"})

#: Action paths knowingly allowed to float on a mutable ref, with the reason. These are
#: deliberate exceptions, not oversights -- the tradeoff is that whoever controls the
#: upstream branch gets code execution in any workflow that runs the action. Anything
#: added here should be called out in the module that teaches pinning.
MUTABLE_REF_ALLOWLIST: dict[str, str] = {
    "trufflesecurity/trufflehog": (
        "upstream publishes frequently and recommends @main; kept unpinned for "
        "maintenance simplicity"
    ),
}

#: Level-2 headings every module file must contain, in no particular order. The teaching
#: template is what makes 20+ modules feel like one course rather than 20 blog posts.
REQUIRED_SECTIONS: tuple[str, ...] = (
    "Learning Objectives",
    "Key Concepts",
    "Expected Outcome",
    "Concept Flow",
    "ELI5 Explanation",
    "Technical Explanation",
    "Real-World Use Case",
    "When To Use",
    "When NOT To Use",
    "Common Mistakes",
    "Debugging Tips",
    "Minimal Workflow Example",
    "Production Workflow Example",
    "Quiz",
    "Labs",
)

#: Directories scanned for standalone workflow YAML.
YAML_SEARCH_DIRS: tuple[str, ...] = (".github", "examples", "advanced")

#: Directories scanned for YAML embedded in fenced markdown code blocks. Most course
#: YAML lives in prose, so skipping these would leave the majority unvalidated.
MARKDOWN_SEARCH_DIRS: tuple[str, ...] = (
    "modules",
    "case-studies",
    "reference",
    "advanced",
    "capstones",
    "assessments",
    "solutions",
)

#: An opening ```yaml fence. Closing fences are matched by length-agnostic ``` lookup.
YAML_FENCE_RE = re.compile(r"^\s*```+\s*(?:ya?ml|github-actions-workflow)\s*$", re.IGNORECASE)

#: Any closing fence.
FENCE_END_RE = re.compile(r"^\s*```+\s*$")

#: ``uses:`` lines, tolerating list-item dashes and quoted values.
USES_RE = re.compile(r"""^\s*(?:-\s*)?uses:\s*['"]?([^'"\s#]+)['"]?""")

#: An action reference split into path and ref.
ACTION_REF_RE = re.compile(r"^(?P<path>[^@]+)@(?P<ref>.+)$")

#: A level-2 markdown heading.
H2_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)

#: ``modules/module-07-jobs-and-steps.md`` -> ``07``
MODULE_FILE_RE = re.compile(r"^module-(?P<number>\d{2})-(?P<slug>.+)\.md$")

#: An inline markdown link, ``[text](target)``. Nested brackets in link text are rare
#: enough in this repo not to warrant a real parser.
MD_LINK_RE = re.compile(r"\[[^\]]*\]\((?P<target>[^)]+)\)")

#: An action reference written as inline code in prose, e.g. ``` `actions/cache@v6` ```.
#: Requires an owner/name@ref shape so ordinary inline code is not matched.
INLINE_ACTION_RE = re.compile(
    r"`(?P<ref>[A-Za-z0-9._-]+/[A-Za-z0-9._/-]+@[A-Za-z0-9._-]+)`"
)


# --------------------------------------------------------------------------------------
# Result plumbing
# --------------------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Outcome of a single named check.

    Attributes:
        name: Check identifier as passed to ``--check``.
        failures: Human-readable failure lines, each prefixed with ``path:line`` where
            a specific location is known.
        scanned: Count of files or items inspected, for the summary line.
    """

    name: str
    failures: list[str] = field(default_factory=list)
    scanned: int = 0

    @property
    def ok(self) -> bool:
        """Whether the check passed."""
        return not self.failures


def _relative(path: Path) -> str:
    """Return ``path`` relative to the repo root using forward slashes."""
    return path.relative_to(REPO_ROOT).as_posix()


def _iter_yaml_files() -> list[Path]:
    """Return every workflow YAML file under :data:`YAML_SEARCH_DIRS`, sorted."""
    found: list[Path] = []
    for directory in YAML_SEARCH_DIRS:
        base = REPO_ROOT / directory
        if not base.is_dir():
            continue
        for pattern in ("**/*.yml", "**/*.yaml"):
            found.extend(base.glob(pattern))
    return sorted(set(found))


def _iter_module_files() -> list[Path]:
    """Return every ``modules/module-NN-*.md`` file, sorted by module number."""
    modules_dir = REPO_ROOT / "modules"
    if not modules_dir.is_dir():
        return []
    return sorted(
        (path for path in modules_dir.glob("module-*.md") if MODULE_FILE_RE.match(path.name)),
        key=lambda path: path.name,
    )


def _iter_markdown_files() -> list[Path]:
    """Return every markdown file that may embed workflow YAML, sorted."""
    found: list[Path] = []
    for directory in MARKDOWN_SEARCH_DIRS:
        base = REPO_ROOT / directory
        if base.is_dir():
            found.extend(base.glob("**/*.md"))
    root_readme = REPO_ROOT / "README.md"
    if root_readme.is_file():
        found.append(root_readme)
    return sorted(set(found))


def _scannable_lines(path: Path) -> list[tuple[int, str]]:
    """Return the ``(line_number, text)`` pairs of ``path`` that may hold workflow YAML.

    For ``.yml``/``.yaml`` files every line qualifies. For markdown, only lines inside a
    fenced YAML block qualify, so prose mentioning ``uses:`` is not misread as policy.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if path.suffix.lower() in {".yml", ".yaml"}:
        return list(enumerate(lines, start=1))

    scannable: list[tuple[int, str]] = []
    in_yaml_fence = False
    for lineno, line in enumerate(lines, start=1):
        if not in_yaml_fence:
            if YAML_FENCE_RE.match(line):
                in_yaml_fence = True
            continue
        if FENCE_END_RE.match(line):
            in_yaml_fence = False
            continue
        scannable.append((lineno, line))
    return scannable


def _iter_action_refs(path: Path) -> list[tuple[int, str]]:
    """Extract ``(line_number, action_reference)`` pairs from a YAML or markdown file.

    Local action references (those beginning with ``./``) and docker image references
    (``docker://``) are skipped -- neither is version-pinned by this policy.
    """
    refs: list[tuple[int, str]] = []
    for lineno, line in _scannable_lines(path):
        match = USES_RE.match(line)
        if not match:
            continue
        value = match.group(1)
        if value.startswith(("./", "../", "docker://")):
            continue
        refs.append((lineno, value))
    return refs


def _iter_workflow_sources() -> list[Path]:
    """Return every file the pin and mutable-ref checks inspect."""
    return sorted(set(_iter_yaml_files()) | set(_iter_markdown_files()))


# --------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------


def _iter_prose_action_refs(path: Path) -> list[tuple[int, str]]:
    """Extract action references from markdown reference **tables**.

    A version quoted in a "use this action" table is never executed, so nothing
    catches it when it goes stale -- that is how ``docker/login-action@v3`` survived
    in the cheat sheet after the pin moved to v4. This is the documentation half of
    the pin check; :func:`_iter_action_refs` covers the executable half.

    Only table rows are inspected. Ordinary prose routinely discusses versions
    *historically* -- "``actions/checkout@v3`` lints clean", "from
    ``upload-artifact@v4`` onward artifacts are immutable" -- and those references
    are deliberately not the pinned version, so enforcing them would be wrong.
    A table row may opt out with a trailing ``<!-- pin-exempt -->`` marker.
    """
    if path.suffix.lower() != ".md":
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    refs: list[tuple[int, str]] = []
    in_fence = False
    for lineno, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        # A table row: starts and ends with a pipe. Not a separator row.
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        if set(stripped) <= set("|- :"):
            continue
        if "pin-exempt" in stripped:
            continue
        for match in INLINE_ACTION_RE.finditer(line):
            refs.append((lineno, match.group("ref")))
    return refs


def check_pins() -> CheckResult:
    """Verify pinned actions use their required major version.

    Covers both executable references (``uses:`` in YAML and fenced YAML) and
    versions quoted as inline code in prose, which drift silently because nothing
    runs them.
    """
    result = CheckResult(name="pins")
    for path in _iter_workflow_sources():
        result.scanned += 1
        for lineno, reference in _iter_prose_action_refs(path):
            parsed = ACTION_REF_RE.match(reference)
            if not parsed:
                continue
            required = PINNED_ACTIONS.get(parsed.group("path"))
            if required is not None and parsed.group("ref") != required:
                result.failures.append(
                    f"{_relative(path)}:{lineno}: prose mentions "
                    f"`{reference}` but the pinned version is "
                    f"`{parsed.group('path')}@{required}`"
                )
        for lineno, reference in _iter_action_refs(path):
            parsed = ACTION_REF_RE.match(reference)
            if not parsed:
                result.failures.append(
                    f"{_relative(path)}:{lineno}: `{reference}` has no `@ref` -- "
                    "every action must specify a version"
                )
                continue
            action_path = parsed.group("path")
            ref = parsed.group("ref")
            required = PINNED_ACTIONS.get(action_path)
            if required is None:
                continue
            if ref != required:
                result.failures.append(
                    f"{_relative(path)}:{lineno}: `{action_path}@{ref}` should be "
                    f"`{action_path}@{required}`"
                )
    return result


def check_mutable() -> CheckResult:
    """Verify no action is referenced by a mutable branch ref."""
    result = CheckResult(name="mutable")
    for path in _iter_workflow_sources():
        result.scanned += 1
        for lineno, reference in _iter_action_refs(path):
            parsed = ACTION_REF_RE.match(reference)
            if not parsed:
                continue
            action_path = parsed.group("path")
            ref = parsed.group("ref")
            if ref not in MUTABLE_REFS:
                continue
            if action_path in MUTABLE_REF_ALLOWLIST:
                continue
            result.failures.append(
                f"{_relative(path)}:{lineno}: `{reference}` uses the mutable ref "
                f"`@{ref}` -- pin to a version tag or a full commit SHA, or add an "
                "entry to MUTABLE_REF_ALLOWLIST with a stated reason"
            )
    return result


def check_structure() -> CheckResult:
    """Verify every module file contains all required level-2 sections."""
    result = CheckResult(name="structure")
    for path in _iter_module_files():
        result.scanned += 1
        headings = {match.group("title").strip() for match in H2_RE.finditer(
            path.read_text(encoding="utf-8")
        )}
        # Headings may carry trailing punctuation or inline code; compare on a
        # normalised form so `## The \`on\` Section` style titles still match.
        normalised = {re.sub(r"[`*_]", "", heading) for heading in headings}
        missing = [
            section
            for section in REQUIRED_SECTIONS
            if not any(section.lower() in heading.lower() for heading in normalised)
        ]
        if missing:
            result.failures.append(
                f"{_relative(path)}: missing section(s): {', '.join(missing)}"
            )
    return result


def _iter_yaml_blocks(path: Path) -> list[tuple[int, str]]:
    """Return ``(start_line, block_text)`` for every fenced YAML block in a markdown file.

    Blocks whose first non-blank line is indented are skipped: those are fragments
    of a larger document (a bare ``steps:`` list, say) rather than standalone YAML,
    and parsing them in isolation reports errors that are not real.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[tuple[int, str]] = []
    start: int | None = None
    body: list[str] = []
    for lineno, line in enumerate(lines, start=1):
        if start is None:
            if YAML_FENCE_RE.match(line):
                start, body = lineno + 1, []
            continue
        if FENCE_END_RE.match(line):
            first = next((item for item in body if item.strip()), "")
            if first and not first[0].isspace():
                blocks.append((start, "\n".join(body)))
            start = None
            continue
        body.append(line)
    return blocks


def check_yaml_blocks() -> CheckResult:
    """Verify every standalone fenced YAML block in the docs actually parses.

    Catches the class of defect that a ``uses:`` grep cannot: an unquoted scalar
    containing ``": "``, or a ``${{ }}`` expression at column 0 terminating a block
    scalar. Both make a real workflow invalid, and both look fine when skimmed.
    """
    result = CheckResult(name="yaml-blocks")
    try:
        import yaml
    except ImportError:  # pragma: no cover - PyYAML is a documented requirement
        result.failures.append(
            "PyYAML is not installed; run `pip install pyyaml` to enable this check"
        )
        return result

    for path in _iter_markdown_files():
        result.scanned += 1
        for start_line, block in _iter_yaml_blocks(path):
            try:
                yaml.safe_load(block)
            except yaml.YAMLError as exc:
                detail = " ".join(str(exc).split())
                result.failures.append(
                    f"{_relative(path)}:{start_line}: YAML block does not parse -- {detail}"
                )
    return result


def check_links() -> CheckResult:
    """Verify every relative markdown link resolves to a file that exists.

    Only repo-relative links are checked. External URLs are deliberately skipped --
    network flakiness in CI produces failures that say nothing about the content.
    """
    result = CheckResult(name="links")
    for path in _iter_markdown_files():
        result.scanned += 1
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in MD_LINK_RE.finditer(line):
                target = match.group("target").strip()
                if not target or target.startswith(
                    ("http://", "https://", "mailto:", "#", "<")
                ):
                    continue
                # Strip any anchor; we verify the file exists, not the heading.
                file_part = target.split("#", 1)[0]
                if not file_part:
                    continue
                resolved = (path.parent / file_part).resolve()
                if not resolved.exists():
                    result.failures.append(
                        f"{_relative(path)}:{lineno}: broken link `{target}`"
                    )
    return result


def check_pairing() -> CheckResult:
    """Verify every module has a paired example workflow and solutions file."""
    result = CheckResult(name="pairing")
    examples_dir = REPO_ROOT / "examples"
    solutions_dir = REPO_ROOT / "solutions"
    for path in _iter_module_files():
        result.scanned += 1
        match = MODULE_FILE_RE.match(path.name)
        if match is None:  # pragma: no cover - guarded by _iter_module_files
            continue
        number = match.group("number")
        if not list(examples_dir.glob(f"module-{number}-*.yml")):
            result.failures.append(
                f"{_relative(path)}: no paired workflow at examples/module-{number}-*.yml"
            )
        if not list(solutions_dir.glob(f"module-{number}-*.md")):
            result.failures.append(
                f"{_relative(path)}: no paired answers at solutions/module-{number}-*.md"
            )
    return result


CHECKS = {
    "pins": check_pins,
    "mutable": check_mutable,
    "yaml-blocks": check_yaml_blocks,
    "links": check_links,
    "structure": check_structure,
    "pairing": check_pairing,
}


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def print_pins() -> None:
    """Emit the pin table as markdown, for pasting into documentation."""
    print("| Action | Pinned major version |")
    print("| --- | --- |")
    for action, version in PINNED_ACTIONS.items():
        print(f"| `{action}` | `{version}` |")


def main(argv: list[str] | None = None) -> int:
    """Run the requested checks and return a process exit code.

    Args:
        argv: Argument vector, defaulting to ``sys.argv[1:]``.

    Returns:
        ``0`` when every requested check passes, ``1`` otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="append",
        choices=sorted(CHECKS),
        help="Run only the named check. Repeatable. Defaults to all checks.",
    )
    parser.add_argument(
        "--print-pins",
        action="store_true",
        help="Print the action pin table as markdown and exit.",
    )
    args = parser.parse_args(argv)

    if args.print_pins:
        print_pins()
        return 0

    selected = args.check or sorted(CHECKS)
    results = [CHECKS[name]() for name in selected]

    failed = 0
    for result in results:
        if result.ok:
            print(f"PASS  {result.name:<10} ({result.scanned} files scanned)")
            continue
        failed += 1
        print(f"FAIL  {result.name:<10} ({len(result.failures)} problem(s))")
        for failure in result.failures:
            print(f"        {failure}")

    print()
    if failed:
        print(f"{failed} of {len(results)} check(s) failed.")
        return 1
    print(f"All {len(results)} check(s) passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
