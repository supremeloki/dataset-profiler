# dataset-profiler

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Instant dataset health-checks: column type inference, missing/uniqueness ratios, numeric summaries, and data-quality warnings — know what's wrong with a CSV before modeling on it.

## 🚀 Overview

The first hour with any new dataset is the same ritual: count rows, check types, hunt empty columns, spot constant flags. `dataset-profiler` automates it in one call. Columns are typed by content *and* name hints (`price`, `age`, …), numeric columns get min/max/mean/median/stddev summaries, and quality warnings flag entirely-empty or constant columns before they poison a model.

## ✨ Features

- **Type inference:** `numeric` (hint-aware threshold), `boolean`, `categorical`, `text`, `empty`
- **Per-column profiles:** total, missing count + ratio, distinct count + uniqueness
- **Numeric summaries:** min / max / mean / median / stddev / range
- **Quality warnings:** entirely-empty columns, single-constant-value columns (>10 rows)
- **CSV reader:** BOM-tolerant UTF-8, typed `FileReadError` for unreadable files
- **Renderable report:** `summary_lines()` for logs; frozen dataclasses throughout
- **Zero dependencies**

## 🚧 Structure

```
dataset-profiler/
├── src/data_profiler/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

```bash
git clone https://github.com/supremeloki/dataset-profiler.git
cd dataset-profiler
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from pathlib import Path
from data_profiler import profile_csv

report = profile_csv(Path("sales.csv"))
for line in report.summary_lines():
    print(line)

price = next(s for s in report.numeric_summaries if s.name == "price")
print(price.mean, price.stddev)
```

### From in-memory rows

```python
from data_profiler import profile_rows

rows = [{"id": "1", "city": "Karaj"}, {"id": "2", "city": "Tehran"}]
report = profile_rows(rows)
```

## 🔧 Error Handling

```text
ProfilingError
├── EmptyDatasetError    # zero rows provided
└── FileReadError        # missing/undecodable CSV file
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style), frozen profiles and reports
- Zero comments — names carry the meaning
- Hint-aware inference keeps `id`/`year` columns numeric without strict parsing

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi**

---

⭐ Star this repo if you find it useful!
