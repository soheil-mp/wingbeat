from __future__ import annotations

from importlib import metadata
from pathlib import Path
from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

import dependency_policy as dp

ALLOWED = frozenset({"MIT", "Apache-2.0", "BSD-2-Clause", "Apache-2.0 WITH LLVM-exception"})


def make_policy(**overrides: str) -> dp.Policy:
    return dp.Policy(
        allowed_licences=ALLOWED,
        denied_packages=frozenset({"scikit-learn", "openai"}),
        denied_prefixes=("torch", "langchain"),
        licence_overrides=dict(overrides),
    )


class FakeMetadata:
    def __init__(self, fields: dict[str, str], classifiers: list[str] | None = None) -> None:
        self._fields = fields
        self._classifiers = classifiers

    def get(self, name: str) -> str | None:
        return self._fields.get(name)

    def get_all(self, name: str) -> list[str] | None:
        return self._classifiers if name == "Classifier" else None


def as_metadata(fake: FakeMetadata) -> metadata.PackageMetadata:
    return cast("metadata.PackageMetadata", fake)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("Scikit_Learn", "scikit-learn"), ("zope.interface", "zope-interface"), ("a--b__c", "a-b-c")],
)
def test_normalise_name_follows_pep_503(raw: str, expected: str) -> None:
    assert dp.normalise_name(raw) == expected


@pytest.mark.parametrize(
    ("expression", "allowed"),
    [
        ("MIT", True),
        ("GPL-3.0-only", False),
        ("Apache-2.0 OR BSD-2-Clause", True),
        ("GPL-3.0-only OR MIT", True),
        ("MIT AND Apache-2.0", True),
        ("MIT AND GPL-3.0-only", False),
        ("(MIT OR GPL-3.0-only) AND BSD-2-Clause", True),
        ("(GPL-2.0-only OR LGPL-3.0-only) AND MIT", False),
        ("Apache-2.0 WITH LLVM-exception", True),
        ("GPL-2.0-only WITH Classpath-exception-2.0", False),
    ],
)
def test_expression_evaluation(expression: str, allowed: bool) -> None:
    assert dp.expression_is_allowed(expression, ALLOWED) is allowed


@pytest.mark.parametrize("expression", ["(MIT", "(MIT MIT", "MIT)", "MIT OR", ""])
def test_malformed_expressions_raise(expression: str) -> None:
    with pytest.raises(ValueError, match=r"licence expression|parentheses"):
        dp.expression_is_allowed(expression, ALLOWED)


licence_ids = st.sampled_from(["MIT", "Apache-2.0", "GPL-3.0-only", "BSD-2-Clause", "SSPL-1.0"])


@given(st.lists(licence_ids, min_size=1, max_size=6), st.sampled_from(["AND", "OR"]))
def test_flat_expressions_match_any_or_all(ids: list[str], operator: str) -> None:
    expected = (all if operator == "AND" else any)(i in ALLOWED for i in ids)
    assert dp.expression_is_allowed(f" {operator} ".join(ids), ALLOWED) is expected


def test_licence_prefers_pep_639_expression() -> None:
    fake = FakeMetadata({"License-Expression": "Apache-2.0 OR MIT", "License": "BSD"})
    assert dp.licence_from_metadata(as_metadata(fake)) == "Apache-2.0 OR MIT"


def test_short_legacy_licence_is_normalised() -> None:
    assert dp.licence_from_metadata(as_metadata(FakeMetadata({"License": "MIT License"}))) == "MIT"


def test_unknown_short_legacy_licence_is_kept_verbatim() -> None:
    fake = FakeMetadata({"License": "Proprietary"})
    assert dp.licence_from_metadata(as_metadata(fake)) == "Proprietary"


def test_full_licence_text_falls_back_to_classifiers() -> None:
    fake = FakeMetadata(
        {"License": "Copyright (c) someone\nPermission is hereby granted..."},
        ["License :: OSI Approved :: MIT License", "Programming Language :: Python"],
    )
    assert dp.licence_from_metadata(as_metadata(fake)) == "MIT"


def test_several_classifiers_must_all_hold() -> None:
    fake = FakeMetadata(
        {},
        [
            "License :: OSI Approved :: MIT License",
            "License :: OSI Approved :: Apache Software License",
        ],
    )
    assert dp.licence_from_metadata(as_metadata(fake)) == "MIT AND Apache-2.0"


