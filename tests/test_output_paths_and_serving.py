import tempfile
from pathlib import Path

from supersonic_atomizer.io.paths import build_output_metadata, prune_old_output_runs
from supersonic_atomizer.domain import OutputConfig


def make_output_config(tmpdir: Path):
    class _OC:
        output_directory = str(tmpdir / "outputs")
        write_csv = True
        write_json = True
        generate_plots = True

    return _OC()


def test_build_output_metadata_project_case(tmp_path):
    oc = make_output_config(tmp_path)
    meta = build_output_metadata(output_config=oc, run_id="run-fixed", project="ProjA", case_name="CaseX")
    assert "ProjA" in meta.output_directory
    assert "CaseX" in meta.output_directory
    assert meta.run_id == "run-fixed"


def test_prune_old_output_runs_keeps_only_current(tmp_path):
    base = tmp_path / "outputs" / "Proj" / "Case"
    base.mkdir(parents=True)
    # create old run dirs and a current run dir
    old1 = base / "run-20230101T000000Z"
    old2 = base / "run-20230202T000000Z"
    current = base / "run-99999999T000000Z"
    for d in (old1, old2, current):
        p = d
        p.mkdir(parents=True)
        # add dummy file
        (p / "results.csv").write_text("a,b,c")

    class _Meta:
        output_directory = str(current)

    prune_old_output_runs(_Meta())

    remaining = [p.name for p in base.iterdir() if p.is_dir()]
    assert remaining == [current.name]
