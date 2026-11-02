"""Validate reference/species.yaml: JSON Schema first, then the rules a schema cannot express."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
TABLE_PATH = ROOT / "reference" / "species.yaml"
SCHEMA_PATH = ROOT / "reference" / "species.schema.json"


@pytest.fixture(scope="module")
def table() -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load(TABLE_PATH.read_text(encoding="utf-8"))
    return loaded


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return loaded


def cited_sources(table: dict[str, Any]) -> list[str]:
    keys = [table["temperature_correction"]["default"]["source"]]
    for species in table["species"]:
        for field in ("measurements", "temperature_slopes", "convergence"):
            keys += [entry["source"] for entry in species.get(field, [])]
    return keys


def test_schema_is_a_valid_draft_2020_12_schema(schema: dict[str, Any]) -> None:
    Draft202012Validator.check_schema(schema)


def test_table_matches_schema(table: dict[str, Any], schema: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(table), key=lambda e: e.path)
    assert not errors, "\n".join(f"{list(e.path)}: {e.message}" for e in errors)


def test_every_cited_source_is_defined(table: dict[str, Any]) -> None:
    assert set(cited_sources(table)) <= set(table["sources"])


def test_every_defined_source_is_cited(table: dict[str, Any]) -> None:
    assert set(table["sources"]) <= set(cited_sources(table))


def test_species_ids_and_taxon_keys_are_unique(table: dict[str, Any]) -> None:
    ids = Counter(s["id"] for s in table["species"])
    keys = Counter(s["gbif_taxon_key"] for s in table["species"])
    assert [i for i, n in ids.items() if n > 1] == []
    assert [k for k, n in keys.items() if n > 1] == []


def test_ids_derive_from_scientific_names(table: dict[str, Any]) -> None:
    for species in table["species"]:
        assert species["id"] == species["scientific_name"].lower().replace(" ", "-")


def test_status_matches_evidence(table: dict[str, Any]) -> None:
    for species in table["species"]:
        if species["status"] == "measured":
            assert species["measurements"], f"{species['id']} is measured but has no values"
        else:
            assert not species["measurements"], f"{species['id']} is unknown but has values"
            assert species.get("notes"), f"{species['id']} must say what is missing"


def test_ranges_are_ordered(table: dict[str, Any]) -> None:
    low, high = table["temperature_correction"]["default"]["valid_range_c"]
    assert low < high
    for species in table["species"]:
        for slope in species.get("temperature_slopes", []):
            assert slope["min_hz_per_c"] <= slope["max_hz_per_c"]
        for band in species.get("convergence", []):
            assert band["band_hz"][0] < band["band_hz"][1]


def test_tolerance_present_only_with_a_temperature(table: dict[str, Any]) -> None:
    for species in table["species"]:
        for m in species["measurements"]:
            if m["temperature_c"] is None:
                assert m["temperature_basis"] == "unknown"
                assert m.get("temperature_tolerance_c") is None


def test_reference_temperatures_agree(table: dict[str, Any]) -> None:
    assert (
        table["reference_temperature_c"]
        == table["temperature_correction"]["default"]["reference_temperature_c"]
    )


def test_default_correction_reproduces_the_published_anchor(table: dict[str, Any]) -> None:
    # Saha et al. 2024 report about 9.63 Hz/°C at 525 Hz from their cluster fits; Eq. 3 is the
    # general fit across clusters, so it should land close to that anchor.
    correction = table["temperature_correction"]["default"]
    slope = correction["quadratic"] * 525.0**2 + correction["linear"] * 525.0
    assert slope == pytest.approx(9.63, abs=0.1)


def test_dois_are_unique(table: dict[str, Any]) -> None:
    dois = Counter(s["doi"].lower() for s in table["sources"].values())
    assert [d for d, n in dois.items() if n > 1] == []


def test_source_keys_name_first_author_and_year(table: dict[str, Any]) -> None:
    for key, source in table["sources"].items():
        author, year = re.fullmatch(r"([a-z]+)(\d{4})[a-z]?", key).groups()  # type: ignore[union-attr]
        assert source["citation"].lower().startswith(author), key
        assert f"({year})" in source["citation"], key


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("locator", None),
        ("source", "Not A Key"),
        ("mean_hz", 5.0),
        ("modality", "guess"),
        ("temperature_basis", "assumed"),
    ],
)
def test_schema_rejects_uncited_or_invalid_measurements(
    table: dict[str, Any], schema: dict[str, Any], field: str, value: object
) -> None:
    broken = json.loads(json.dumps(table))
    measurement = broken["species"][0]["measurements"][0]
    if value is None:
        del measurement[field]
    else:
        measurement[field] = value
    assert not Draft202012Validator(schema).is_valid(broken)
