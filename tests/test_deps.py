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


def test_rfi_database_admission_importable() -> None:
    from techno_search.rfi_database_admission import (  # noqa: F401
        rfi_database_admission_summary,
    )


def test_curated_dataset_admission_importable() -> None:
    from techno_search.curated_dataset_admission import (  # noqa: F401
        curated_dataset_admission_summary,
    )


def test_project_status_consistency_importable() -> None:
    from techno_search.project_status_consistency import (  # noqa: F401
        project_status_consistency_summary,
    )


def test_production_blocker_consistency_importable() -> None:
    from techno_search.production_blocker_consistency import (  # noqa: F401
        production_blocker_consistency_summary,
    )


def test_operations_alert_review_consistency_importable() -> None:
    from techno_search.operations_alert_review_consistency import (  # noqa: F401
        operations_alert_review_consistency_summary,
    )


def test_operations_action_resolution_consistency_importable() -> None:
    from techno_search.operations_action_resolution_consistency import (  # noqa: F401
        operations_action_resolution_consistency_summary,
    )


def test_operations_blocker_progress_consistency_importable() -> None:
    from techno_search.operations_blocker_progress_consistency import (  # noqa: F401
        operations_blocker_progress_consistency_summary,
    )


def test_top_level_sqlite_log_consistency_importable() -> None:
    from techno_search.top_level_sqlite_log_consistency import (  # noqa: F401
        top_level_sqlite_log_consistency_summary,
    )


def test_sqlite_operational_log_registry_importable() -> None:
    from techno_search.sqlite_operational_log_registry import (  # noqa: F401
        sqlite_operational_log_registry_summary,
    )


def test_sqlite_operational_log_adapter_plan_importable() -> None:
    from techno_search.sqlite_operational_log_adapter_plan import (  # noqa: F401
        sqlite_operational_log_adapter_plan_summary,
    )


def test_sqlite_operational_log_adapter_contract_importable() -> None:
    from techno_search.sqlite_operational_log_adapter_contract import (  # noqa: F401
        sqlite_operational_log_adapter_contract_summary,
    )


def test_sqlite_operational_log_adapter_ddl_preview_importable() -> None:
    from techno_search.sqlite_operational_log_adapter_ddl_preview import (  # noqa: F401
        sqlite_operational_log_adapter_ddl_preview_summary,
    )


def test_sqlite_operational_log_adapter_row_preview_importable() -> None:
    from techno_search.sqlite_operational_log_adapter_row_preview import (  # noqa: F401
        sqlite_operational_log_adapter_row_preview_summary,
    )


def test_sqlite_operational_log_adapter_insert_preview_importable() -> None:
    from techno_search.sqlite_operational_log_adapter_insert_preview import (  # noqa: F401
        sqlite_operational_log_adapter_insert_preview_summary,
    )


def test_sqlite_operational_log_adapter_execution_preview_importable() -> None:
    from techno_search.sqlite_operational_log_adapter_execution_preview import (  # noqa: F401
        sqlite_operational_log_adapter_execution_preview_summary,
    )


def test_labeled_dataset_importable() -> None:
    from techno_search.labeled_dataset import labeled_dataset_summary  # noqa: F401


def test_baseline_eval_importable() -> None:
    from techno_search.baseline_eval import eval_against_labels, evaluate_baseline  # noqa: F401
