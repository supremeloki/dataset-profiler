import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from data_profiler import (
    EmptyDatasetError,
    FileReadError,
    infer_type,
    profile_csv,
    profile_rows,
    summarize_numeric,
)


@pytest.fixture
def sample_rows():
    return [
        {"id": "1", "city": "Karaj", "price": "120.5", "active": "yes", "note": "ok"},
        {"id": "2", "city": "Tehran", "price": "99.9", "active": "no", "note": ""},
        {"id": "3", "city": "Karaj", "price": "150", "active": "yes", "note": ""},
    ]


def test_profile_counts_rows_and_columns(sample_rows):
    report = profile_rows(sample_rows)
    assert report.row_count == 3
    assert len(report.column_profiles) == 5


def test_numeric_inference_with_hint(sample_rows):
    report = profile_rows(sample_rows)
    by_name = {p.name: p for p in report.column_profiles}
    assert by_name["id"].inferred_type == "numeric"
    assert by_name["price"].inferred_type == "numeric"


def test_categorical_inference(sample_rows):
    report = profile_rows(sample_rows)
    by_name = {p.name: p for p in report.column_profiles}
    assert by_name["city"].inferred_type == "categorical"


def test_boolean_inference():
    rows = [{"flag": "yes"}, {"flag": "no"}]
    report = profile_rows(rows)
    assert report.column_profiles[0].inferred_type == "boolean"


def test_missing_ratio_computed(sample_rows):
    report = profile_rows(sample_rows)
    note = next(p for p in report.column_profiles if p.name == "note")
    assert note.missing == 2
    assert note.missing_ratio == pytest.approx(2 / 3)


def test_numeric_summary_values(sample_rows):
    report = profile_rows(sample_rows)
    price = next(s for s in report.numeric_summaries if s.name == "price")
    assert price.minimum == pytest.approx(99.9)
    assert price.maximum == pytest.approx(150.0)
    assert price.median == pytest.approx(120.5)


def test_constant_column_warns():
    rows = [{"status": "same"} for _ in range(15)]
    report = profile_rows(rows)
    assert any("constant" in w for w in report.warnings)


def test_entirely_empty_column_warns():
    rows = [{"a": "", "b": "1"}, {"a": "", "b": "2"}]
    report = profile_rows(rows)
    assert any("entirely empty" in w for w in report.warnings)


def test_empty_dataset_rejected():
    with pytest.raises(EmptyDatasetError):
        profile_rows([])


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileReadError):
        profile_csv(tmp_path / "ghost.csv")


def test_csv_roundtrip(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text(
        "id,score\n1,10\n2,20\n3,30\n",
        encoding="utf-8",
    )
    report = profile_csv(source)
    score = next(p for p in report.column_profiles if p.name == "score")
    assert score.inferred_type == "numeric"
    summary = next(s for s in report.numeric_summaries if s.name == "score")
    assert summary.mean == pytest.approx(20.0)


def test_summary_lines_render(sample_rows):
    lines = profile_rows(sample_rows).summary_lines()
    assert any(line.startswith("rows=3") for line in lines)
