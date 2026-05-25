"""Dependency availability sanity checks for CI environments."""
from __future__ import annotations


def test_core_stdlib_available() -> None:
    import csv  # noqa: F401
    import json  # noqa: F401
    import sqlite3  # noqa: F401
    from pathlib import Path  # noqa: F401


def test_techno_search_importable() -> None:
    import techno_search  # noqa: F401
    from techno_search import schemas, scoring  # noqa: F401


def test_pipeline_runner_importable() -> None:
    from techno_search.pipeline_runner import PipelineRunResult, run_pipeline  # noqa: F401


def test_hit_table_reader_importable() -> None:
    from techno_search.radio.hit_table_reader import read_hit_table_csv  # noqa: F401


def test_catalog_reader_importable() -> None:
    from techno_search.infrared.catalog_reader import read_gaia_wise_csv  # noqa: F401


def test_anomaly_catalog_reader_importable() -> None:
    from techno_search.anomalies.catalog_reader import read_anomaly_csv  # noqa: F401


def test_data_quality_importable() -> None:
    from techno_search.data_quality import validate_input  # noqa: F401


def test_rfi_database_importable() -> None:
    from techno_search.rfi_database import rfi_database_summary  # noqa: F401


def test_labeled_dataset_importable() -> None:
    from techno_search.labeled_dataset import labeled_dataset_summary  # noqa: F401


def test_baseline_eval_importable() -> None:
    from techno_search.baseline_eval import eval_against_labels, evaluate_baseline  # noqa: F401
