"""Dependency policy gate: every locked third-party package must be allowed by licence and scope.

Two rules, both read from ``[tool.wingbeat.dependency-policy]`` in the root ``pyproject.toml``:

* **Scope (ADR-0002).** No machine-learning frameworks or model-API clients may appear anywhere
  in ``uv.lock``, not even as transitive dependencies.
* **Licence.** The licence of every installed third-party distribution must evaluate to an
  allowed SPDX identifier. Expressions such as ``Apache-2.0 OR BSD-2-Clause`` are evaluated;
  legacy ``License`` fields and trove classifiers are normalised first.

Run with ``uv run python tools/dependency_policy.py``. Exits non-zero on any violation.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

_TOKEN = re.compile(r"\(|\)|[^\s()]+")
#: A legacy ``License`` field longer than this is licence text, not an identifier.
_MAX_LICENCE_NAME_LENGTH = 40

#: Trove classifiers and free-text ``License`` values mapped to SPDX identifiers.
LEGACY_LICENCE_NAMES: dict[str, str] = {
    "license :: osi approved :: mit license": "MIT",
    "license :: osi approved :: mit no attribution license (mit-0)": "MIT-0",
    "license :: osi approved :: bsd license": "BSD-3-Clause",
    "license :: osi approved :: apache software license": "Apache-2.0",
    "license :: osi approved :: mozilla public license 2.0 (mpl 2.0)": "MPL-2.0",
    "license :: osi approved :: python software foundation license": "PSF-2.0",
    "license :: osi approved :: isc license (iscl)": "ISC",
    "license :: osi approved :: the unlicense (unlicense)": "Unlicense",
    "license :: osi approved :: zlib/libpng license": "Zlib",
    "license :: cc0 1.0 universal (cc0 1.0) public domain dedication": "CC0-1.0",
    "mit": "MIT",
    "mit license": "MIT",
    "bsd": "BSD-3-Clause",
    "bsd license": "BSD-3-Clause",
    "new bsd": "BSD-3-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "3-clause bsd": "BSD-3-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "apache 2.0": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "apache software license": "Apache-2.0",
    "mpl-2.0": "MPL-2.0",
    "mpl 2.0": "MPL-2.0",
    "psf": "PSF-2.0",
    "psf-2.0": "PSF-2.0",
    "isc": "ISC",
}


@dataclass(frozen=True)
class Policy:
    """The allowed licences, the denied packages and the per-package licence overrides."""

    allowed_licences: frozenset[str]
    denied_packages: frozenset[str]
    denied_prefixes: tuple[str, ...]
    licence_overrides: dict[str, str]


@dataclass(frozen=True)
class LockedPackage:
    """A third-party package pinned in ``uv.lock``."""

    name: str
    version: str


@dataclass(frozen=True)
class Violation:
    """One broken rule, with enough context to act on it."""

    package: str
    rule: str
    detail: str


def normalise_name(name: str) -> str:
    """Return the PEP 503 normalised form of a distribution name."""
    return re.sub(r"[-_.]+", "-", name).lower()


def load_policy(pyproject: Path) -> Policy:
    """Read the policy table from a ``pyproject.toml`` file.

    Args:
        pyproject: Path to the workspace root ``pyproject.toml``.

    Returns:
        The parsed policy.

    Raises:
        KeyError: If the ``[tool.wingbeat.dependency-policy]`` table is missing.
    """
    table: dict[str, Any] = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    raw = table["tool"]["wingbeat"]["dependency-policy"]
    return Policy(
        allowed_licences=frozenset(raw["allowed-licences"]),
        denied_packages=frozenset(normalise_name(n) for n in raw["denied-packages"]),
        denied_prefixes=tuple(normalise_name(p) for p in raw.get("denied-prefixes", [])),
        licence_overrides={
            normalise_name(k): v for k, v in raw.get("licence-overrides", {}).items()
        },
    )


def locked_third_party_packages(lockfile: Path) -> list[LockedPackage]:
    """List the third-party packages pinned in ``uv.lock``, skipping workspace members.

    Args:
        lockfile: Path to ``uv.lock``.

    Returns:
        Packages from a registry, sorted by name.
    """
    lock: dict[str, Any] = tomllib.loads(lockfile.read_text(encoding="utf-8"))
    packages = [
        LockedPackage(normalise_name(p["name"]), p.get("version", "?"))
        for p in lock.get("package", [])
        if "registry" in p.get("source", {})
    ]
    return sorted(packages, key=lambda p: p.name)


def is_denied(name: str, policy: Policy) -> bool:
    """Tell whether a package name is on the scope deny-list."""
    normalised = normalise_name(name)
    return normalised in policy.denied_packages or any(
        normalised == prefix or normalised.startswith(f"{prefix}-")
        for prefix in policy.denied_prefixes
    )


def licence_from_metadata(dist_metadata: metadata.PackageMetadata) -> str | None:
    """Extract the best available licence expression from distribution metadata.

    Prefers the PEP 639 ``License-Expression`` field, then a short legacy ``License`` field,
    then trove classifiers (joined with ``AND``, since all of them apply).

    Args:
        dist_metadata: Metadata of an installed distribution.

    Returns:
        An SPDX expression, or ``None`` if nothing usable is declared.
    """
    expression = dist_metadata.get("License-Expression")
    if expression:
        return expression.strip()
    legacy = (dist_metadata.get("License") or "").strip()
    if legacy and "\n" not in legacy and len(legacy) <= _MAX_LICENCE_NAME_LENGTH:
        return LEGACY_LICENCE_NAMES.get(legacy.lower(), legacy)
    classifiers = [
        LEGACY_LICENCE_NAMES[c.lower()]
        for c in dist_metadata.get_all("Classifier") or []
        if c.lower() in LEGACY_LICENCE_NAMES
    ]
    if classifiers:
        return " AND ".join(dict.fromkeys(classifiers))
    return None


def expression_is_allowed(expression: str, allowed: frozenset[str]) -> bool:
    """Evaluate an SPDX licence expression against an allow-list.

    ``OR`` needs one allowed side, ``AND`` needs both, parentheses group, and ``WITH``
    exceptions are allowed only when the full ``<licence> WITH <exception>`` text is listed.

    Args:
        expression: An SPDX licence expression such as ``Apache-2.0 OR BSD-2-Clause``.
        allowed: Allowed SPDX identifiers.

    Returns:
        True when the expression is satisfiable with allowed licences only.

    Raises:
        ValueError: If the expression is malformed.
    """
    tokens: list[str] = _TOKEN.findall(expression)
    position = 0

    def peek() -> str | None:
        return tokens[position] if position < len(tokens) else None

    def take() -> str:
        nonlocal position
        if position >= len(tokens):
            msg = f"unexpected end of licence expression: {expression!r}"
            raise ValueError(msg)
        token = tokens[position]
        position += 1
        return token

    def atom() -> bool:
        lexeme = take()
        if lexeme == "(":
            value = disjunction()
            if take() != ")":
                msg = f"unbalanced parentheses in {expression!r}"
                raise ValueError(msg)
            return value
        if peek() == "WITH":
            take()
            return f"{lexeme} WITH {take()}" in allowed
        return lexeme in allowed

    def conjunction() -> bool:
        value = atom()
        while peek() == "AND":
            take()
            value = atom() and value
        return value

    def disjunction() -> bool:
        value = conjunction()
        while peek() == "OR":
            take()
            value = conjunction() or value
        return value

    result = disjunction()
    if position != len(tokens):
        msg = f"trailing tokens in licence expression: {expression!r}"
        raise ValueError(msg)
    return result


def check(packages: list[LockedPackage], policy: Policy) -> list[Violation]:
    """Apply the scope and licence rules to every locked package.

    Args:
        packages: Third-party packages from the lockfile.
        policy: The policy to enforce.

    Returns:
        Every violation found; empty when the lockfile complies.
    """
    violations: list[Violation] = []
    for package in packages:
        if is_denied(package.name, policy):
            violations.append(
                Violation(package.name, "scope", "ML or model-API package (see ADR-0002)")
            )
            continue
        licence = policy.licence_overrides.get(package.name)
        if licence is None:
            try:
                licence = licence_from_metadata(metadata.metadata(package.name))
            except metadata.PackageNotFoundError:
                violations.append(
                    Violation(
                        package.name,
                        "licence",
                        "not installed on this platform: run `uv sync --locked`, or add a "
                        "verified entry to licence-overrides for platform-specific packages",
                    )
                )
                continue
        if licence is None:
            violations.append(Violation(package.name, "licence", "no licence metadata"))
            continue
        try:
            allowed = expression_is_allowed(licence, policy.allowed_licences)
        except ValueError as error:
            violations.append(Violation(package.name, "licence", str(error)))
            continue
        if not allowed:
            violations.append(Violation(package.name, "licence", f"{licence} is not allowed"))
    return violations


def main(argv: list[str] | None = None) -> int:
    """Run the gate and print a report. Returns the process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    policy = load_policy(args.root / "pyproject.toml")
    packages = locked_third_party_packages(args.root / "uv.lock")
    violations = check(packages, policy)
    for violation in violations:
        print(f"FAIL {violation.package}: [{violation.rule}] {violation.detail}")
    print(f"{len(packages)} third-party packages checked, {len(violations)} violation(s).")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
