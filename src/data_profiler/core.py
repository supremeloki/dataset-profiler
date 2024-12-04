from __future__ import annotations

import csv
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence


class ProfilingError(Exception):
    pass


class EmptyDatasetError(ProfilingError):
    pass


class FileReadError(ProfilingError):
    pass


NUMERIC_HINTS = ("id", "count", "total", "amount", "price", "age", "year", "quantity")


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    inferred_type: str
    total: int
    missing: int
    distinct: int

    @property
    def missing_ratio(self) -> float:
        return self.missing / self.total if self.total else 0.0

    @property
    def uniqueness(self) -> float:
        return self.distinct / self.total if self.total else 0.0


@dataclass(frozen=True)
class NumericSummary:
    name: str
    minimum: float
    maximum: float
    mean: float
    median: float
    stddev: float

    @property
    def range(self) -> float:
        return self.maximum - self.minimum


@dataclass(frozen=True)
class DatasetReport:
    row_count: int
    column_profiles: tuple[ColumnProfile, ...]
    numeric_summaries: tuple[NumericSummary, ...] = ()
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def summary_lines(self) -> list[str]:
        lines = [f"rows={self.row_count} columns={len(self.column_profiles)}"]
        for profile in self.column_profiles:
            line = (
                f"{profile.name}: {profile.inferred_type}, "
                f"missing={profile.missing_ratio:.1%}, unique={profile.uniqueness:.1%}"
            )
            lines.append(line)
        for warning in self.warnings:
            lines.append(f"⚠ {warning}")
        return lines


def _is_numeric(value: str) -> bool:
    try:
        float(value.replace(",", ""))
        return True
    except ValueError:
        return False


def _looks_numeric_column(name: str, values: Sequence[str]) -> bool:
    lowered = name.lower()
    hinted = any(hint in lowered for hint in NUMERIC_HINTS)
    sampled = [v for v in values[:200] if v.strip() != ""]
    if not sampled:
        return False
    numeric_ratio = sum(1 for v in sampled if _is_numeric(v)) / len(sampled)
    threshold = 0.5 if hinted else 0.9
    return numeric_ratio >= threshold


def infer_type(name: str, values: Sequence[str]) -> str:
    non_empty = [v for v in values if v.strip() != ""]
    if not non_empty:
        return "empty"
    if _looks_numeric_column(name, non_empty):
        return "numeric"
    lowered = {v.lower() for v in non_empty}
    if lowered <= {"true", "false", "yes", "no", "0", "1"}:
        return "boolean"
    distinct = len(set(non_empty))
    if distinct <= max(12, len(non_empty) * 0.05):
        return "categorical"
    return "text"


def summarize_numeric(name: str, raw_values: Sequence[str]) -> NumericSummary | None:
    numbers = []
    for value in raw_values:
        stripped = value.strip()
        if stripped == "":
            continue
        try:
            numbers.append(float(stripped.replace(",", "")))
        except ValueError:
            continue
    if not numbers:
        return None
    ordered = sorted(numbers)
    count = len(ordered)
    middle = count // 2
    median = (
        ordered[middle]
        if count % 2 == 1
        else (ordered[middle - 1] + ordered[middle]) / 2
    )
    mean = sum(ordered) / count
    variance = sum((x - mean) ** 2 for x in ordered) / count
    return NumericSummary(
        name=name,
        minimum=ordered[0],
        maximum=ordered[-1],
        mean=mean,
        median=median,
        stddev=math.sqrt(variance),
    )


def profile_rows(rows: list[dict[str, str]]) -> DatasetReport:
    if not rows:
        raise EmptyDatasetError("no rows to profile")
    columns = list(rows[0].keys())
    profiles: list[ColumnProfile] = []
    summaries: list[NumericSummary] = []
    warnings: list[str] = []
    for name in columns:
        values = [row.get(name, "") or "" for row in rows]
        missing = sum(1 for v in values if v.strip() == "")
        distinct = len({v for v in values if v.strip() != ""})
        inferred = infer_type(name, values)
        profiles.append(ColumnProfile(
            name=name,
            inferred_type=inferred,
            total=len(values),
            missing=missing,
            distinct=distinct,
        ))
        if inferred == "numeric":
            summary = summarize_numeric(name, values)
            if summary is not None:
                summaries.append(summary)
        if missing == len(values):
            warnings.append(f"column {name!r} is entirely empty")
        elif inferred != "empty" and distinct == 1 and len(values) > 10:
            warnings.append(f"column {name!r} has a single constant value")
    return DatasetReport(
        row_count=len(rows),
        column_profiles=tuple(profiles),
        numeric_summaries=tuple(summaries),
        warnings=tuple(warnings),
    )


def read_csv_rows(path: Path, encoding: str = "utf-8-sig") -> list[dict[str, str]]:
    if not path.exists():
        raise FileReadError(f"dataset file not found: {path}")
    try:
        with path.open(encoding=encoding, newline="") as handle:
            return [
                {k: (v or "") for k, v in record.items()}
                for record in csv.DictReader(handle)
            ]
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise FileReadError(f"cannot read {path.name}: {exc}") from exc


def profile_csv(path: Path) -> DatasetReport:
    rows = read_csv_rows(path)
    report = profile_rows(rows)
    object.__setattr__(report, "source", str(path.name))
    return report
