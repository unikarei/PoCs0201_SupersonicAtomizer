"""Tests: P23-T03 — CaseStore — create / list / load / save / delete.

All tests use a temporary directory via ``tmp_path`` so no real ``cases/``
directory is touched.  Tests cover:
- round-trip create → load → save → load persistence,
- list_cases ordering and empty-dir edge case,
- invalid-name rejection (CaseNameError),
- missing-case rejection (CaseNotFoundError),
- duplicate-create rejection (FileExistsError),
- exists() and case_path() helpers,
- delete() happy path and not-found path,
- template seeding via create(template=...),
- the default template matches the expected minimal structure,
- the saved YAML is loadable by config/loader.py (integration check).
"""

from __future__ import annotations

import pytest

from supersonic_atomizer.gui.case_store import (
    CaseNameError,
    CaseNotFoundError,
    CasePersistenceError,
    CaseStore,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def store(tmp_path):
    """A CaseStore whose cases_dir lives inside the pytest tmp_path."""
    cases_dir = tmp_path / "cases"
    return CaseStore(cases_dir=cases_dir)


# ── cases_dir property ────────────────────────────────────────────────────────


def test_cases_dir_property(store, tmp_path):
    assert store.cases_dir == tmp_path / "cases"


# ── create ────────────────────────────────────────────────────────────────────


def test_create_returns_path(store, tmp_path):
    path = store.create("alpha")
    assert path == tmp_path / "cases" / "alpha.yaml"


def test_create_makes_file(store, tmp_path):
    store.create("alpha")
    assert (tmp_path / "cases" / "alpha.yaml").is_file()


def test_create_makes_cases_dir(store, tmp_path):
    store.create("alpha")
    assert (tmp_path / "cases").is_dir()


def test_create_default_template_has_required_sections(store):
    store.create("alpha")
    cfg = store.load("alpha")
    for section in ("fluid", "boundary_conditions", "geometry",
                    "droplet_injection", "models", "outputs"):
        assert section in cfg, f"Missing section: {section}"


def test_create_duplicate_raises_file_exists_error(store):
    store.create("alpha")
    with pytest.raises(FileExistsError, match="already exists"):
        store.create("alpha")


def test_create_with_custom_template(store):
    template = {"fluid": {"working_fluid": "steam"}, "custom": True}
    store.create("beta", template=template)
    cfg = store.load("beta")
    assert cfg["fluid"]["working_fluid"] == "steam"
    assert cfg["custom"] is True


# ── list_cases ────────────────────────────────────────────────────────────────


def test_list_cases_empty_when_dir_absent(store):
    assert store.list_cases() == []


def test_list_cases_returns_sorted_names(store):
    for name in ("charlie", "alpha", "bravo"):
        store.create(name)
    assert store.list_cases() == ["alpha", "bravo", "charlie"]


def test_list_cases_excludes_non_yaml_files(store, tmp_path):
    cases_dir = tmp_path / "cases"
    cases_dir.mkdir()
    (cases_dir / "alpha.yaml").write_text("fluid:\n  working_fluid: air\n")
    (cases_dir / "readme.txt").write_text("not a case")
    assert store.list_cases() == ["alpha"]


# ── load ──────────────────────────────────────────────────────────────────────


def test_load_returns_dict(store):
    store.create("alpha")
    cfg = store.load("alpha")
    assert isinstance(cfg, dict)


def test_load_missing_case_raises_case_not_found_error(store):
    with pytest.raises(CaseNotFoundError):
        store.load("nonexistent")


def test_load_preserves_values(store):
    template = {"fluid": {"working_fluid": "steam"}}
    store.create("gamma", template=template)
    cfg = store.load("gamma")
    assert cfg["fluid"]["working_fluid"] == "steam"


# ── save ──────────────────────────────────────────────────────────────────────


def test_save_creates_new_file(store):
    cfg = {"fluid": {"working_fluid": "air"}}
    store.save("delta", cfg)
    assert store.exists("delta")


def test_save_overwrites_existing(store):
    store.create("alpha")
    updated = store.load("alpha")
    updated["fluid"]["working_fluid"] = "steam"
    store.save("alpha", updated)
    reloaded = store.load("alpha")
    assert reloaded["fluid"]["working_fluid"] == "steam"


def test_save_returns_path(store, tmp_path):
    path = store.save("epsilon", {"fluid": {"working_fluid": "air"}})
    assert path == tmp_path / "cases" / "epsilon.yaml"


# ── Round-trip ────────────────────────────────────────────────────────────────


def test_round_trip_create_load_modify_save_load(store):
    store.create("roundtrip")
    cfg = store.load("roundtrip")
    cfg["boundary_conditions"]["Pt_in"] = 300_000.0
    store.save("roundtrip", cfg)
    reloaded = store.load("roundtrip")
    assert reloaded["boundary_conditions"]["Pt_in"] == pytest.approx(300_000.0)


# ── delete ────────────────────────────────────────────────────────────────────


def test_delete_removes_file(store):
    store.create("alpha")
    store.delete("alpha")
    assert not store.exists("alpha")


def test_delete_updates_list(store):
    store.create("alpha")
    store.create("bravo")
    store.delete("alpha")
    assert store.list_cases() == ["bravo"]


def test_delete_missing_raises_case_not_found_error(store):
    with pytest.raises(CaseNotFoundError):
        store.delete("nonexistent")


# ── exists / case_path ────────────────────────────────────────────────────────


def test_exists_returns_false_before_create(store):
    assert not store.exists("alpha")


def test_exists_returns_true_after_create(store):
    store.create("alpha")
    assert store.exists("alpha")


def test_case_path_returns_expected_path(store, tmp_path):
    path = store.case_path("alpha")
    assert path == tmp_path / "cases" / "alpha.yaml"


# ── CaseNameError ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("bad_name", [
    "",
    "has space",
    "has/slash",
    "has\\backslash",
    "has.dot",
    "a" * 129,
    "../traversal",
])
def test_invalid_names_raise_case_name_error(store, bad_name):
    with pytest.raises(CaseNameError):
        store.create(bad_name)


@pytest.mark.parametrize("good_name", [
    "alpha",
    "case_001",
    "case-002",
    "CamelCase",
    "A" * 128,
])
def test_valid_names_are_accepted(store, good_name):
    path = store.create(good_name)
    assert path.is_file()


# ── config/loader.py integration ──────────────────────────────────────────────


def test_saved_yaml_is_loadable_by_config_loader(store):
    """A case written by CaseStore must be parseable by the existing loader."""
    from supersonic_atomizer.config import load_raw_case_config

    path = store.create("loader_compat")
    raw = load_raw_case_config(str(path))
    assert isinstance(raw, dict)
    assert "fluid" in raw


def test_saved_custom_config_is_loadable_by_config_loader(store):
    """A custom config dict persisted via save() must survive the loader round-trip."""
    from supersonic_atomizer.config import load_raw_case_config

    cfg = {
        "fluid": {"working_fluid": "steam"},
        "boundary_conditions": {"Pt_in": 300_000.0, "Tt_in": 500.0, "Ps_out": 150_000.0},
    }
    path = store.save("steam_compat", cfg)
    raw = load_raw_case_config(str(path))
    assert raw["fluid"]["working_fluid"] == "steam"
    assert raw["boundary_conditions"]["Pt_in"] == pytest.approx(300_000.0)