def test_missing_licence_metadata_returns_none() -> None:
    assert dp.licence_from_metadata(as_metadata(FakeMetadata({}, []))) is None


@pytest.mark.parametrize(
    ("name", "denied"),
    [
        ("openai", True),
        ("Scikit_Learn", True),
        ("torch", True),
        ("torch-geometric", True),
        ("langchain-core", True),
        ("torchx-like", False),
        ("numpy", False),
    ],
)
def test_deny_list_matches_names_and_prefixes(name: str, denied: bool) -> None:
    assert dp.is_denied(name, make_policy()) is denied


def test_check_reports_each_kind_of_violation() -> None:
    policy = make_policy(**{"good-pkg": "MIT", "copyleft-pkg": "GPL-3.0-only", "bad": "MIT ("})
    packages = [
        dp.LockedPackage("good-pkg", "1.0"),
        dp.LockedPackage("copyleft-pkg", "1.0"),
        dp.LockedPackage("bad", "1.0"),
        dp.LockedPackage("openai", "1.0"),
        dp.LockedPackage("surely-not-installed-wingbeat-test-pkg", "1.0"),
    ]
    rules = {v.package: v.rule for v in dp.check(packages, policy)}
    assert rules == {
        "copyleft-pkg": "licence",
        "bad": "licence",
        "openai": "scope",
        "surely-not-installed-wingbeat-test-pkg": "licence",
    }


def test_check_reads_installed_metadata() -> None:
    assert dp.check([dp.LockedPackage("pytest", metadata.version("pytest"))], make_policy()) == []


def test_check_flags_packages_without_licence_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(metadata, "metadata", lambda _name: as_metadata(FakeMetadata({}, [])))
    violations = dp.check([dp.LockedPackage("mystery", "1.0")], make_policy())
    assert [(v.package, v.detail) for v in violations] == [("mystery", "no licence metadata")]


LOCK = """
version = 1
[[package]]
name = "wingbeat-dsp"
version = "0.0.0"
source = { editable = "packages/wingbeat-dsp" }

[[package]]
name = "wingbeat"
version = "0.0.0"
source = { virtual = "." }

[[package]]
name = "Pytest"
version = "9.2.0"
source = { registry = "https://pypi.org/simple" }

[[package]]
name = "iniconfig"
version = "2.1.0"
source = { registry = "https://pypi.org/simple" }
"""

PYPROJECT = """
[tool.wingbeat.dependency-policy]
allowed-licences = ["MIT"]
denied-packages = ["OpenAI"]
denied-prefixes = ["torch"]

[tool.wingbeat.dependency-policy.licence-overrides]
Some_Pkg = "MIT"
"""


def test_lockfile_parsing_skips_workspace_members(tmp_path: Path) -> None:
    lockfile = tmp_path / "uv.lock"
    lockfile.write_text(LOCK, encoding="utf-8")
    assert dp.locked_third_party_packages(lockfile) == [
        dp.LockedPackage("iniconfig", "2.1.0"),
        dp.LockedPackage("pytest", "9.2.0"),
    ]


def test_policy_loading_normalises_names(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(PYPROJECT, encoding="utf-8")
    policy = dp.load_policy(pyproject)
    assert policy.denied_packages == frozenset({"openai"})
    assert policy.denied_prefixes == ("torch",)
    assert policy.licence_overrides == {"some-pkg": "MIT"}


def test_main_exit_codes_and_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (tmp_path / "uv.lock").write_text(LOCK, encoding="utf-8")
    assert dp.main(["--root", str(tmp_path)]) == 0
    assert "2 third-party packages checked, 0 violation(s)." in capsys.readouterr().out

    (tmp_path / "uv.lock").write_text(
        LOCK + '\n[[package]]\nname = "openai"\nversion = "1"\nsource = { registry = "x" }\n',
        encoding="utf-8",
    )
    assert dp.main(["--root", str(tmp_path)]) == 1
    assert "FAIL openai: [scope]" in capsys.readouterr().out


def test_repository_lockfile_complies() -> None:
    root = Path(__file__).resolve().parents[2]
    assert dp.main(["--root", str(root)]) == 0
