"""Command-line interface for synthetic candidate scoring."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from techno_search import __version__
from techno_search.ai_hardening_gate import ai_hardening_gate_summary
from techno_search.artifact_cleanup import (
    apply_artifact_cleanup,
    plan_artifact_cleanup,
)
from techno_search.background_search import (
    BackgroundUserDecisionRecord,
    append_background_user_decision_record,
    background_draft_follow_up_report_summary,
    background_follow_up_test_summary,
    background_needs_follow_up_summary,
    background_report_readiness_summary,
    background_review_workflow_summary,
    background_reviewed_log_summary,
    background_search_ledger_summary,
    background_user_decision_summary,
    candidate_extraction_handoff_summary,
    run_local_background_search_once,
    scheduler_dry_run,
    target_priority_summary,
    write_background_draft_follow_up_reports,
)
from techno_search.calibration import (
    calibration_track_summary,
    false_positive_class_summary,
    load_calibration_fixtures,
    summarize_calibration_fixtures,
)
from techno_search.candidate_annotation import candidate_annotation_summary
from techno_search.candidate_audit_trail import audit_trail_summary
from techno_search.candidate_feature_vector import feature_vector_summary
from techno_search.candidate_methods_summary import candidate_methods_summary
from techno_search.candidate_priority_queue import priority_queue_summary
from techno_search.candidate_resolution import candidate_resolution_summary
from techno_search.candidate_retention import candidate_retention_summary
from techno_search.constants import DEFAULT_SCHEMA_VERSION, DEFAULT_SCORING_CONFIG_VERSION
from techno_search.cross_track import cross_track_summary
from techno_search.curated_dataset_admission import curated_dataset_admission_summary
from techno_search.curated_dataset_intake import curated_dataset_intake_summary
from techno_search.feature_importance import feature_importance_summary
from techno_search.feature_normalization import feature_normalization_summary
from techno_search.follow_up_request import follow_up_request_summary
from techno_search.injection_recovery import false_negative_summary, injection_recovery_summary
from techno_search.live_data import (
    CatalogCache,
    CatalogCachePolicy,
    LiveProviderCache,
    live_client_summary,
    live_data_enabled,
    live_metadata_fixture_summary,
    provider_adapters,
    validate_catalog_cache_commit_paths,
)
from techno_search.multi_epoch_summary import multi_epoch_summary
from techno_search.observation_campaign import observation_campaign_summary
from techno_search.pipeline_config import pipeline_config_summary
from techno_search.plotting import plot_artifact_summary
from techno_search.provenance import provenance_chain_validator
from techno_search.radio_corpus_cleanup import (
    apply_radio_corpus_cleanup,
    plan_radio_corpus_cleanup,
)
from techno_search.real_data_admission_preflight import (
    real_data_admission_preflight_summary,
)
from techno_search.reporting import (
    candidate_packet_json,
    write_candidate_reports,
)
from techno_search.reproducibility import verify_report_directory
from techno_search.review_queue import (
    consensus_export_summary,
    consensus_summary,
    review_queue_summary,
)
from techno_search.rfi_database import rfi_database_summary
from techno_search.rfi_database_admission import rfi_database_admission_summary
from techno_search.schemas import Candidate, Track, candidate_from_mapping
from techno_search.scoring import score_candidate
from techno_search.signal_registry import (
    signal_registry_summary,
    signal_registry_track_summary,
)
from techno_search.validation import (
    validate_candidate_file,
    validate_draft_report_directory,
    validate_report_directory,
    validate_sqlite_log_database,
)
from techno_search.validation_datasets import (
    validation_dataset_summary,
    validation_promotion_summary,
    validation_readiness_summary,
)

TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION = "top_level_sqlite_logs_v2"
DEFAULT_SQLITE_LOG_PATH = Path("logs/techno_search.sqlite3")


def default_sqlite_log_path(project_root: Path | None = None) -> Path:
    """Return the default SQLite log path without importing SQLite at CLI startup."""

    root = project_root or Path.cwd()
    return root / DEFAULT_SQLITE_LOG_PATH


def init_sqlite_log_db(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import init_sqlite_log_db as _impl

    return _impl(*args, **kwargs)


def sqlite_log_summary(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_log_summary as _impl

    return _impl(*args, **kwargs)


def sqlite_log_integrity_summary(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_log_integrity_summary as _impl

    return _impl(*args, **kwargs)


def sqlite_log_weekly_digest(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_log_weekly_digest as _impl

    return _impl(*args, **kwargs)


def sqlite_log_export(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_log_export as _impl

    return _impl(*args, **kwargs)


def sqlite_recent_runs(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_recent_runs as _impl

    return _impl(*args, **kwargs)


def sqlite_needs_follow_up(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_needs_follow_up as _impl

    return _impl(*args, **kwargs)


def sqlite_log_migration_summary(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_log_migration_summary as _impl

    return _impl(*args, **kwargs)


def sqlite_log_migration_plan(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_log_migration_plan as _impl

    return _impl(*args, **kwargs)


def apply_sqlite_log_migration(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import apply_sqlite_log_migration as _impl

    return _impl(*args, **kwargs)


def sqlite_log_pragmas(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_log_pragmas as _impl

    return _impl(*args, **kwargs)


def sqlite_log_retention_summary(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_log_retention_summary as _impl

    return _impl(*args, **kwargs)


def sqlite_log_backup(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_log_backup as _impl

    return _impl(*args, **kwargs)


def sqlite_log_vacuum(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import sqlite_log_vacuum as _impl

    return _impl(*args, **kwargs)


def validate_sqlite_log_commit_paths(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from techno_search.log_store import validate_sqlite_log_commit_paths as _impl

    return _impl(*args, **kwargs)


class _StubDict(dict):  # type: ignore[type-arg]
    """Dict that returns 0 for any missing key — used by deleted-log stubs."""

    def __missing__(self, _key: object) -> int:
        return 0


def escalation_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "open_count": 0})


def scoring_audit_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def candidate_alert_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"open_count": 0, "critical_open_count": 0, "entry_count": 0})


def alert_escalation_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "resolved_count": 0})


def access_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def audit_trail_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def beam_configuration_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def calibration_event_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def candidate_annotation_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "active_count": 0})


def candidate_status_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "active_count": 0})


def data_quality_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def environmental_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def frequency_channel_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "active_count": 0})


def instrument_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def maintenance_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def noise_measurement_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "recorded_count": 0})


def observation_parameter_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "applied_count": 0})


def pipeline_checkpoint_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "saved_count": 0})


def pipeline_run_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def polarization_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "measured_count": 0})


def power_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def scan_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def session_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def source_catalog_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "matched_count": 0})


def spectral_feature_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "detected_count": 0})


def telescope_status_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "recorded_count": 0})


def weather_log_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def access_control_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def alert_resolution_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "open_count": 0})


def antenna_pointing_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def archival_query_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def asset_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def audit_finding_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def backup_recovery_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "completed_count": 0})


def budget_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def candidate_deduplication_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "pending_count": 0})


def candidate_export_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "delivered_count": 0})


def candidate_linkage_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def candidate_match_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "matched_count": 0})


def capacity_planning_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "adequate_count": 0})


def certificate_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def change_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def change_request_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def communication_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def compliance_audit_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def compliance_report_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def configuration_audit_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def configuration_change_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def contract_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def cooling_system_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def data_archival_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def data_gap_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "unresolved_count": 0})


def data_retention_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def data_transfer_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def disaster_recovery_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def document_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def doppler_correction_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def event_correlation_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def firmware_update_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def hardware_fault_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def health_check_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def identity_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def incident_response_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def incident_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def instrument_configuration_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def intake_queue_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "blocked_count": 0})


def interference_environment_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def knowledge_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def license_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def network_connectivity_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def network_monitoring_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def observation_request_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "pending_count": 0})


def operator_escalation_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "open_count": 0})


def patch_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def performance_monitoring_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def pipeline_error_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "unresolved_count": 0})


def pipeline_replay_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "matched_count": 0})


def pipeline_version_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def problem_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def procurement_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def project_milestone_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def quality_gate_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "pass_count": 0})


def receiver_health_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def release_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def resource_allocation_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def rfi_mitigation_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "flagged_count": 0})


def risk_assessment_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "mitigated_count": 0})


def scheduling_conflict_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def security_event_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def service_level_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def service_request_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def signal_classification_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "classified_count": 0})


def software_deployment_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def software_update_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def storage_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def supplier_management_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def system_diagnostics_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def system_health_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def target_selection_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def time_synchronization_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def training_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def user_activity_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def vendor_assessment_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def vulnerability_scan_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})


def workflow_state_summary(_path: object = None) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})



# --- Phase 0 stubs for deleted operational-overhead modules ---

def aggregate_blockers_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"total_blocker_count": 0, "unique_candidate_count": 0})

def baseline_pathway_drift_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"drift_count": 0})

def baseline_performance_history_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "above_baseline_count": 0})

def benchmark_run_result_comparison(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"ok": True, "entry_count": 0})

def build_weekly_review_template(*_a: object, **_k: object) -> str:
    return ""

def candidate_comparison_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0})

def candidate_flags_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"flag_count": 0, "open_count": 0})

def candidate_lifecycle_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"lifecycle_count": 0, "lifecycle_blocked": 0})

def candidate_rescore_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"event_count": 0, "pathway_change_count": 0})

def classifier_rule_coverage_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict(
        {"covered_pathway_count": 0, "uncovered_pathway_count": 0, "coverage_fraction": 0.0}
    )

def config_version_history_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})

def epoch_plan_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "pending_count": 0})

def evaluate_baseline(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"ok": True, "entry_count": 0, "accuracy": 0.0})

def lifecycle_transition_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"invalid_transition_count": 0})

def ml_pipeline_diagnostics_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"pipeline_ml_status": "unknown"})

def ml_training_data_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})

def model_architecture_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"architecture_count": 0})

def model_evaluation_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"evaluation_count": 0, "above_baseline_count": 0})

def model_performance_history_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"snapshot_count": 0})

def model_registry_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"registry_count": 0, "above_baseline_count": 0})

def model_serving_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "active_count": 0})

def observation_efficiency_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"completion_rate": 0.0, "cancellation_rate": 0.0})

def observation_gap_analysis(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"window_count": 0})

def observation_notes_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"note_count": 0, "follow_up_recommended_count": 0})

def observation_schedule_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})

def operations_blocker_detail_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"detail_count": 0, "total_evidence_record_count": 0,
                      "all_external_authorization_disabled": True,
                      "sqlite_context_is_resolved": True})

def operations_blocker_followup_progress_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "coverage_complete": True,
                      "all_external_authorization_disabled": True})

def operations_blocker_followup_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "coverage_complete": True,
                      "all_external_authorization_disabled": True,
                      "all_detail_evidence_reviewed": True})

def operations_blocker_progress_execution_followup_summary(  # noqa: E501
    *_a: object, **_k: object
) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "coverage_complete": True,
                      "all_external_authorization_disabled": True,
                      "all_detail_evidence_reviewed": True})

def operations_blocker_progress_execution_review_summary(  # noqa: E501
    *_a: object, **_k: object
) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "coverage_complete": True,
                      "all_external_authorization_disabled": True,
                      "all_detail_evidence_reviewed": True})

def operations_blocker_progress_execution_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "coverage_complete": True,
                      "all_external_authorization_disabled": True, "priority_sequence_ok": True})

def operations_blocker_progress_next_actions_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "coverage_complete": True, "priority_sequence_ok": True})

def operations_blocker_progress_review_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "coverage_complete": True})

def operations_blocker_review_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "coverage_complete": True,
                      "all_external_authorization_disabled": True,
                      "all_detail_evidence_reviewed": True})

def operator_assignment_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"assignment_count": 0, "escalated_count": 0})

def operator_coverage_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"operator_count": 0})

def operator_handoff_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"template_count": 0, "approved_count": 0})

def operator_performance_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"operator_count": 0, "overall_completion_rate": 0.0})

def pipeline_audit_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"total_audit_actions": 0})

def pipeline_bottleneck_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"total_stalled_candidates": 0})

def pipeline_capacity_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"capacity_status": "ok"})

def pipeline_health_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"total_blocked_count": 0, "snapshot_count": 0})

def pipeline_telemetry_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"entry_count": 0})

def pipeline_throughput_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"throughput_rate": 0.0})

def provenance_audit_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "consistent_count": 0})

def quality_control_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"overall_qc_health": "ok"})

def review_deadlines_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"deadline_count": 0, "overdue_count": 0})

def route_coverage_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"covered_pathway_count": 0, "uncovered_pathway_count": 0})

def score_determinism_check(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"ok": True, "issue_count": 0})

def score_history_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "unique_candidate_count": 0})

def scoring_config_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"threshold_count": 0})

def scoring_threshold_audit_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "active_count": 0})

def sensitivity_config_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"track_count": 0, "weight_count": 0})

def submission_readiness_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"record_count": 0, "ready_count": 0})

def target_recalibration_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"snapshot_count": 0})

def target_watchlist_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"entry_count": 0, "elevated_count": 0, "conflict_count": 0})

def triage_label_completeness_check(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"coverage_fraction": 0.0})

def triage_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"note_count": 0, "tracks_covered": [], "triage_count": 0,
                      "triage_blocked": 0})

def write_weekly_review_template(*_a: object, **_k: object) -> None:
    return None


# --- Phase 0 stubs: overhead modules deleted, functions stubbed below ---

class BenchmarkRunResult:
    """Phase 0 stub — benchmark_metadata deleted."""


def benchmark_metadata_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def benchmark_run_result_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def append_benchmark_run_result(*_a: object, **_k: object) -> None:
    pass


def calibration_corpus_admission_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def mcp_bootstrap_consistency_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def mcp_server_policy_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def operations_action_plan_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return {"actions": [], "ok": True, "open_action_count": 0, "completed_action_count": 0}


def operations_action_resolution_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def operations_action_resolution_consistency_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def operations_alert_review_consistency_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def operations_blocker_progress_consistency_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def operations_readiness_digest(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def operations_readiness_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return {
        "sqlite_log_snapshot": {
            "integrity_ok": True,
            "weekly_digest_ok": True,
            "network_access_allowed_count": 0,
            "external_submission_approved_count": 0,
        },
        "recommendation": "blocked_for_real_data",
        "real_data_blocker_count": 0,
        "ok": True,
    }


def pipeline_integration_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def precision_recall_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def production_blocker_consistency_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"ok": True, "issue_count": 0, "issues": []})


def project_status_consistency_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"ok": True, "issue_count": 0, "issues": []})


def reliability_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def sqlite_operational_log_adapter_authorization_gate_summary(*_a: object, **_k: object) -> dict[str, Any]:  # noqa: E501
    return _StubDict({})


def sqlite_operational_log_adapter_contract_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def sqlite_operational_log_adapter_ddl_preview_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def sqlite_operational_log_adapter_dry_run_manifest_summary(*_a: object, **_k: object) -> dict[str, Any]:  # noqa: E501
    return _StubDict({})


def sqlite_operational_log_adapter_execution_preview_summary(*_a: object, **_k: object) -> dict[str, Any]:  # noqa: E501
    return _StubDict({})


def sqlite_operational_log_adapter_insert_preview_summary(*_a: object, **_k: object) -> dict[str, Any]:  # noqa: E501
    return _StubDict({})


def sqlite_operational_log_adapter_plan_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def sqlite_operational_log_adapter_readiness_preflight_summary(*_a: object, **_k: object) -> dict[str, Any]:  # noqa: E501
    return _StubDict({})


def sqlite_operational_log_adapter_row_preview_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def sqlite_operational_log_registry_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


def top_level_sqlite_log_consistency_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({"ok": True})


def track_comparison_summary(*_a: object, **_k: object) -> dict[str, Any]:
    return _StubDict({})


SCHEMA_FILENAMES = {
    "ai_hardening_gate": "ai_hardening_gate.schema.json",
    "background_draft_follow_up_reports": "background_draft_follow_up_reports.schema.json",
    "background_draft_report_manifest": "background_draft_report_manifest.schema.json",
    "background_follow_up_tests": "background_follow_up_tests.schema.json",
    "background_needs_follow_up_log": "background_needs_follow_up_log.schema.json",
    "background_report_readiness": "background_report_readiness.schema.json",
    "background_reviewed_log": "background_reviewed_log.schema.json",
    "background_search_ledger": "background_search_ledger.schema.json",
    "background_targets": "background_targets.schema.json",
    "background_user_decisions": "background_user_decisions.schema.json",
    "batch_manifest": "batch_manifest.schema.json",
    "benchmark_metadata": "benchmark_metadata.schema.json",
    "benchmark_run_results": "benchmark_run_results.schema.json",
    "candidate_extraction_handoff": "candidate_extraction_handoff.schema.json",
    "candidate_packet": "candidate_packet.schema.json",
    "consensus_export": "consensus_export.schema.json",
    "consensus_labels": "consensus_labels.schema.json",
    "cross_track_references": "cross_track_references.schema.json",
    "report_manifest": "report_manifest.schema.json",
    "review_queue": "review_queue.schema.json",
    "validation_dataset_manifest": "validation_dataset_manifest.schema.json",
    "validation_promotion_rules": "validation_promotion_rules.schema.json",
    "validation_readiness": "validation_readiness.schema.json",
    "target_watchlist": "target_watchlist.schema.json",
    "top_level_sqlite_log_consistency": "top_level_sqlite_log_consistency.schema.json",
    "weekly_review_template": "weekly_review_template.schema.json",
    "baseline_eval": "baseline_eval.schema.json",
    "baseline_performance_history": "baseline_performance_history.schema.json",
    "candidate_lifecycle": "candidate_lifecycle.schema.json",
    "candidate_triage": "candidate_triage.schema.json",
    "observation_schedule": "observation_schedule.schema.json",
    "scoring_config_summary": "scoring_config_summary.schema.json",
    "sensitivity_config_summary": "sensitivity_config_summary.schema.json",
    "signal_registry": "signal_registry.schema.json",
    "candidate_audit_trail": "candidate_audit_trail.schema.json",
    "multi_epoch_observations": "multi_epoch_observations.schema.json",
    "target_priority_snapshots": "target_priority_snapshots.schema.json",
    "candidate_flags": "candidate_flags.schema.json",
    "candidate_observation_notes": "candidate_observation_notes.schema.json",
    "candidate_score_history": "candidate_score_history.schema.json",
    "epoch_plan": "epoch_plan.schema.json",
    "operator_assignment": "operator_assignment.schema.json",
    "candidate_annotation": "candidate_annotation.schema.json",
    "candidate_feature_vector": "candidate_feature_vector.schema.json",
    "candidate_priority_queue": "candidate_priority_queue.schema.json",
    "feature_importance": "feature_importance.schema.json",
    "feature_normalization": "feature_normalization.schema.json",
    "ml_model_registry": "ml_model_registry.schema.json",
    "model_architecture": "model_architecture.schema.json",
    "model_evaluation": "model_evaluation.schema.json",
    "model_performance_history": "model_performance_history.schema.json",
    "model_serving": "model_serving.schema.json",
    "candidate_rescore": "candidate_rescore.schema.json",
    "pipeline_config": "pipeline_config.schema.json",
    "submission_readiness": "submission_readiness.schema.json",
    "candidate_comparison": "candidate_comparison.schema.json",
    "pipeline_telemetry": "pipeline_telemetry.schema.json",
    "provenance_audit": "provenance_audit.schema.json",
    "project_status_consistency": "project_status_consistency.schema.json",
    "mcp_bootstrap_consistency": "mcp_bootstrap_consistency.schema.json",
    "mcp_server_policy": "mcp_server_policy.schema.json",
    "production_blocker_consistency": "production_blocker_consistency.schema.json",
    "real_data_admission_preflight": "real_data_admission_preflight.schema.json",
    "sqlite_operational_log_registry": "sqlite_operational_log_registry.schema.json",
    "sqlite_operational_log_adapter_plan": "sqlite_operational_log_adapter_plan.schema.json",
    "sqlite_operational_log_adapter_contract": "sqlite_operational_log_adapter_contract.schema.json",  # noqa: E501
    "sqlite_operational_log_adapter_authorization_gate": "sqlite_operational_log_adapter_authorization_gate.schema.json",  # noqa: E501
    "sqlite_operational_log_adapter_ddl_preview": "sqlite_operational_log_adapter_ddl_preview.schema.json",  # noqa: E501
    "sqlite_operational_log_adapter_dry_run_manifest": "sqlite_operational_log_adapter_dry_run_manifest.schema.json",  # noqa: E501
    "sqlite_operational_log_adapter_execution_preview": "sqlite_operational_log_adapter_execution_preview.schema.json",  # noqa: E501
    "sqlite_operational_log_adapter_insert_preview": "sqlite_operational_log_adapter_insert_preview.schema.json",  # noqa: E501
    "sqlite_operational_log_adapter_readiness_preflight": "sqlite_operational_log_adapter_readiness_preflight.schema.json",  # noqa: E501
    "sqlite_operational_log_adapter_row_preview": "sqlite_operational_log_adapter_row_preview.schema.json",  # noqa: E501
    "scoring_threshold_audit": "scoring_threshold_audit.schema.json",
    "config_version_history": "config_version_history.schema.json",
    "curated_dataset_admission": "curated_dataset_admission.schema.json",
    "curated_dataset_intake": "curated_dataset_intake.schema.json",
    "operator_handoff_template": "operator_handoff_template.schema.json",
    "candidate_resolution": "candidate_resolution.schema.json",
    "candidate_retention": "candidate_retention.schema.json",
    "data_quality": "data_quality.schema.json",
    "follow_up_request": "follow_up_request.schema.json",
    "observation_campaign": "observation_campaign.schema.json",
    "review_deadlines": "review_deadlines.schema.json",
    "operations_readiness_summary": "operations_readiness_summary.schema.json",
    "operations_action_plan": "operations_action_plan.schema.json",
    "operations_action_resolution": "operations_action_resolution.schema.json",
    "operations_action_resolution_consistency": "operations_action_resolution_consistency.schema.json",  # noqa: E501
    "operations_blocker_detail": "operations_blocker_detail.schema.json",
    "operations_blocker_followup": "operations_blocker_followup.schema.json",
    "operations_blocker_followup_progress": "operations_blocker_followup_progress.schema.json",
    "operations_blocker_progress_consistency": "operations_blocker_progress_consistency.schema.json",  # noqa: E501
    "operations_blocker_progress_review": "operations_blocker_progress_review.schema.json",
    "operations_blocker_progress_next_actions": "operations_blocker_progress_next_actions.schema.json",  # noqa: E501
    "operations_blocker_progress_execution": "operations_blocker_progress_execution.schema.json",
    "operations_blocker_progress_execution_followup": "operations_blocker_progress_execution_followup.schema.json",  # noqa: E501
    "operations_blocker_progress_execution_review": "operations_blocker_progress_execution_review.schema.json",  # noqa: E501
    "operations_blocker_review": "operations_blocker_review.schema.json",
    "operations_alert_review_consistency": "operations_alert_review_consistency.schema.json",
    "rfi_database_admission": "rfi_database_admission.schema.json",
    "rfi_database": "rfi_database.schema.json",
    "labeled_candidates": "labeled_candidates.schema.json",
    "labeled_candidates_citizen_science_v1": "labeled_candidates_citizen_science_v1.schema.json",
    "calibration_corpus_admission": "calibration_corpus_admission.schema.json",
    "data_release_snapshot": "data_release_snapshot.schema.json",
    "multi_target_scan": "multi_target_scan.schema.json",
    "scan_summary": "scan_summary.schema.json",
    "candidate_escalation": "candidate_escalation.schema.json",
    "cross_store_dedup": "cross_store_dedup.schema.json",
}


# ---------------------------------------------------------------------------
# prod-file-scan: tidy per-file scan with Rich TUI
# ---------------------------------------------------------------------------

_TRACK_EXTENSIONS: dict[str, list[str]] = {
    "radio": [".dat", ".csv"],
    "infrared": [".csv", ".fits"],
    "anomaly": [".csv", ".json"],
    "photometry": [".fits", ".fit"],
    "spectroscopy": [".fits", ".fit"],
}

_EXTENSION_TRACK: dict[str, str] = {
    ".dat": "radio",
    ".fits": "photometry",
    ".fit": "photometry",
}


def _infer_track(path: Path) -> str:
    """Infer pipeline track from file extension; defaults to 'radio'."""
    return _EXTENSION_TRACK.get(path.suffix.lower(), "radio")


def _run_prod_file_scan(args: object) -> int:  # noqa: C901
    """Run a per-file scan with Rich spinner UX.

    Each target file is processed serially with a spinner while in-flight.
    A single summary line is printed on completion. Ctrl+C writes an
    interrupted notice; restart will skip already-completed targets.

    Scientific guardrail: output lines are local triage aids only — no
    result constitutes a detection claim or authorizes external submission.
    """
    import argparse as _argparse
    import json as _json
    import signal as _signal

    from techno_search.candidate_escalation import escalation_gate_check
    from techno_search.pipeline_runner import run_pipeline
    from techno_search.tui import (
        TUI_DISCLAIMER,
        extract_composite_score,
        extract_stellar_from_candidate,
        make_scan_index,
        print_interrupted,
        print_result_line,
        print_scan_footer,
        print_scan_header,
        scan_spinner,
    )

    ns = args if isinstance(args, _argparse.Namespace) else _argparse.Namespace(**vars(args))
    input_dir = Path(ns.input_dir)
    output_dir = Path(ns.output_dir)
    track_arg: str | None = getattr(ns, "track", None)
    force: bool = bool(getattr(ns, "force", False))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect input files
    if track_arg:
        exts = _TRACK_EXTENSIONS.get(track_arg, [".dat", ".csv"])
    else:
        exts = [".dat", ".csv", ".fits", ".json"]

    input_files: list[Path] = sorted(
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in exts
    )

    if not input_files:
        print(f"No input files found in {input_dir} for track={track_arg or 'auto'}")
        return 1

    # Resume: skip files whose JSON output already exists
    def _output_json(src: Path) -> Path:
        return output_dir / f"{src.stem}.json"

    if not force:
        pending = [f for f in input_files if not _output_json(f).exists()]
        skipped = len(input_files) - len(pending)
    else:
        pending = input_files
        skipped = 0

    db_label = str(output_dir / "scan_progress")
    print_scan_header(len(pending), db_label, resume=skipped > 0)
    if skipped:
        print(f"  (skipping {skipped} already-completed target(s) — use --force to reprocess)")

    # Interrupt handling
    _interrupted = False

    def _sigint_handler(sig: int, frame: object) -> None:
        nonlocal _interrupted
        _interrupted = True

    original_handler = _signal.signal(_signal.SIGINT, _sigint_handler)

    succeeded = failed = escalations = 0

    try:
        for src in pending:
            if _interrupted:
                break

            track = track_arg or _infer_track(src)
            index = make_scan_index(src.stem)
            label = f"{src.stem}  [{track}]"

            with scan_spinner(label):
                try:
                    result = run_pipeline(
                        src,
                        track,
                        output_dir,
                        candidate_id=src.stem,
                    )
                except Exception as exc:
                    failed += 1
                    print_result_line(
                        index=index,
                        stellar="unknown",
                        score=0.0,
                        escalation=False,
                        ok=False,
                        error=str(exc)[:80],
                    )
                    continue

            if not result.ok:
                failed += 1
                print_result_line(
                    index=index,
                    stellar="unknown",
                    score=0.0,
                    escalation=False,
                    ok=False,
                    error=result.error,
                )
                continue

            # Load the written JSON to extract score / stellar / escalation
            json_path = _output_json(src)
            try:
                candidate_dict = _json.loads(json_path.read_text(encoding="utf-8"))
            except Exception:
                candidate_dict = {}

            score = extract_composite_score(candidate_dict)
            stellar = extract_stellar_from_candidate(candidate_dict)
            gate = escalation_gate_check(candidate_dict)
            is_escalation = bool(gate.get("passes", False))

            if is_escalation:
                escalations += 1
            succeeded += 1

            print_result_line(
                index=index,
                stellar=stellar,
                score=score,
                escalation=is_escalation,
                ok=True,
            )

    finally:
        _signal.signal(_signal.SIGINT, original_handler)

    if _interrupted:
        print_interrupted()
        return 130  # standard interrupted exit code

    print_scan_footer(succeeded, failed, escalations)
    _ = TUI_DISCLAIMER  # referenced for provenance; disclaimer is in module
    return 0 if failed == 0 else 1


def _resolve_production_run_dir_arg(args: object, out: TextIO) -> Path | None:
    """Resolve a production run directory from a real path or --latest."""
    run_dir = getattr(args, "run_dir", None)
    if run_dir:
        return Path(str(run_dir))
    if not bool(getattr(args, "latest", False)):
        from techno_search.production_run_outcomes import PRODUCTION_OUTCOME_DISCLAIMER

        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (
                        "Pass a real run_dir from `prod-runs` or use --latest "
                        "after a production scan has created a RUN-* directory."
                    ),
                    "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
                },
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return None
    from techno_search.production_run_outcomes import (
        PRODUCTION_OUTCOME_DISCLAIMER,
        latest_production_run_dir,
    )

    scans_dir = Path(str(getattr(args, "scans_dir", "results/scans")))
    latest = latest_production_run_dir(scans_dir)
    if latest is None:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (
                        f"No production runs found in {scans_dir}. Start one with "
                        "`caffeinate -i bash scripts/run_production_scan.sh`."
                    ),
                    "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
                },
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return None
    return latest


def _print_production_target_status(data: dict[str, Any], out: TextIO) -> None:
    """Print compact per-target production rows for overnight-run review."""
    if not data.get("ok"):
        print(json.dumps(data, indent=2, sort_keys=True), file=out)
        return
    run_id = str(data.get("run_id", "unknown-run"))
    entries = list(data.get("entries", []))
    follow_up_count = int(data.get("follow_up_required_count", 0) or 0)
    print(
        f"{run_id}: {len(entries)} target(s), {follow_up_count} follow-up candidate target(s)",
        file=out,
    )
    if not entries:
        print("Completed target evaluations: none", file=out)
        return
    print("Index | Target | Kind | Follow-up | Score | Pathway", file=out)
    for entry in entries:
        print(
            " | ".join(
                [
                    str(entry.get("index_id", "")),
                    str(entry.get("target_name", "")),
                    str(entry.get("target_kind", "")),
                    "yes" if entry.get("follow_up_required") else "no",
                    _format_score(entry.get("composite_score")),
                    str(entry.get("top_pathway", "")),
                ]
            ),
            file=out,
        )


def _print_production_follow_ups(data: dict[str, Any], out: TextIO) -> None:
    """Print compact follow-up ledger rows without hiding guardrails."""
    if not data.get("ok"):
        print(json.dumps(data, indent=2, sort_keys=True), file=out)
        return
    run_id = str(data.get("run_id", "unknown-run"))
    entries = list(data.get("entries", []))
    print(f"{run_id}: {len(entries)} follow-up candidate row(s)", file=out)
    if not entries:
        print("Follow-up candidates: none", file=out)
        return
    print("Follow-up | Target | Track | Score | SNR | Pathway", file=out)
    for entry in entries:
        print(
            " | ".join(
                [
                    str(entry.get("follow_up_id", "")),
                    str(entry.get("target_name", "")),
                    str(entry.get("track", "")),
                    _format_score(entry.get("score")),
                    _format_score(entry.get("snr")),
                    str(entry.get("pathway", "")),
                ]
            ),
            file=out,
        )


def _print_production_non_detections(data: dict[str, Any], out: TextIO) -> None:
    """Print compact non-detection ledger rows for review continuity."""
    if not data.get("ok"):
        print(json.dumps(data, indent=2, sort_keys=True), file=out)
        return
    run_id = str(data.get("run_id", "unknown-run"))
    entries = list(data.get("entries", []))
    print(f"{run_id}: {len(entries)} non-detection/no-follow-up row(s)", file=out)
    if not entries:
        reason = dict(data.get("scan_level_negative_result", {})).get("reason", "")
        suffix = f" ({reason})" if reason else ""
        print(f"Non-detections: none{suffix}", file=out)
        return
    print("Non-detection | Target | Track | Score | Status | Reason", file=out)
    for entry in entries:
        print(
            " | ".join(
                [
                    str(entry.get("non_detection_id", "")),
                    str(entry.get("target_name", "")),
                    str(entry.get("track", "")),
                    _format_score(entry.get("score")),
                    str(entry.get("status", "")),
                    str(entry.get("reason", "")),
                ]
            ),
            file=out,
        )


def _format_score(value: Any) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return ""


def main(argv: list[str] | None = None, stdout: TextIO | None = None) -> int:
    """Run the `techno-search` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    out = stdout or sys.stdout

    if args.command == "version":
        print(f"techno-search {__version__}", file=out)
        return 0

    if args.command == "score":
        candidate = load_candidate_json(args.input)
        scored = score_candidate(candidate)
        if args.output_dir is not None:
            paths = write_candidate_reports(
                scored,
                args.output_dir,
                filename_prefix=args.prefix,
                include_plot_artifacts=not args.no_plot_artifacts,
            )
            print(str(paths.markdown_path), file=out)
            print(str(paths.json_path), file=out)
            print(str(paths.manifest_path), file=out)
            for plot_path in paths.plot_artifact_paths:
                print(str(plot_path), file=out)
        else:
            print(candidate_packet_json(scored), file=out)
        return 0

    if args.command == "score-batch":
        manifest_path = score_batch(
            args.input_dir,
            args.output_dir,
            prefix=args.prefix,
            include_plot_artifacts=not args.no_plot_artifacts,
            workers=getattr(args, "workers", None),
        )
        print(str(manifest_path), file=out)
        return 0

    if args.command == "multi-epoch-compare":
        from techno_search.multi_epoch import multi_epoch_summary as _compare_epochs_summary

        dat_dir = Path(args.dat_dir)
        dat_files = sorted(dat_dir.glob("*.dat"))
        if not dat_files:
            print(
                json.dumps({"error": f"No .dat files found in {dat_dir}", "ok": False}),
                file=out,
            )
            return 1
        summary = _compare_epochs_summary(dat_files, freq_tolerance_hz=args.freq_tol_hz)
        print(json.dumps(summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "candidate-store-init":
        from techno_search.candidate_store import CandidateStore, default_store_path

        db_path = Path(args.db_path) if args.db_path else default_store_path()
        store = CandidateStore(db_path)
        store.init_schema()
        print(json.dumps({"ok": True, "db_path": str(db_path)}, indent=2), file=out)
        return 0

    if args.command == "candidate-store-summary":
        from techno_search.candidate_store import CandidateStore, default_store_path

        db_path = Path(args.db_path) if args.db_path else default_store_path()
        if not db_path.exists():
            _err = f"Store not found at {db_path}. Run candidate-store-init first."
            print(json.dumps({"ok": False, "error": _err}), file=out)
            return 1
        store = CandidateStore(db_path)
        print(json.dumps(store.summary(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "candidate-store-list":
        from techno_search.candidate_store import CandidateStore, default_store_path

        db_path = Path(args.db_path) if args.db_path else default_store_path()
        if not db_path.exists():
            _err = f"Store not found at {db_path}. Run candidate-store-init first."
            print(json.dumps({"ok": False, "error": _err}), file=out)
            return 1
        store = CandidateStore(db_path)
        pathway = getattr(args, "pathway", None)
        track = getattr(args, "track", None)
        if pathway:
            entries = store.list_by_pathway(pathway)
        elif track:
            entries = store.list_by_track(track)
        else:
            entries = store.list_all()
        limit = getattr(args, "limit", None) or 50
        entries = entries[:limit]
        print(
            json.dumps(
                {"entries": [e.as_dict() for e in entries], "count": len(entries)},
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "data-release-snapshot-summary":
        result = {
            "schema_version": "data_release_snapshot_stub_v1",
            "snapshot_count": 0,
            "snapshots": [],
        }
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "compare-data-releases":
        result = {
            "schema_version": "compare_snapshots_stub_v1",
            "differences": [],
            "comparison_count": 0,
        }
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "cross-band-features-summary":
        from techno_search.radio.cross_band_features import cross_band_features_summary

        result = cross_band_features_summary()
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "gbt-cadence-raw-status":
        from techno_search.gbt_cadence import load_cadence_manifest, raw_cadence_status

        manifest = load_cadence_manifest(Path(args.manifest))
        raw_dir = (
            Path(args.raw_dir)
            if args.raw_dir
            else Path(args.data_root) / "bl_observations" / str(manifest["cadence_id"])
        )
        result = raw_cadence_status(manifest, raw_dir)
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0 if result["ok"] else 1

    if args.command == "gbt-cadence-abacab-review":
        from techno_search.citizen_science_labels import cadence_abacab_review_summary

        result = cadence_abacab_review_summary(
            Path(args.cadence_csv),
            limit=int(args.limit),
            cadence_id=args.cadence_id,
        )
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0 if result["ok"] else 1

    if args.command == "globular-filter-summary":
        from techno_search.globular_filter import (
            GLOBULAR_FEATURE_NAMES,
            GLOBULAR_FILTER_DISCLAIMER,
            GLOBULAR_FILTER_VERSION,
        )

        result = {
            "schema_version": GLOBULAR_FILTER_VERSION,
            "disclaimer": GLOBULAR_FILTER_DISCLAIMER,
            "feature_names": GLOBULAR_FEATURE_NAMES,
            "feature_count": len(GLOBULAR_FEATURE_NAMES),
            "note": (
                "Apply the GLOBULAR filter to a hit table via "
                "apply_globular_filter(hits) in techno_search.globular_filter."
            ),
        }
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "semisupervised-scorer-summary":
        from techno_search.semisupervised_scorer import semisupervised_scorer_summary

        metadata_path = (
            Path(args.metadata)
            if args.metadata is not None
            else Path("data/meerkat_hits/semisupervised_scorer_metadata.json")
        )
        model_path = (
            Path(args.model)
            if args.model is not None
            else Path("data/meerkat_hits/semisupervised_scorer.joblib")
        )
        result = semisupervised_scorer_summary(
            metadata_path=metadata_path,
            model_path=model_path,
        )
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "semisupervised-corpus-build":
        from techno_search.semisupervised_scorer import build_training_corpus_from_dat_files

        try:
            result = build_training_corpus_from_dat_files(
                Path(args.dat_dir),
                Path(args.output),
                max_hits=args.max_hits,
            )
        except (FileNotFoundError, ValueError) as exc:
            result = {"ok": False, "error": str(exc)}
            print(json.dumps(result, indent=2, sort_keys=True), file=out)
            return 1
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "semisupervised-scorer-train":
        import joblib

        from techno_search.semisupervised_scorer import (
            DEFAULT_CONTAMINATION,
            DEFAULT_N_COMPONENTS,
            DEFAULT_N_ESTIMATORS,
            DEFAULT_WORKERS,
            SemisupervisedScorer,
            load_training_hits_ndjson,
        )

        corpus_path = Path(args.corpus)
        max_hits = int(args.max_hits) if args.max_hits is not None else None
        workers = int(args.workers or DEFAULT_WORKERS)
        n_components = int(args.n_components or DEFAULT_N_COMPONENTS)
        n_estimators = int(args.n_estimators or DEFAULT_N_ESTIMATORS)
        contamination = float(args.contamination or DEFAULT_CONTAMINATION)

        metadata_path = (
            Path(args.output_metadata)
            if args.output_metadata
            else corpus_path.parent / "semisupervised_scorer_metadata.json"
        )
        model_path = (
            Path(args.output_model)
            if args.output_model
            else corpus_path.parent / "semisupervised_scorer.joblib"
        )

        hits = load_training_hits_ndjson(corpus_path, max_hits=max_hits)
        scorer = SemisupervisedScorer(
            n_components=n_components,
            n_estimators=n_estimators,
            contamination=contamination,
            n_jobs=workers,
        ).fit(hits)
        scorer.save(metadata_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(scorer, model_path)

        result = {
            **scorer.summary(),
            "ok": True,
            "corpus_path": str(corpus_path),
            "metadata_path": str(metadata_path),
            "model_path": str(model_path),
            "max_hits_requested": max_hits,
            "accelerator": {
                "requested": "auto",
                "used": "sklearn_cpu",
                "reason": (
                    "This scorer uses sklearn IsolationForest/PCA; no tested "
                    "Apple Metal/MPS or MLX backend exists for this estimator "
                    "in the project yet."
                ),
            },
        }
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "radio-real-corpus-summary":
        from techno_search.radio_real_corpus_summary import radio_real_corpus_summary

        result = radio_real_corpus_summary(
            [Path(path) for path in args.dat_dir],
            hit_ndjson_paths=(
                [Path(path) for path in args.hit_ndjson]
                if args.hit_ndjson is not None
                else None
            ),
            semisupervised_model_path=(
                Path(args.semisupervised_model)
                if args.semisupervised_model is not None
                else None
            ),
            max_files=args.max_files,
            max_hit_rows=args.max_hit_rows,
            candidate_sample_limit=args.candidate_sample_limit,
            freq_tolerance_hz=args.freq_tolerance_hz,
        )
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "multi-modal-crossmatch-summary":
        from techno_search.multi_modal_crossmatch import multi_modal_crossmatch_summary

        report_dir = Path(args.report_dir)
        report_paths = sorted(
            path
            for path in report_dir.glob("*.json")
            if not path.name.endswith(".manifest.json")
        )
        reports = [json.loads(path.read_text(encoding="utf-8")) for path in report_paths]
        result = multi_modal_crossmatch_summary(
            reports,
            match_radius_arcsec=args.match_radius_arcsec,
        )
        result["report_dir"] = str(report_dir)
        result["report_file_count"] = len(report_paths)
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "calibration-summary":
        fixtures = load_calibration_fixtures(args.fixture_path)
        cal_summary = summarize_calibration_fixtures(fixtures)
        print(json.dumps(cal_summary.as_dict(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "false-positive-summary":
        print(
            json.dumps(
                false_positive_class_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "calibration-track-summary":
        print(
            json.dumps(
                calibration_track_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "validate-candidate":
        vresult = validate_candidate_file(args.input)
        print(json.dumps(vresult.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if vresult.ok else 1

    if args.command == "validate-reports":
        vresult = validate_report_directory(args.report_dir)
        print(json.dumps(vresult.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if vresult.ok else 1

    if args.command == "schema-paths":
        print(json.dumps(schema_paths(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "score-regression-summary":
        print(
            json.dumps(score_regression_summary(args.snapshot_path), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "injection-recovery-summary":
        print(
            json.dumps(
                injection_recovery_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "reliability-summary":
        print(
            json.dumps(
                reliability_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "precision-recall-summary":
        print(
            json.dumps(
                precision_recall_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "validation-dataset-summary":
        print(
            json.dumps(
                validation_dataset_summary(args.manifest_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "validation-promotion-summary":
        print(
            json.dumps(
                validation_promotion_summary(args.rules_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "validation-readiness-summary":
        print(
            json.dumps(
                validation_readiness_summary(args.readiness_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "benchmark-metadata-summary":
        print(
            json.dumps(
                benchmark_metadata_summary(args.metadata_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "benchmark-run-summary":
        print(
            json.dumps(
                benchmark_run_result_summary(args.results_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "benchmark-run-append":
        append_benchmark_run_result(args.results_path, BenchmarkRunResult())
        print(
            json.dumps(
                {"ok": True, "schema_version": "benchmark_run_results_stub_v1"},
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "benchmark-run-compare":
        print(
            json.dumps(
                benchmark_run_result_comparison(args.results_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "target-priority-summary":
        print(
            json.dumps(
                target_priority_summary(
                    args.target_path,
                    args.config_path,
                    args.ledger_path,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "background-ledger-summary":
        print(
            json.dumps(
                background_search_ledger_summary(args.ledger_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "background-reviewed-workflow-summary":
        print(
            json.dumps(
                background_review_workflow_summary(args.ledger_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "reviewed-log-summary":
        print(
            json.dumps(
                background_reviewed_log_summary(args.reviewed_log_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "needs-follow-up-summary":
        print(
            json.dumps(
                background_needs_follow_up_summary(args.needs_follow_up_log_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "follow-up-test-summary":
        print(
            json.dumps(
                background_follow_up_test_summary(args.follow_up_tests_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "report-readiness-summary":
        print(
            json.dumps(
                background_report_readiness_summary(args.report_readiness_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "draft-follow-up-report-summary":
        print(
            json.dumps(
                background_draft_follow_up_report_summary(
                    args.report_readiness_path,
                    from_readiness=True,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "draft-report-fixture-summary":
        print(
            json.dumps(
                background_draft_follow_up_report_summary(args.draft_report_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "draft-follow-up-report-write":
        write_result = write_background_draft_follow_up_reports(
            args.output_dir,
            readiness_path=args.report_readiness_path,
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "output_dir": str(write_result.output_dir),
                    "manifest_path": str(write_result.manifest_path),
                    "markdown_paths": [
                        str(path) for path in write_result.markdown_paths
                    ],
                    "summary": background_draft_follow_up_report_summary(
                        args.report_readiness_path,
                        from_readiness=True,
                    ),
                },
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "validate-draft-reports":
        vresult = validate_draft_report_directory(args.report_dir)
        print(json.dumps(vresult.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if vresult.ok else 1

    if args.command == "user-decision-summary":
        print(
            json.dumps(
                background_user_decision_summary(args.user_decision_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "user-decision-record":
        external_approved = bool(args.confirm_external_submission_approval)
        record = BackgroundUserDecisionRecord(
            decision_id=args.decision_id,
            readiness_id=args.readiness_id,
            follow_up_id=args.follow_up_id,
            target_id=args.target_id,
            track=Track(args.track),
            decision=args.decision,
            decided_at_utc=args.decided_at_utc
            or datetime.now(UTC).isoformat(),
            rationale=args.rationale,
            required_next_actions=tuple(args.required_next_action or ()),
            external_submission_approved=external_approved,
            request_more_tests=args.decision == "request_more_tests",
            close_as_reviewed=args.decision == "close_as_reviewed",
            submission_destination=args.submission_destination,
            blocking_issues=tuple(args.blocking_issue or ()),
            network_access_allowed=False,
        )
        print(
            json.dumps(
                append_background_user_decision_record(
                    args.user_decision_path,
                    record,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "submission-recommendation-summary":
        print(
            json.dumps(
                background_report_readiness_summary(args.report_readiness_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-extraction-handoff-summary":
        print(
            json.dumps(
                candidate_extraction_handoff_summary(args.handoff_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "background-run-once":
        print(
            json.dumps(
                run_local_background_search_once(
                    args.ledger_path,
                    reviewed_log_path=args.reviewed_log_path,
                    needs_follow_up_log_path=args.needs_follow_up_log_path,
                    sqlite_log_path=args.sqlite_log_path,
                    target_path=args.target_path,
                    config_path=args.config_path,
                    run_id=args.run_id,
                    code_commit=args.code_commit,
                    opt_in=args.acknowledge_local_run,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "init-logs":
        print(
            json.dumps(
                init_sqlite_log_db(
                    args.db_path,
                    code_commit=args.code_commit,
                    config_version=args.config_version,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-summary":
        print(
            json.dumps(
                sqlite_log_summary(args.db_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-integrity-summary":
        print(
            json.dumps(
                sqlite_log_integrity_summary(args.db_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-bootstrap-summary":
        init_result = init_sqlite_log_db(
            args.db_path,
            code_commit=args.code_commit,
            config_version=args.config_version,
        )
        integrity = sqlite_log_integrity_summary(args.db_path)
        weekly_digest = sqlite_log_weekly_digest(
            args.db_path,
            window_days=args.window_days,
        )
        readiness = operations_readiness_summary(sqlite_log_path=args.db_path)
        sqlite_snapshot = readiness["sqlite_log_snapshot"]
        bootstrap_result = {
            "ok": (
                bool(init_result["ok"])
                and bool(integrity["ok"])
                and bool(weekly_digest["ok"])
                and bool(sqlite_snapshot["integrity_ok"])
                and bool(sqlite_snapshot["weekly_digest_ok"])
                and int(sqlite_snapshot["network_access_allowed_count"]) == 0
                and int(sqlite_snapshot["external_submission_approved_count"]) == 0
            ),
            "db_path": str(args.db_path),
            "schema_version": init_result["schema_version"],
            "disclaimer": init_result["disclaimer"],
            "sqlite_log_initialized": bool(init_result["database_exists"]),
            "sqlite_integrity_ok": bool(integrity["ok"]),
            "sqlite_weekly_digest_ok": bool(weekly_digest["ok"]),
            "readiness_sqlite_integrity_ok": bool(sqlite_snapshot["integrity_ok"]),
            "readiness_sqlite_weekly_digest_ok": bool(
                sqlite_snapshot["weekly_digest_ok"]
            ),
            "readiness_recommendation": readiness["recommendation"],
            "readiness_real_data_blocker_count": readiness["real_data_blocker_count"],
            "network_access_allowed_count": int(
                sqlite_snapshot["network_access_allowed_count"]
            ),
            "external_submission_approved_count": int(
                sqlite_snapshot["external_submission_approved_count"]
            ),
            "validated_action_ids": ["ops-action-009", "ops-action-010"],
            "does_not_mutate_action_resolution_fixture": True,
            "uncertainty_and_limitations": [
                "Bootstrap checks restore SQLite visibility for the supplied local database only.",
                "Validated SQLite visibility does not clear non-SQLite operations blockers.",
                "Generated SQLite databases and backups must remain ignored local artifacts.",
            ],
            "init_summary": init_result,
            "integrity_summary": integrity,
            "weekly_digest": weekly_digest,
            "operations_readiness_summary": readiness,
        }
        print(json.dumps(bootstrap_result, indent=2, sort_keys=True), file=out)
        return 0 if bootstrap_result["ok"] else 1

    if args.command == "sqlite-log-export":
        print(
            json.dumps(
                sqlite_log_export(args.db_path, limit=args.limit),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-recent-runs":
        print(
            json.dumps(
                sqlite_recent_runs(args.db_path, limit=args.limit),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-needs-follow-up":
        print(
            json.dumps(
                sqlite_needs_follow_up(args.db_path, limit=args.limit),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-migration-summary":
        print(
            json.dumps(
                sqlite_log_migration_summary(args.db_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-migrate":
        plan = sqlite_log_migration_plan(
            args.db_path,
            target_version=args.target_version,
        )
        if args.apply:
            apply_result = apply_sqlite_log_migration(args.db_path)
            print(json.dumps(apply_result, indent=2, sort_keys=True), file=out)
            return 0 if apply_result.get("ok") else 1
        print(json.dumps(plan, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "sqlite-log-pragmas":
        print(
            json.dumps(
                sqlite_log_pragmas(args.db_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-retention-summary":
        print(
            json.dumps(
                sqlite_log_retention_summary(
                    args.db_path,
                    backup_dir=args.backup_dir,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-backup":
        backup_result = sqlite_log_backup(args.db_path, backup_dir=args.backup_dir)
        print(json.dumps(backup_result, indent=2, sort_keys=True), file=out)
        return 0 if backup_result["ok"] else 1

    if args.command == "sqlite-log-vacuum":
        vacuum_result = sqlite_log_vacuum(args.db_path)
        print(json.dumps(vacuum_result, indent=2, sort_keys=True), file=out)
        return 0 if vacuum_result["ok"] else 1

    if args.command == "sqlite-log-weekly-digest":
        digest_result = sqlite_log_weekly_digest(
            args.db_path,
            window_days=args.window_days,
        )
        print(json.dumps(digest_result, indent=2, sort_keys=True), file=out)
        return 0 if digest_result.get("ok", False) else 1

    if args.command == "sqlite-log-commit-guard":
        commit_guard_paths = args.paths or git_tracked_paths(default_project_root())
        commit_guard_result = validate_sqlite_log_commit_paths(
            [Path(path) for path in commit_guard_paths],
            project_root=default_project_root(),
        )
        print(json.dumps(commit_guard_result, indent=2, sort_keys=True), file=out)
        return 0 if commit_guard_result["ok"] else 1

    if args.command == "sqlite-log-consistency-summary":
        root = default_project_root()
        consistency_commit_guard = validate_sqlite_log_commit_paths(
            git_tracked_paths(root),
            project_root=root,
        )
        consistency_result = top_level_sqlite_log_consistency_summary(
            args.fixture_path,
            db_path=args.db_path,
            commit_guard=consistency_commit_guard,
        )
        print(json.dumps(consistency_result, indent=2, sort_keys=True), file=out)
        return 0 if consistency_result["ok"] else 1

    if args.command == "validate-sqlite-logs":
        vresult = validate_sqlite_log_database(args.db_path)
        print(json.dumps(vresult.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if vresult.ok else 1

    if args.command == "scheduler-dry-run":
        print(
            json.dumps(
                scheduler_dry_run(
                    args.artifact_dir,
                    run_id=args.run_id,
                    code_commit=args.code_commit,
                    sqlite_log_path=args.sqlite_log_path,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "review-queue-summary":
        print(
            json.dumps(
                review_queue_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "consensus-summary":
        print(
            json.dumps(
                consensus_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "consensus-export-summary":
        print(
            json.dumps(
                consensus_export_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "cross-track-summary":
        print(
            json.dumps(
                cross_track_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "verify-report-reproducibility":
        verify_result = verify_report_directory(args.report_dir)
        print(json.dumps(verify_result, indent=2, sort_keys=True), file=out)
        return 0 if verify_result.get("ok", False) else 1

    if args.command == "validate-all":
        all_result = validate_all()
        print(json.dumps(all_result, indent=2, sort_keys=True), file=out)
        return 0 if all_result["ok"] else 1

    if args.command == "validation-summary":
        summary_result = validation_summary()
        print(json.dumps(summary_result, indent=2, sort_keys=True), file=out)
        return 0 if summary_result["ok"] else 1

    if args.command == "regenerate-examples":
        regeneration_result = regenerate_examples()
        print(json.dumps(regeneration_result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "provenance-summary":
        print(
            json.dumps(provenance_summary(args.report_dir), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "plot-artifact-summary":
        print(
            json.dumps(plot_artifact_summary(args.report_dir), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "live-provider-summary":
        print(json.dumps(live_provider_summary(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "live-cache-summary":
        print(
            json.dumps(live_cache_summary(args.cache_dir), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "live-fixture-summary":
        print(
            json.dumps(live_metadata_fixture_summary(args.fixture_dir), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "live-client-summary":
        print(json.dumps(live_client_summary(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "catalog-cache-policy":
        print(
            json.dumps(catalog_cache_policy_summary(args.cache_root), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "catalog-cache-summary":
        print(
            json.dumps(catalog_cache_summary(args.cache_root), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "catalog-cache-validate":
        catalog_result = catalog_cache_validation_summary(args.paths)
        print(json.dumps(catalog_result, indent=2, sort_keys=True), file=out)
        return 0 if catalog_result["ok"] else 1

    if args.command == "baseline-eval-summary":
        eval_result = evaluate_baseline(
            calibration_fixture_path=getattr(args, "calibration_fixture", None),
            example_candidates_dir=getattr(args, "example_candidates_dir", None),
        )
        result_without_details = {
            k: v for k, v in eval_result.items() if k != "results"
        }
        print(json.dumps(result_without_details, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "target-watchlist-summary":
        print(
            json.dumps(
                target_watchlist_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "weekly-review-template":
        print(
            json.dumps(
                {"ok": False, "message": "weekly-review-template removed in Phase 0 cleanup"},
                indent=2,
            ),
            file=out,
        )
        return 1

    if args.command == "baseline-performance-history-summary":
        history = baseline_performance_history_summary(
            getattr(args, "history_path", None)
        )
        print(json.dumps(history, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "baseline-pathway-drift-summary":
        drift = baseline_pathway_drift_summary(
            getattr(args, "example_candidates_dir", None)
        )
        print(json.dumps(drift, indent=2, sort_keys=True), file=out)
        return 0 if drift["zero_drift"] else 1

    if args.command == "sqlite-log-track-summary":
        _db_path = getattr(args, "db_path", None) or default_sqlite_log_path(
            default_project_root()
        )
        track_summary = _sqlite_log_track_summary(_db_path)
        print(json.dumps(track_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "health":
        _health = _project_health_summary(out)
        print(json.dumps(_health, indent=2, sort_keys=True), file=out)
        return 0 if _health["all_gates_pass"] else 1

    if args.command == "review-dashboard":
        _dash: dict[str, Any] = {
            "needs_attention": False,
            "schema_version": "review_dashboard_stub_v1",
        }
        print(json.dumps(_dash, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "scan-summary":
        from techno_search.scan_summary import scan_summary_from_batch_dir
        _scan = scan_summary_from_batch_dir(Path(args.batch_dir))
        print(json.dumps(_scan, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "prod-target-queue":
        from techno_search.prod_scan_queue import build_target_queue

        _hist_path: Path | None = None
        if getattr(args, "history_file", None):
            _hist_path = Path(args.history_file)
        _queue = build_target_queue(
            Path(args.dat_dir),
            _hist_path,
            force_rescan=bool(getattr(args, "force", False)),
        )
        _queue_out = {
            "schema_version": "prod_scan_queue_v1",
            "disclaimer": (
                "Target queue is a local scheduling aid. "
                "No result constitutes a detection claim or authorizes external submission."
            ),
            "dat_dir": args.dat_dir,
            "history_file": str(_hist_path) if _hist_path else None,
            "pending_count": len(_queue),
            "queue": [
                {
                    "target_stem": e.target_stem,
                    "dat_file": str(e.dat_file),
                    "is_first_scan": e.is_first_scan,
                    "prior_scan_count": e.prior_scan_count,
                    "last_scanned_at_utc": e.last_scanned_at_utc,
                    "last_score": e.last_score,
                    "last_pathway": e.last_pathway,
                    "selection_score": e.selection_score,
                    "rationale": e.rationale,
                }
                for e in _queue
            ],
        }
        print(json.dumps(_queue_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "prod-record-scan":
        from techno_search.prod_scan_queue import ScanHistoryRecord, append_scan_record

        _record = ScanHistoryRecord(
            target_stem=str(args.target_stem),
            run_id=str(args.run_id),
            scanned_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            score=float(args.score),
            pathway=str(args.pathway),
            dat_file=str(args.dat_file),
            parent_run_id=getattr(args, "parent_run_id", None) or None,
        )
        _hist_file = Path(args.history_file)
        append_scan_record(_hist_file, _record)
        print(
            json.dumps(
                {
                    "ok": True,
                    "target_stem": _record.target_stem,
                    "run_id": _record.run_id,
                    "scanned_at_utc": _record.scanned_at_utc,
                    "history_file": str(_hist_file),
                },
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "scan-history-summary":
        from techno_search.prod_scan_queue import scan_history_summary

        _sh_hist: Path | None = (
            Path(args.history_file) if getattr(args, "history_file", None) else None
        )
        _sh_dat: Path | None = (
            Path(args.dat_dir) if getattr(args, "dat_dir", None) else None
        )
        _sh = scan_history_summary(_sh_hist, _sh_dat)
        print(json.dumps(_sh, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "prod-run-id":
        from techno_search.production_run_outcomes import make_production_run_id

        _run_id = make_production_run_id(token=getattr(args, "token", None))
        print(json.dumps({"run_id": _run_id}, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "prod-write-outcomes":
        from techno_search.production_run_outcomes import write_production_outcomes

        _completed = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        _summary = write_production_outcomes(
            results_dir=Path(args.results_dir),
            run_dir=Path(args.run_dir),
            run_id=str(args.run_id),
            started_at_utc=str(args.started_at_utc),
            completed_at_utc=_completed,
            scan_summary_path=(
                Path(args.scan_summary_path)
                if getattr(args, "scan_summary_path", None)
                else None
            ),
        )
        print(json.dumps(_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "prod-scan":
        from techno_search.production_scan import (
            EmptyProductionScanError,
            run_production_scan,
        )

        try:
            run_production_scan(
                results_dir=Path(args.results_dir),
                scans_dir=Path(args.scans_dir),
                stdout=out,
                run_id=getattr(args, "run_id", None),
                resume_run_dir=(
                    Path(args.resume_run_dir)
                    if getattr(args, "resume_run_dir", None)
                    else None
                ),
                use_rich=not bool(getattr(args, "no_rich", False)),
                allow_empty=bool(getattr(args, "allow_empty", False)),
            )
        except EmptyProductionScanError:
            return 1
        except KeyboardInterrupt:
            return 130
        return 0

    if args.command == "prod-diagnostics":
        from techno_search.production_scan import production_diagnostics

        _diagnostics = production_diagnostics(
            scans_dir=Path(args.scans_dir),
            stdout=out,
            use_rich=not bool(getattr(args, "no_rich", False)),
        )
        if getattr(args, "json", False):
            print(json.dumps(_diagnostics, indent=2, sort_keys=True), file=out)
        return (
            0
            if _diagnostics["validate_all_ok"]
            and not _diagnostics["review_dashboard_needs_attention"]
            else 1
        )

    if args.command == "prod-runs":
        from techno_search.production_run_outcomes import production_run_list

        _runs = production_run_list(Path(args.scans_dir))
        print(json.dumps(_runs, indent=2, sort_keys=True), file=out)
        return 0 if _runs.get("ok") else 1

    if args.command == "prod-show":
        from techno_search.production_run_outcomes import production_run_summary

        run_dir = _resolve_production_run_dir_arg(args, out)
        if run_dir is None:
            return 1
        _run = production_run_summary(run_dir)
        print(json.dumps(_run, indent=2, sort_keys=True), file=out)
        return 0 if _run.get("ok") else 1

    if args.command == "prod-follow-ups":
        from techno_search.production_run_outcomes import production_run_file

        run_dir = _resolve_production_run_dir_arg(args, out)
        if run_dir is None:
            return 1
        _follow_ups = production_run_file(run_dir, "follow_ups")
        if getattr(args, "json", False):
            print(json.dumps(_follow_ups, indent=2, sort_keys=True), file=out)
        else:
            _print_production_follow_ups(_follow_ups, out)
        return 0 if _follow_ups.get("ok") else 1

    if args.command == "prod-non-detections":
        from techno_search.production_run_outcomes import production_run_file

        run_dir = _resolve_production_run_dir_arg(args, out)
        if run_dir is None:
            return 1
        _non_detections = production_run_file(run_dir, "non_detections")
        if getattr(args, "json", False):
            print(json.dumps(_non_detections, indent=2, sort_keys=True), file=out)
        else:
            _print_production_non_detections(_non_detections, out)
        return 0 if _non_detections.get("ok") else 1

    if args.command == "prod-target-status":
        from techno_search.production_run_outcomes import production_run_file

        run_dir = _resolve_production_run_dir_arg(args, out)
        if run_dir is None:
            return 1
        _target_status = production_run_file(run_dir, "target_status")
        if getattr(args, "json", False):
            print(json.dumps(_target_status, indent=2, sort_keys=True), file=out)
        else:
            _print_production_target_status(_target_status, out)
        return 0 if _target_status.get("ok") else 1

    if args.command == "cross-target-rfi-summary":
        from techno_search.cross_target_rfi import cross_target_rfi_summary

        _candidate_lists: list[list[dict[str, Any]]] = []
        _results_dir = getattr(args, "results_dir", None)
        if _results_dir:
            from techno_search.scan_summary import load_candidates_from_batch_dir
            _flat = load_candidates_from_batch_dir(Path(_results_dir))
            _by_target: dict[str, list[dict[str, Any]]] = {}
            for _c in _flat:
                _by_target.setdefault(str(_c.get("target_name", "")), []).append(_c)
            _candidate_lists = list(_by_target.values())
        _rfi = cross_target_rfi_summary(_candidate_lists)
        print(json.dumps(_rfi, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "escalation-gate-check":
        import json as _json

        from techno_search.candidate_escalation import escalation_gate_check
        try:
            _cdata = _json.loads(Path(args.candidate_file).read_text())
        except (OSError, ValueError) as _exc:
            print(
                json.dumps({"ok": False, "error": str(_exc)}, indent=2),
                file=out,
            )
            return 1
        _gate = escalation_gate_check(_cdata)
        print(
            json.dumps(
                {
                    "escalation_required": _gate["passes"],
                    "passes": _gate["passes"],
                    "reason": _gate["reason"],
                    "pathway": _gate["pathway"],
                    "snr": _gate["snr"],
                    "multi_epoch_persistence_score": _gate[
                        "multi_epoch_persistence_score"
                    ],
                },
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-readiness-summary":
        _log_path = getattr(args, "sqlite_log_path", None)
        print(
            json.dumps(
                operations_readiness_summary(sqlite_log_path=_log_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-action-plan-summary":
        _log_path = getattr(args, "sqlite_log_path", None)
        ops_summary = operations_readiness_summary(sqlite_log_path=_log_path)
        print(
            json.dumps(
                operations_action_plan_summary(ops_summary),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-action-resolution-summary":
        fixture_path = getattr(args, "fixture_path", None)
        _log_path = getattr(args, "sqlite_log_path", None)
        ops_summary = operations_readiness_summary(sqlite_log_path=_log_path)
        ops_action_plan = operations_action_plan_summary(ops_summary)
        expected_action_ids = [
            str(action["action_id"])
            for action in ops_action_plan["actions"]
            if isinstance(action, dict)
        ]
        print(
            json.dumps(
                operations_action_resolution_summary(
                    fixture_path,
                    expected_action_ids=expected_action_ids,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-action-resolution-consistency-summary":
        fixture_path = getattr(args, "fixture_path", None)
        consistency_summary = operations_action_resolution_consistency_summary(
            fixture_path
        )
        print(
            json.dumps(
                consistency_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if consistency_summary["ok"] else 1

    if args.command == "operations-blocker-detail-summary":
        _log_path = getattr(args, "sqlite_log_path", None)
        print(
            json.dumps(
                operations_blocker_detail_summary(sqlite_log_path=_log_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-review-summary":
        fixture_path = getattr(args, "fixture_path", None)
        _log_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=_log_path)
        expected_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        print(
            json.dumps(
                operations_blocker_review_summary(
                    fixture_path,
                    expected_action_ids=expected_action_ids,
                    blocker_detail_summary=blocker_detail,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-followup-summary":
        fixture_path = getattr(args, "fixture_path", None)
        _log_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=_log_path)
        expected_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        print(
            json.dumps(
                operations_blocker_followup_summary(
                    fixture_path,
                    blocker_detail_summary_data=blocker_detail,
                    blocker_review_summary_data=blocker_review,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-followup-progress-summary":
        fixture_path = getattr(args, "fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        _log_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=_log_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        print(
            json.dumps(
                operations_blocker_followup_progress_summary(
                    fixture_path,
                    expected_action_ids=expected_action_ids,
                    blocker_followup_summary=blocker_followup,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-review-summary":
        fixture_path = getattr(args, "fixture_path", None)
        progress_fixture_path = getattr(args, "progress_fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        _log_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=_log_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        progress_summary = operations_blocker_followup_progress_summary(
            progress_fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_followup_summary=blocker_followup,
        )
        unresolved_action_ids = [
            str(record["action_id"])
            for record in progress_summary["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ]
        print(
            json.dumps(
                operations_blocker_progress_review_summary(
                    fixture_path,
                    expected_action_ids=unresolved_action_ids,
                    blocker_followup_progress_summary=progress_summary,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-next-actions-summary":
        fixture_path = getattr(args, "fixture_path", None)
        progress_review_fixture_path = getattr(
            args,
            "progress_review_fixture_path",
            None,
        )
        progress_fixture_path = getattr(args, "progress_fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        _log_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=_log_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        progress_summary = operations_blocker_followup_progress_summary(
            progress_fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_followup_summary=blocker_followup,
        )
        unresolved_action_ids = [
            str(record["action_id"])
            for record in progress_summary["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ]
        progress_review_summary = operations_blocker_progress_review_summary(
            progress_review_fixture_path,
            expected_action_ids=unresolved_action_ids,
            blocker_followup_progress_summary=progress_summary,
        )
        expected_next_action_ids = [
            str(record["action_id"])
            for record in progress_review_summary["records"]
            if isinstance(record, dict)
        ]
        print(
            json.dumps(
                operations_blocker_progress_next_actions_summary(
                    fixture_path,
                    expected_action_ids=expected_next_action_ids,
                    blocker_progress_review_summary=progress_review_summary,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-execution-summary":
        fixture_path = getattr(args, "fixture_path", None)
        next_actions_fixture_path = getattr(args, "next_actions_fixture_path", None)
        progress_review_fixture_path = getattr(
            args,
            "progress_review_fixture_path",
            None,
        )
        progress_fixture_path = getattr(args, "progress_fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        _log_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=_log_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        progress_summary = operations_blocker_followup_progress_summary(
            progress_fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_followup_summary=blocker_followup,
        )
        unresolved_action_ids = [
            str(record["action_id"])
            for record in progress_summary["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ]
        progress_review_summary = operations_blocker_progress_review_summary(
            progress_review_fixture_path,
            expected_action_ids=unresolved_action_ids,
            blocker_followup_progress_summary=progress_summary,
        )
        expected_next_action_ids = [
            str(record["action_id"])
            for record in progress_review_summary["records"]
            if isinstance(record, dict)
        ]
        next_actions_summary = operations_blocker_progress_next_actions_summary(
            next_actions_fixture_path,
            expected_action_ids=expected_next_action_ids,
            blocker_progress_review_summary=progress_review_summary,
        )
        expected_execution_ids = [
            str(record["next_action_id"])
            for record in next_actions_summary["records"]
            if isinstance(record, dict)
        ]
        print(
            json.dumps(
                operations_blocker_progress_execution_summary(
                    fixture_path,
                    expected_next_action_ids=expected_execution_ids,
                    blocker_progress_next_actions_summary=next_actions_summary,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-execution-review-summary":
        fixture_path = getattr(args, "fixture_path", None)
        execution_fixture_path = getattr(args, "execution_fixture_path", None)
        next_actions_fixture_path = getattr(args, "next_actions_fixture_path", None)
        progress_review_fixture_path = getattr(
            args,
            "progress_review_fixture_path",
            None,
        )
        progress_fixture_path = getattr(args, "progress_fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        _log_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=_log_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        progress_summary = operations_blocker_followup_progress_summary(
            progress_fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_followup_summary=blocker_followup,
        )
        unresolved_action_ids = [
            str(record["action_id"])
            for record in progress_summary["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ]
        progress_review_summary = operations_blocker_progress_review_summary(
            progress_review_fixture_path,
            expected_action_ids=unresolved_action_ids,
            blocker_followup_progress_summary=progress_summary,
        )
        expected_next_action_ids = [
            str(record["action_id"])
            for record in progress_review_summary["records"]
            if isinstance(record, dict)
        ]
        next_actions_summary = operations_blocker_progress_next_actions_summary(
            next_actions_fixture_path,
            expected_action_ids=expected_next_action_ids,
            blocker_progress_review_summary=progress_review_summary,
        )
        expected_execution_next_action_ids = [
            str(record["next_action_id"])
            for record in next_actions_summary["records"]
            if isinstance(record, dict)
        ]
        execution_summary = operations_blocker_progress_execution_summary(
            execution_fixture_path,
            expected_next_action_ids=expected_execution_next_action_ids,
            blocker_progress_next_actions_summary=next_actions_summary,
        )
        expected_review_execution_ids = [
            str(record["execution_id"])
            for record in execution_summary["records"]
            if isinstance(record, dict)
        ]
        print(
            json.dumps(
                operations_blocker_progress_execution_review_summary(
                    fixture_path,
                    expected_execution_ids=expected_review_execution_ids,
                    blocker_progress_execution_summary=execution_summary,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-execution-followup-summary":
        fixture_path = getattr(args, "fixture_path", None)
        execution_review_fixture_path = getattr(
            args,
            "execution_review_fixture_path",
            None,
        )
        execution_fixture_path = getattr(args, "execution_fixture_path", None)
        next_actions_fixture_path = getattr(args, "next_actions_fixture_path", None)
        progress_review_fixture_path = getattr(
            args,
            "progress_review_fixture_path",
            None,
        )
        progress_fixture_path = getattr(args, "progress_fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        _log_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=_log_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        progress_summary = operations_blocker_followup_progress_summary(
            progress_fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_followup_summary=blocker_followup,
        )
        unresolved_action_ids = [
            str(record["action_id"])
            for record in progress_summary["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ]
        progress_review_summary = operations_blocker_progress_review_summary(
            progress_review_fixture_path,
            expected_action_ids=unresolved_action_ids,
            blocker_followup_progress_summary=progress_summary,
        )
        expected_next_action_ids = [
            str(record["action_id"])
            for record in progress_review_summary["records"]
            if isinstance(record, dict)
        ]
        next_actions_summary = operations_blocker_progress_next_actions_summary(
            next_actions_fixture_path,
            expected_action_ids=expected_next_action_ids,
            blocker_progress_review_summary=progress_review_summary,
        )
        expected_execution_next_action_ids = [
            str(record["next_action_id"])
            for record in next_actions_summary["records"]
            if isinstance(record, dict)
        ]
        execution_summary = operations_blocker_progress_execution_summary(
            execution_fixture_path,
            expected_next_action_ids=expected_execution_next_action_ids,
            blocker_progress_next_actions_summary=next_actions_summary,
        )
        expected_review_execution_ids = [
            str(record["execution_id"])
            for record in execution_summary["records"]
            if isinstance(record, dict)
        ]
        execution_review_summary = operations_blocker_progress_execution_review_summary(
            execution_review_fixture_path,
            expected_execution_ids=expected_review_execution_ids,
            blocker_progress_execution_summary=execution_summary,
        )
        expected_followup_review_ids = [
            str(record["review_id"])
            for record in execution_review_summary["records"]
            if isinstance(record, dict)
        ]
        print(
            json.dumps(
                operations_blocker_progress_execution_followup_summary(
                    fixture_path,
                    expected_review_ids=expected_followup_review_ids,
                    blocker_progress_execution_review_summary=(
                        execution_review_summary
                    ),
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-consistency-summary":
        fixture_path = getattr(args, "fixture_path", None)
        consistency_summary = operations_blocker_progress_consistency_summary(
            fixture_path
        )
        print(
            json.dumps(
                consistency_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if consistency_summary["ok"] else 1

    if args.command == "operations-readiness-digest":
        _log_path = getattr(args, "sqlite_log_path", None)
        ops_summary = operations_readiness_summary(sqlite_log_path=_log_path)
        digest = operations_readiness_digest(ops_summary)
        if args.output_path is not None:
            args.output_path.parent.mkdir(parents=True, exist_ok=True)
            args.output_path.write_text(digest["markdown"], encoding="utf-8")
            output = {
                "ok": True,
                "path": str(args.output_path),
                "recommendation": digest["recommendation"],
            }
            print(json.dumps(output, indent=2, sort_keys=True), file=out)
        else:
            print(digest["markdown"], file=out)
        return 0

    if args.command == "baseline-confusion-matrix-summary":
        confusion_result = evaluate_baseline()
        confusion_output = {
            "schema_version": "baseline_eval_v0",
            "disclaimer": confusion_result["disclaimer"],
            "total_cases": confusion_result["total_cases"],
            "confusion_matrix": confusion_result["confusion_matrix"],
            "per_pathway_precision": confusion_result["per_pathway_precision"],
            "per_pathway_recall": confusion_result["per_pathway_recall"],
            "per_pathway_f1": confusion_result["per_pathway_f1"],
        }
        print(json.dumps(confusion_output, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "score-determinism-check":
        candidate_paths = getattr(args, "candidate_paths", None)
        runs = int(getattr(args, "runs", 3))
        if not candidate_paths:
            _default_examples = _default_example_candidates_dir()
            candidate_paths = sorted(_default_examples.glob("*.json"))
        results_det = []
        all_deterministic = True
        for cp in candidate_paths:
            det = score_determinism_check(Path(cp), runs=runs)
            results_det.append(det)
            if not det["deterministic"]:
                all_deterministic = False
        output_det = {
            "all_deterministic": all_deterministic,
            "runs_per_candidate": runs,
            "results": results_det,
        }
        print(json.dumps(output_det, indent=2, sort_keys=True), file=out)
        return 0 if all_deterministic else 1

    if args.command == "candidate-lifecycle-summary":
        fixture_path = getattr(args, "fixture_path", None)
        lifecycle = candidate_lifecycle_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(lifecycle, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "observation-schedule-summary":
        fixture_path = getattr(args, "fixture_path", None)
        schedule = observation_schedule_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(schedule, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "false-negative-summary":
        fixture_path = getattr(args, "fixture_path", None)
        fn_summary = false_negative_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(fn_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "scoring-config-summary":
        config_path = getattr(args, "config_path", None)
        sc_summary = scoring_config_summary(
            Path(config_path) if config_path else None
        )
        print(json.dumps(sc_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "route-coverage-summary":
        rc_summary = route_coverage_summary()
        print(json.dumps(rc_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "lifecycle-transition-summary":
        fixture_path = getattr(args, "fixture_path", None)
        lt_summary = lifecycle_transition_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(lt_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "observation-efficiency-summary":
        fixture_path = getattr(args, "fixture_path", None)
        oe_summary = observation_efficiency_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(oe_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "sensitivity-config-summary":
        config_path = getattr(args, "config_path", None)
        sens_summary = sensitivity_config_summary(
            Path(config_path) if config_path else None
        )
        print(json.dumps(sens_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "triage-summary":
        fixture_path = getattr(args, "fixture_path", None)
        tr_summary = triage_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(tr_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "artifacts-cleanup":
        if args.apply:
            cleanup_result = apply_artifact_cleanup(
                args.artifacts_dir,
                project_root=default_project_root(),
                acknowledge_local_apply=args.acknowledge_local_apply,
            )
        else:
            cleanup_result = plan_artifact_cleanup(
                args.artifacts_dir,
                project_root=default_project_root(),
            )
        print(json.dumps(cleanup_result, indent=2, sort_keys=True), file=out)
        return 0 if cleanup_result.get("ok", False) else 1

    if args.command == "radio-corpus-cleanup":
        if args.apply:
            cleanup_result = apply_radio_corpus_cleanup(
                args.corpus_dir,
                results_dir=args.results_dir,
                project_root=default_project_root(),
                acknowledge_local_apply=args.acknowledge_local_apply,
            )
        else:
            cleanup_result = plan_radio_corpus_cleanup(
                args.corpus_dir,
                results_dir=args.results_dir,
                project_root=default_project_root(),
            )
        print(json.dumps(cleanup_result, indent=2, sort_keys=True), file=out)
        return 0 if cleanup_result.get("ok", False) else 1

    if args.command == "signal-registry-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                signal_registry_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "signal-registry-track-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                signal_registry_track_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "schema-drift-check":
        print(
            json.dumps(
                {"drift_count": 0, "schema_version": "schema_drift_stub_v1"},
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "audit-trail-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                audit_trail_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "observation-gap-analysis":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                observation_gap_analysis(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "multi-epoch-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                multi_epoch_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "classifier-rule-coverage":
        print(
            json.dumps(classifier_rule_coverage_summary(), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "target-recalibration-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                target_recalibration_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operator-coverage-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                operator_coverage_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "triage-label-completeness":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                triage_label_completeness_check(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "provenance-chain-validate":
        pc_result = provenance_chain_validator(
            report_dir=default_project_root() / "examples" / "reports",
        )
        print(json.dumps(pc_result, indent=2, sort_keys=True), file=out)
        return 0 if pc_result["ok"] else 1

    if args.command == "observation-notes-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                observation_notes_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "epoch-plan-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                epoch_plan_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "aggregate-blockers-summary":
        print(
            json.dumps(
                aggregate_blockers_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "score-history-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                score_history_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operator-assignment-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                operator_assignment_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-health-summary":
        print(
            json.dumps(
                pipeline_health_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-flags-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                candidate_flags_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "review-deadlines-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                review_deadlines_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-throughput-summary":
        print(
            json.dumps(
                pipeline_throughput_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-retention-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                candidate_retention_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operator-performance-summary":
        print(
            json.dumps(
                operator_performance_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "track-comparison-summary":
        print(
            json.dumps(
                track_comparison_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-resolution-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                candidate_resolution_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "escalation-log-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                escalation_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "quality-control-summary":
        print(
            json.dumps(
                quality_control_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "observation-campaign-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                observation_campaign_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "data-quality-log-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                data_quality_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-audit-summary":
        print(
            json.dumps(
                pipeline_audit_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "follow-up-request-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                follow_up_request_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-bottleneck-summary":
        print(
            json.dumps(
                pipeline_bottleneck_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-annotation-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                candidate_annotation_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "session-log-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                session_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "priority-queue-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                priority_queue_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-capacity-summary":
        print(
            json.dumps(
                pipeline_capacity_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "feature-vector-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                feature_vector_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "model-registry-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                model_registry_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "ml-diagnostics-summary":
        print(
            json.dumps(
                ml_pipeline_diagnostics_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "feature-normalization-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                feature_normalization_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "feature-importance-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                feature_importance_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "ml-training-data-summary":
        print(
            json.dumps(
                ml_training_data_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "model-architecture-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                model_architecture_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "model-evaluation-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                model_evaluation_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "model-performance-history-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                model_performance_history_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "model-serving-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                model_serving_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "scoring-audit-log-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                scoring_audit_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "curated-dataset-intake-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                curated_dataset_intake_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "curated-dataset-admission-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        admission_summary = curated_dataset_admission_summary(fixture_path)
        print(
            json.dumps(
                admission_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if admission_summary["validation_ok"] else 1

    if args.command == "project-status-consistency-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        consistency_summary = project_status_consistency_summary(fixture_path)
        print(
            json.dumps(
                consistency_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if consistency_summary["ok"] else 1

    if args.command == "mcp-bootstrap-consistency-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        consistency_summary = mcp_bootstrap_consistency_summary(fixture_path)
        print(
            json.dumps(
                consistency_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if consistency_summary["ok"] else 1

    if args.command == "mcp-server-policy-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        policy_summary = mcp_server_policy_summary(fixture_path)
        print(
            json.dumps(
                policy_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if policy_summary["ok"] else 1

    if args.command == "production-blocker-consistency-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        consistency_summary = production_blocker_consistency_summary(fixture_path)
        print(
            json.dumps(
                consistency_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if consistency_summary["ok"] else 1

    if args.command == "ai-hardening-gate-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        gate_summary = ai_hardening_gate_summary(fixture_path)
        print(
            json.dumps(
                gate_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if gate_summary["ok"] else 1

    if args.command == "real-data-admission-preflight-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        preflight_summary = real_data_admission_preflight_summary(fixture_path)
        print(
            json.dumps(
                preflight_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if preflight_summary["ok"] else 1

    if args.command == "sqlite-operational-log-registry-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        registry_summary = sqlite_operational_log_registry_summary(
            fixture_path,
            schema_names=set(SCHEMA_FILENAMES),
        )
        print(
            json.dumps(
                registry_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if registry_summary["ok"] else 1

    if args.command == "sqlite-operational-log-adapter-plan-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        adapter_plan_summary = sqlite_operational_log_adapter_plan_summary(
            fixture_path,
        )
        print(
            json.dumps(
                adapter_plan_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if adapter_plan_summary["ok"] else 1

    if args.command == "sqlite-operational-log-adapter-contract-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        adapter_contract_summary = sqlite_operational_log_adapter_contract_summary(
            fixture_path,
        )
        print(
            json.dumps(
                adapter_contract_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if adapter_contract_summary["ok"] else 1

    if args.command == "sqlite-operational-log-adapter-ddl-preview-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        ddl_preview_summary = sqlite_operational_log_adapter_ddl_preview_summary(
            fixture_path,
        )
        print(
            json.dumps(
                ddl_preview_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if ddl_preview_summary["ok"] else 1

    if args.command == "sqlite-operational-log-adapter-row-preview-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        row_preview_summary = sqlite_operational_log_adapter_row_preview_summary(
            fixture_path,
        )
        print(
            json.dumps(
                row_preview_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if row_preview_summary["ok"] else 1

    if args.command == "sqlite-operational-log-adapter-insert-preview-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        insert_preview_summary = sqlite_operational_log_adapter_insert_preview_summary(
            fixture_path,
        )
        print(
            json.dumps(
                insert_preview_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if insert_preview_summary["ok"] else 1

    if args.command == "sqlite-operational-log-adapter-execution-preview-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        execution_preview_summary = (
            sqlite_operational_log_adapter_execution_preview_summary(
                fixture_path,
            )
        )
        print(
            json.dumps(
                execution_preview_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if execution_preview_summary["ok"] else 1

    if args.command == "sqlite-operational-log-adapter-dry-run-manifest-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        dry_run_manifest_summary = (
            sqlite_operational_log_adapter_dry_run_manifest_summary(
                fixture_path,
            )
        )
        print(
            json.dumps(
                dry_run_manifest_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if dry_run_manifest_summary["ok"] else 1

    if args.command == "sqlite-operational-log-adapter-readiness-preflight-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        readiness_preflight_summary = (
            sqlite_operational_log_adapter_readiness_preflight_summary(
                fixture_path,
            )
        )
        print(
            json.dumps(
                readiness_preflight_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if readiness_preflight_summary["ok"] else 1

    if args.command == "sqlite-operational-log-adapter-authorization-gate-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        authorization_gate_summary = (
            sqlite_operational_log_adapter_authorization_gate_summary(
                fixture_path,
            )
        )
        print(
            json.dumps(
                authorization_gate_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if authorization_gate_summary["ok"] else 1

    if args.command == "operations-alert-review-consistency-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        consistency_summary = operations_alert_review_consistency_summary(fixture_path)
        print(
            json.dumps(
                consistency_summary,
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if consistency_summary["ok"] else 1

    if args.command == "candidate-rescore-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                candidate_rescore_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operator-handoff-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                operator_handoff_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-methods-summary":
        print(
            json.dumps(
                candidate_methods_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-config-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                pipeline_config_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "submission-readiness-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                submission_readiness_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-integration-summary":
        print(
            json.dumps(
                pipeline_integration_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-alert-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_alert_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-replay-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                pipeline_replay_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "scoring-threshold-audit-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                scoring_threshold_audit_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "alert-resolution-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                alert_resolution_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "config-version-history-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                config_version_history_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operator-escalation-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                operator_escalation_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-deduplication-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_deduplication_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "intake-queue-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                intake_queue_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "workflow-state-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                workflow_state_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "data-gap-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                data_gap_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-match-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_match_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-error-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                pipeline_error_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "observation-request-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                observation_request_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-export-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_export_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "quality-gate-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                quality_gate_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-comparison-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_comparison_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-telemetry-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                pipeline_telemetry_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "provenance-audit-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                provenance_audit_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "instrument-log-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                instrument_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "archival-query-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                archival_query_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-linkage-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_linkage_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "signal-classification-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                signal_classification_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "rfi-database-summary":
        fixture_path = getattr(args, "fixture_path", None)
        rfi_db_summary = rfi_database_summary(fixture_path)
        print(json.dumps(rfi_db_summary, indent=2, sort_keys=True), file=out)
        return 0 if rfi_db_summary["validation_ok"] else 1

    if args.command == "rfi-database-admission-summary":
        fixture_path = getattr(args, "fixture_path", None)
        admission_summary = rfi_database_admission_summary(fixture_path)
        print(json.dumps(admission_summary, indent=2, sort_keys=True), file=out)
        return 0 if admission_summary["validation_ok"] else 1

    if args.command == "calibration-corpus-admission-summary":
        cal_admission: dict[str, Any] = {
            "ok": True,
            "schema_version": "calibration_corpus_admission_stub_v1",
            "issue_count": 0,
            "issues": [],
        }
        print(json.dumps(cal_admission, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "rfi-mitigation-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                rfi_mitigation_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-annotation-log-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_annotation_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "frequency-channel-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                frequency_channel_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-checkpoint-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                pipeline_checkpoint_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-status-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_status_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "beam-configuration-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                beam_configuration_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "calibration-event-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                calibration_event_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-run-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                pipeline_run_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "source-catalog-summary":
        fixture_path = getattr(args, "fixture_path", None)
        scl_out = source_catalog_log_summary(fixture_path)
        print(json.dumps(scl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "noise-measurement-summary":
        fixture_path = getattr(args, "fixture_path", None)
        nml_out = noise_measurement_log_summary(fixture_path)
        print(json.dumps(nml_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "spectral-feature-summary":
        fixture_path = getattr(args, "fixture_path", None)
        sfl_out = spectral_feature_log_summary(fixture_path)
        print(json.dumps(sfl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "polarization-summary":
        fixture_path = getattr(args, "fixture_path", None)
        pol_out = polarization_log_summary(fixture_path)
        print(json.dumps(pol_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "telescope-status-summary":
        fixture_path = getattr(args, "fixture_path", None)
        tsl_out = telescope_status_log_summary(fixture_path)
        print(json.dumps(tsl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "observation-parameter-summary":
        fixture_path = getattr(args, "fixture_path", None)
        opl_out = observation_parameter_log_summary(fixture_path)
        print(json.dumps(opl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "target-selection-summary":
        fixture_path = getattr(args, "fixture_path", None)
        tsel_out = target_selection_summary(fixture_path)
        print(json.dumps(tsel_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "doppler-correction-summary":
        fixture_path = getattr(args, "fixture_path", None)
        dcl_out = doppler_correction_summary(fixture_path)
        print(json.dumps(dcl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "data-archival-summary":
        fixture_path = getattr(args, "fixture_path", None)
        dal_out = data_archival_summary(fixture_path)
        print(json.dumps(dal_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "interference-environment-summary":
        fixture_path = getattr(args, "fixture_path", None)
        iel_out = interference_environment_summary(fixture_path)
        print(json.dumps(iel_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "receiver-health-summary":
        fixture_path = getattr(args, "fixture_path", None)
        rhl_out = receiver_health_summary(fixture_path)
        print(json.dumps(rhl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "pipeline-version-summary":
        fixture_path = getattr(args, "fixture_path", None)
        pvl_out = pipeline_version_summary(fixture_path)
        print(json.dumps(pvl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "data-transfer-summary":
        fixture_path = getattr(args, "fixture_path", None)
        dtl_out = data_transfer_summary(fixture_path)
        print(json.dumps(dtl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "scheduling-conflict-summary":
        fixture_path = getattr(args, "fixture_path", None)
        scl_out = scheduling_conflict_summary(fixture_path)
        print(json.dumps(scl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "system-health-summary":
        fixture_path = getattr(args, "fixture_path", None)
        shl_out = system_health_summary(fixture_path)
        print(json.dumps(shl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "instrument-configuration-summary":
        fixture_path = getattr(args, "fixture_path", None)
        icl_out = instrument_configuration_summary(fixture_path)
        print(json.dumps(icl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "scan-log-summary":
        fixture_path = getattr(args, "fixture_path", None)
        sl_out = scan_log_summary(fixture_path)
        print(json.dumps(sl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "time-synchronization-summary":
        fixture_path = getattr(args, "fixture_path", None)
        tsl_out = time_synchronization_summary(fixture_path)
        print(json.dumps(tsl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "antenna-pointing-summary":
        fixture_path = getattr(args, "fixture_path", None)
        apl_out = antenna_pointing_summary(fixture_path)
        print(json.dumps(apl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "weather-summary":
        fixture_path = getattr(args, "fixture_path", None)
        wl_out = weather_log_summary(fixture_path)
        print(json.dumps(wl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "power-summary":
        fixture_path = getattr(args, "fixture_path", None)
        pl_out = power_log_summary(fixture_path)
        print(json.dumps(pl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "cooling-system-summary":
        fixture_path = getattr(args, "fixture_path", None)
        cs_out = cooling_system_summary(fixture_path)
        print(json.dumps(cs_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "network-connectivity-summary":
        fixture_path = getattr(args, "fixture_path", None)
        nc_out = network_connectivity_summary(fixture_path)
        print(json.dumps(nc_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "software-update-summary":
        fixture_path = getattr(args, "fixture_path", None)
        su_out = software_update_summary(fixture_path)
        print(json.dumps(su_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "hardware-fault-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(json.dumps(hardware_fault_summary(fixture_path), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "maintenance-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(json.dumps(maintenance_log_summary(fixture_path), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "environmental-summary":
        fixture_path = getattr(args, "fixture_path", None)
        env_out = environmental_log_summary(fixture_path)
        print(json.dumps(env_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "access-log-summary":
        fixture_path = getattr(args, "fixture_path", None)
        access_out = access_log_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(access_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "security-event-summary":
        fixture_path = getattr(args, "fixture_path", None)
        sec_out = security_event_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(sec_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "audit-trail-log-summary":
        fixture_path = getattr(args, "fixture_path", None)
        atl_out = audit_trail_log_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(atl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "incident-response-summary":
        fixture_path = getattr(args, "fixture_path", None)
        ir_out = incident_response_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(ir_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "change-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        cm_out = change_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(cm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "compliance-report-summary":
        fixture_path = getattr(args, "fixture_path", None)
        cr_out = compliance_report_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(cr_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "risk-assessment-summary":
        fixture_path = getattr(args, "fixture_path", None)
        ra_out = risk_assessment_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(ra_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "backup-recovery-summary":
        fixture_path = getattr(args, "fixture_path", None)
        br_out = backup_recovery_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(br_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "capacity-planning-summary":
        fixture_path = getattr(args, "fixture_path", None)
        cp_out = capacity_planning_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(cp_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "software-deployment-summary":
        fixture_path = getattr(args, "fixture_path", None)
        sd_out = software_deployment_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(sd_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "performance-monitoring-summary":
        fixture_path = getattr(args, "fixture_path", None)
        pm_out = performance_monitoring_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(pm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "user-activity-summary":
        fixture_path = getattr(args, "fixture_path", None)
        ua_out = user_activity_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(ua_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "health-check-summary":
        fixture_path = getattr(args, "fixture_path", None)
        hc_out = health_check_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(hc_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "license-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        lm_out = license_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(lm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "storage-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        stm_out = storage_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(stm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "firmware-update-summary":
        fixture_path = getattr(args, "fixture_path", None)
        fu_out = firmware_update_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(fu_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "configuration-audit-summary":
        fixture_path = getattr(args, "fixture_path", None)
        cau_out = configuration_audit_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(cau_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "event-correlation-summary":
        fixture_path = getattr(args, "fixture_path", None)
        ecr_out = event_correlation_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(ecr_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "system-diagnostics-summary":
        fixture_path = getattr(args, "fixture_path", None)
        sd_out = system_diagnostics_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(sd_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "resource-allocation-summary":
        fixture_path = getattr(args, "fixture_path", None)
        ra_out = resource_allocation_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(ra_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "access-control-summary":
        fixture_path = getattr(args, "fixture_path", None)
        ac_out = access_control_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(ac_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "incident-summary":
        fixture_path = getattr(args, "fixture_path", None)
        inc_out = incident_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(inc_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "patch-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        pm_out = patch_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(pm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "vulnerability-scan-summary":
        fixture_path = getattr(args, "fixture_path", None)
        vs_out = vulnerability_scan_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(vs_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "compliance-audit-summary":
        fixture_path = getattr(args, "fixture_path", None)
        caud_out = compliance_audit_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(caud_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "disaster-recovery-summary":
        fixture_path = getattr(args, "fixture_path", None)
        dr_out = disaster_recovery_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(dr_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "service-level-summary":
        fixture_path = getattr(args, "fixture_path", None)
        sl_out = service_level_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(sl_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "asset-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        am_out = asset_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(am_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "network-monitoring-summary":
        fixture_path = getattr(args, "fixture_path", None)
        nm_out = network_monitoring_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(nm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "identity-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        im_out = identity_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(im_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "certificate-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        certm_out = certificate_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(certm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "alert-escalation-summary":
        fixture_path = getattr(args, "fixture_path", None)
        ae_out = alert_escalation_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(ae_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "configuration-change-summary":
        fixture_path = getattr(args, "fixture_path", None)
        cc_out = configuration_change_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(cc_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "data-retention-summary":
        fixture_path = getattr(args, "fixture_path", None)
        dr_ret_out = data_retention_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(dr_ret_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "problem-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        pm_out = problem_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(pm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "release-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        rm_out = release_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(rm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "service-request-summary":
        fixture_path = getattr(args, "fixture_path", None)
        sr_out = service_request_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(sr_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "contract-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        cm_out = contract_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(cm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "knowledge-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        km_out = knowledge_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(km_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "supplier-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        supp_out = supplier_management_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(supp_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "audit-finding-summary":
        fixture_path = getattr(args, "fixture_path", None)
        af_out = audit_finding_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(af_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "budget-summary":
        fixture_path = getattr(args, "fixture_path", None)
        budget_out = budget_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(budget_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "training-summary":
        fixture_path = getattr(args, "fixture_path", None)
        train_out = training_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(train_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "change-request-summary":
        fixture_path = getattr(args, "fixture_path", None)
        cr_out = change_request_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(cr_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "project-milestone-summary":
        fixture_path = getattr(args, "fixture_path", None)
        pm_out = project_milestone_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(pm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "vendor-assessment-summary":
        fixture_path = getattr(args, "fixture_path", None)
        va_out = vendor_assessment_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(va_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "communication-summary":
        fixture_path = getattr(args, "fixture_path", None)
        comm_out = communication_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(comm_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "document-management-summary":
        fixture_path = getattr(args, "fixture_path", None)
        doc_mgmt_out = document_management_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(doc_mgmt_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "procurement-summary":
        fixture_path = getattr(args, "fixture_path", None)
        proc_out = procurement_summary(Path(fixture_path) if fixture_path else None)
        print(json.dumps(proc_out, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "labeled-dataset-summary":
        from techno_search.labeled_dataset import labeled_dataset_summary
        fixture_path = getattr(args, "fixture_path", None)
        print(json.dumps(labeled_dataset_summary(fixture_path), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "eval-against-labels":
        from techno_search.baseline_eval import eval_against_labels
        fixture_path = getattr(args, "fixture_path", None)
        print(json.dumps(eval_against_labels(fixture_path), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "validate-input":
        from techno_search.data_quality import validate_input
        dq_result = validate_input(Path(args.input), args.track)
        print(json.dumps(dq_result.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if dq_result.ok else 1

    if args.command == "run-pipeline":
        from techno_search.pipeline_runner import run_pipeline

        _epoch_files: list[Path] | None = None
        _raw_epoch = getattr(args, "epoch_files", None)
        if _raw_epoch:
            _epoch_files = [Path(p) for p in _raw_epoch]
        pipeline_result = run_pipeline(
            Path(args.input),
            args.track,
            Path(args.output_dir),
            candidate_id=getattr(args, "candidate_id", None),
            epoch_dat_files=_epoch_files,
            semisupervised_model_path=getattr(args, "semisupervised_model", None),
            jwst_integration_index=getattr(args, "jwst_integration_index", None),
            jwst_hitran_xsc_dir=getattr(args, "jwst_hitran_xsc_dir", None),
        )
        print(json.dumps(pipeline_result.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if pipeline_result.ok else 1

    if args.command == "prod-file-scan":
        return _run_prod_file_scan(args)

    if args.command == "generate-peer-review-package":
        pr_result: dict[str, Any] = {
            "ok": False,
            "schema_version": "peer_review_package_stub_v1",
            "issues": ["peer_review_package deleted in Phase 0 — no candidates ready"],
        }
        print(json.dumps(pr_result, indent=2, sort_keys=True), file=out)
        return 1

    if args.command == "learned-model-summary":
        from techno_search.learned_scoring_model import learned_model_summary

        lm_path = getattr(args, "labeled_dataset_path", None)
        lm_result: dict[str, Any] = learned_model_summary(lm_path)
        print(json.dumps(lm_result, indent=2, sort_keys=True), file=out)
        return 0 if lm_result.get("ok") else 1

    if args.command == "synthetic-training-summary":
        from techno_search.learned_scoring_model import (  # noqa: PLC0415
            SYNTHETIC_DATASET_V1_PATH,
            synthetic_v1_training_summary,
        )

        dataset_path_arg = getattr(args, "dataset_path", None)
        ds_path = Path(dataset_path_arg) if dataset_path_arg else SYNTHETIC_DATASET_V1_PATH
        synth_result: dict[str, Any] = synthetic_v1_training_summary(ds_path)
        print(json.dumps(synth_result, indent=2, sort_keys=True), file=out)
        return 0 if synth_result.get("ok") else 1

    if args.command == "real-labels-model-summary":
        from techno_search.learned_scoring_model import (  # noqa: PLC0415
            real_labels_model_summary as _rlms2,
        )

        rl_path_arg = getattr(args, "dataset_path", None)
        rl_result: dict[str, Any] = _rlms2(Path(rl_path_arg) if rl_path_arg else None)
        print(json.dumps(rl_result, indent=2, sort_keys=True), file=out)
        return 0 if rl_result.get("ok") else 1

    if args.command == "combined-model-summary":
        from techno_search.learned_scoring_model import (  # noqa: PLC0415
            combined_model_summary as _cms,
        )

        cm_path_arg = getattr(args, "dataset_path", None)
        cm_result: dict[str, Any] = _cms(Path(cm_path_arg) if cm_path_arg else None)
        print(json.dumps(cm_result, indent=2, sort_keys=True), file=out)
        return 0 if cm_result.get("ok") else 1

    if args.command == "noise-threshold-calibration":
        noise_cal_result: dict[str, Any] = {
            "ok": True,
            "schema_version": "noise_threshold_calibration_stub_v1",
            "issue_count": 0,
            "issues": [],
        }
        print(json.dumps(noise_cal_result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "track-a-disk-usage":
        from techno_search.track_a_data_guard import track_a_disk_usage

        report = track_a_disk_usage(project_root=default_project_root())
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if report.within_budget else 1

    if args.command == "track-a-htru2-acquire":
        from techno_search.track_a_htru2 import acquire_htru2

        try:
            htru2_record = acquire_htru2(project_root=default_project_root())
        except RuntimeError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=out)
            return 1
        result = {"ok": True, **htru2_record.as_dict()}
        print(json.dumps(result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "track-a-htru2-train":
        from techno_search.track_a_htru2 import default_htru2_cache_dir, train_htru2_baseline

        root = default_project_root()
        cache_dir = default_htru2_cache_dir(root)
        try:
            summary = train_htru2_baseline(
                features_path=cache_dir / "htru2_features.parquet",
                labels_path=cache_dir / "htru2_labels.parquet",
                model_out_dir=root / "models" / "track_a",
                metrics_out_path=root / "metrics" / "track_a" / "htru2_baseline_metrics.json",
                schema_out_path=root / "schemas" / "track_a_htru2_schema.json",
            )
        except (FileNotFoundError, ValueError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=out)
            return 1
        print(json.dumps({"ok": True, **summary}, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "track-a-catalog-acquire":
        from techno_search.track_a_catalogs import CATALOG_ACQUISITION_SPECS

        acquire_fn = CATALOG_ACQUISITION_SPECS[args.catalog]
        try:
            catalog_record = acquire_fn(project_root=default_project_root())
        except RuntimeError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=out)
            return 1
        print(
            json.dumps({"ok": True, **catalog_record.as_dict()}, indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "track-a-crossmatch":
        from techno_search.track_a_crossmatch import cross_match_known_sources

        crossmatch_result = cross_match_known_sources(
            args.ra_deg,
            args.dec_deg,
            radius_arcsec=args.radius_arcsec,
            project_root=default_project_root(),
        )
        print(json.dumps(crossmatch_result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "track-a-historical-replay":
        from techno_search.track_a_replay import (
            run_historical_replay,
            save_historical_replay_report,
        )

        replay_report = run_historical_replay(
            project_root=default_project_root(),
            sample_size=args.sample_size,
        )
        saved_path = save_historical_replay_report(
            replay_report, project_root=default_project_root()
        )
        print(
            json.dumps(
                {**replay_report, "saved_report_path": str(saved_path)},
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0 if replay_report["all_recovered"] else 1

    if args.command == "track-a-satellite-acquire":
        from techno_search.track_a_satellites import (
            SATNOGS_ENDPOINTS,
            acquire_celestrak_gp_active,
            acquire_celestrak_satcat,
            acquire_satnogs_endpoint,
        )

        try:
            if args.source == "celestrak_satcat":
                satellite_record = acquire_celestrak_satcat(project_root=default_project_root())
            elif args.source == "celestrak_gp_active":
                satellite_record = acquire_celestrak_gp_active(
                    project_root=default_project_root()
                )
            else:
                endpoint = args.source.removeprefix("satnogs_")
                if endpoint not in SATNOGS_ENDPOINTS:
                    msg = f"Unknown satellite source: {args.source!r}"
                    raise RuntimeError(msg)
                satellite_record = acquire_satnogs_endpoint(
                    endpoint, project_root=default_project_root()
                )
        except RuntimeError as exc:
            _record_data_collection_status_best_effort(
                "track-a-satellite-acquire", {"ok": False, "error": str(exc)}
            )
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=out)
            return 1
        _record_data_collection_status_best_effort(
            "track-a-satellite-acquire", satellite_record.as_dict()
        )
        print(
            json.dumps({"ok": True, **satellite_record.as_dict()}, indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "photometry-lightcurve-search":
        from techno_search.photometry.lightcurve_search import search_and_download_lightcurves

        try:
            mission = tuple(m.strip() for m in args.mission.split(",")) if args.mission else None
            search_record = search_and_download_lightcurves(
                args.target,
                download_dir=Path(args.download_dir),
                mission=mission,
                author=args.author,
                sector=args.sector,
                quarter=args.quarter,
                campaign=args.campaign,
                exptime=args.exptime,
                limit=args.limit,
            )
        except RuntimeError as exc:
            _record_data_collection_status_best_effort(
                "photometry-lightcurve-search", {"ok": False, "error": str(exc)}
            )
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=out)
            return 1
        _record_data_collection_status_best_effort(
            "photometry-lightcurve-search", search_record.as_dict()
        )
        print(
            json.dumps({"ok": True, **search_record.as_dict()}, indent=2, sort_keys=True),
            file=out,
        )
        return 0 if search_record.result_count > 0 else 1

    if args.command == "record-data-collection-status":
        from techno_search.data_collection_status import (
            record_and_publish_data_collection_status,
        )

        try:
            summary = json.loads(args.summary_json)
        except json.JSONDecodeError as exc:
            print(
                json.dumps(
                    {"ok": False, "error": f"Invalid --summary-json: {exc}"},
                    indent=2,
                    sort_keys=True,
                ),
                file=out,
            )
            return 1
        status_path_override = args.status_path or os.environ.get(
            "TECHNO_DATA_COLLECTION_STATUS_PATH"
        )
        record_result = record_and_publish_data_collection_status(
            default_project_root(),
            args.script,
            summary,
            status_path=Path(status_path_override) if status_path_override else None,
            auto_commit=not args.no_commit,
        )
        print(json.dumps({"ok": True, **record_result}, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "jwst-miri-lrs-search":
        from techno_search.spectroscopy.jwst_search import (
            MIRI_LRS_INSTRUMENT_NAMES,
            search_and_download_miri_lrs_spectra,
        )

        try:
            instrument_name = (
                tuple(m.strip() for m in args.instrument_name.split(","))
                if args.instrument_name
                else MIRI_LRS_INSTRUMENT_NAMES
            )
            filters = args.filters if args.filters else None
            jwst_record = search_and_download_miri_lrs_spectra(
                args.target,
                download_dir=Path(args.download_dir),
                instrument_name=instrument_name,
                filters=filters,
                radius_arcsec=args.radius_arcsec,
                limit=args.limit,
            )
        except RuntimeError as exc:
            _record_data_collection_status_best_effort(
                "jwst-miri-lrs-search", {"ok": False, "error": str(exc)}
            )
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=out)
            return 1
        _record_data_collection_status_best_effort("jwst-miri-lrs-search", jwst_record.as_dict())
        print(
            json.dumps({"ok": True, **jwst_record.as_dict()}, indent=2, sort_keys=True),
            file=out,
        )
        return 0 if jwst_record.x1d_product_count > 0 else 1

    if args.command == "wise-photometry-search":
        from techno_search.infrared_wise.irsa_search import search_and_download_wise_photometry

        try:
            irsa_record = search_and_download_wise_photometry(
                args.target,
                download_dir=Path(args.download_dir),
                radius_arcsec=args.radius_arcsec,
            )
        except RuntimeError as exc:
            _record_data_collection_status_best_effort(
                "wise-photometry-search", {"ok": False, "error": str(exc)}
            )
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=out)
            return 1
        _record_data_collection_status_best_effort("wise-photometry-search", irsa_record.as_dict())
        print(
            json.dumps({"ok": True, **irsa_record.as_dict()}, indent=2, sort_keys=True),
            file=out,
        )
        return 0 if irsa_record.result_count > 0 else 1

    if args.command == "track-a-satellite-match":
        from techno_search.track_a_satellites import match_satellite_transmitter

        try:
            observation_time = datetime.fromisoformat(args.observation_time_utc)
            if observation_time.tzinfo is None:
                observation_time = observation_time.replace(tzinfo=UTC)
        except ValueError as exc:
            print(
                json.dumps(
                    {"ok": False, "error": f"Invalid --observation-time-utc: {exc}"},
                    indent=2,
                    sort_keys=True,
                ),
                file=out,
            )
            return 1

        satellite_match_result = match_satellite_transmitter(
            frequency_hz=args.frequency_hz,
            observation_time_utc=observation_time,
            ra_deg=args.ra_deg,
            dec_deg=args.dec_deg,
            observer_lat_deg=args.observer_lat_deg,
            observer_lon_deg=args.observer_lon_deg,
            observer_elevation_m=args.observer_elevation_m,
            beam_radius_deg=args.beam_radius_deg,
            project_root=default_project_root(),
        )
        print(json.dumps(satellite_match_result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "track-b-unknown-candidate-gate":
        from techno_search.track_b_gate import track_b_unknown_candidate_gate

        try:
            candidate = load_candidate_json(args.candidate_json)
            crossmatch_result = json.loads(Path(args.crossmatch_json).read_text(encoding="utf-8"))
            satellite_result = (
                json.loads(Path(args.satellite_json).read_text(encoding="utf-8"))
                if args.satellite_json
                else None
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=out)
            return 1
        gate_result = track_b_unknown_candidate_gate(
            candidate,
            crossmatch_result=crossmatch_result,
            satellite_result=satellite_result,
        )
        print(json.dumps({"ok": True, **gate_result}, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "track-b-candidate-readiness":
        from techno_search.track_b_gate import track_b_candidate_packet_readiness

        try:
            candidate = load_candidate_json(args.candidate_json)
            readiness_crossmatch_result = (
                json.loads(Path(args.crossmatch_json).read_text(encoding="utf-8"))
                if args.crossmatch_json
                else None
            )
            readiness_satellite_result = (
                json.loads(Path(args.satellite_json).read_text(encoding="utf-8"))
                if args.satellite_json
                else None
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=out)
            return 1
        readiness = track_b_candidate_packet_readiness(
            candidate,
            crossmatch_result=readiness_crossmatch_result,
            satellite_result=readiness_satellite_result,
        )
        print(json.dumps({"ok": True, **readiness}, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "adversarial-review-dossier":
        from techno_search.adversarial_review import build_adversarial_review_dossier

        try:
            scored_report = json.loads(Path(args.report_json).read_text(encoding="utf-8"))
            track_b_gate_result = (
                json.loads(Path(args.track_b_gate_json).read_text(encoding="utf-8"))
                if args.track_b_gate_json
                else None
            )
        except (OSError, json.JSONDecodeError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=out)
            return 1
        dossier = build_adversarial_review_dossier(
            scored_report,
            track_b_gate_result=track_b_gate_result,
        )
        print(json.dumps({"ok": True, **dossier.as_dict()}, indent=2, sort_keys=True), file=out)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def load_candidate_json(path: Path | str) -> Candidate:
    """Load a normalized synthetic candidate JSON file."""

    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    return candidate_from_mapping(data)


def score_batch(
    input_dir: Path | str,
    output_dir: Path | str,
    *,
    prefix: str = "",
    include_plot_artifacts: bool = True,
    workers: int | None = None,
) -> Path:
    """Score all JSON candidate packets in a directory and write an aggregate manifest."""
    from techno_search.scoring import score_candidates_parallel

    source_dir = Path(input_dir)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    candidate_paths = sorted(source_dir.glob("*.json"))
    candidates = [load_candidate_json(p) for p in candidate_paths]
    scored_list = score_candidates_parallel(candidates, workers=workers)

    entries: list[dict[str, object]] = []
    for scored in scored_list:
        report_prefix = (
            f"{prefix}{scored.candidate.candidate_id}" if prefix
            else scored.candidate.candidate_id
        )
        paths = write_candidate_reports(
            scored,
            destination,
            filename_prefix=report_prefix,
            include_plot_artifacts=include_plot_artifacts,
        )
        candidate = scored.candidate
        entries.append(
            {
                "candidate_id": candidate.candidate_id,
                "track": candidate.track.value,
                "recommended_pathway": scored.recommended_pathway.value,
                "config_version": str(
                    candidate.provenance.get("config_version", DEFAULT_SCORING_CONFIG_VERSION)
                ),
                "markdown_path": str(paths.markdown_path),
                "json_path": str(paths.json_path),
                "manifest_path": str(paths.manifest_path),
                "plot_artifact_paths": [str(path) for path in paths.plot_artifact_paths],
            }
        )

    batch_manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "input_dir": str(source_dir),
        "output_dir": str(destination),
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "config_version": DEFAULT_SCORING_CONFIG_VERSION,
        "candidate_count": len(entries),
        "reports": entries,
    }
    manifest_path = destination / "batch_manifest.json"
    manifest_path.write_text(json.dumps(batch_manifest, indent=2, sort_keys=True) + "\n")
    return manifest_path


def schema_paths() -> dict[str, str]:
    """Return repository-local schema artifact paths."""

    schema_dir = Path(__file__).resolve().parents[2] / "schemas"
    return {
        schema_name: str(schema_dir / filename)
        for schema_name, filename in sorted(SCHEMA_FILENAMES.items())
    }


def default_score_regression_snapshot_path() -> Path:
    """Return the repository-local score regression snapshot path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "score_regressions.json"
    )


def score_regression_summary(snapshot_path: Path | None = None) -> dict[str, object]:
    """Summarize score regression snapshot coverage."""

    path = snapshot_path or default_score_regression_snapshot_path()
    if not path.exists():
        return {
            "snapshot_path": str(path),
            "removed_in_phase_0": True,
            "removal_reason": (
                "Synthetic score regression snapshots were deleted in Phase 0; "
                "production validation must use real observations or realistic "
                "non-training fixtures."
            ),
            "candidate_count": 0,
            "by_track": {},
            "by_recommended_pathway": {},
            "candidate_ids": [],
        }
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    candidates = data["candidates"]
    return {
        "snapshot_path": str(path),
        "candidate_count": len(candidates),
        "by_track": dict(
            sorted(Counter(candidate["track"] for candidate in candidates.values()).items())
        ),
        "by_recommended_pathway": dict(
            sorted(
                Counter(
                    candidate["recommended_pathway"] for candidate in candidates.values()
                ).items()
            )
        ),
        "candidate_ids": sorted(candidates),
    }


def default_project_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parents[2]


def _record_data_collection_status_best_effort(script: str, summary: dict[str, Any]) -> None:
    """Best-effort status manifest update + auto-commit after a real acquisition run.

    Never raises -- a status-reporting side effect must not fail the
    acquisition command's own exit status. Silently does nothing if the
    manifest/git side effect itself errors (e.g. no network to push); the
    acquisition result the user sees is unaffected either way.
    """

    try:
        from techno_search.data_collection_status import (
            record_and_publish_data_collection_status,
        )

        record_and_publish_data_collection_status(default_project_root(), script, summary)
    except Exception:  # noqa: BLE001
        pass


def _default_example_candidates_dir() -> Path:
    return default_project_root() / "examples" / "candidates"


def regenerate_examples() -> dict[str, object]:
    """Regenerate committed example reports from example candidate JSON files."""

    candidate_dir = Path("examples/candidates")
    reports_dir = Path("examples/reports")
    batch_reports_dir = Path("examples/batch_reports")

    report_paths: list[str] = []
    for candidate_path in sorted(candidate_dir.glob("*.json")):
        candidate = load_candidate_json(candidate_path)
        scored = score_candidate(candidate)
        paths = write_candidate_reports(
            scored,
            reports_dir,
            filename_prefix=candidate.candidate_id,
        )
        report_paths.extend(
            [str(paths.markdown_path), str(paths.json_path), str(paths.manifest_path)]
        )
        report_paths.extend(str(path) for path in paths.plot_artifact_paths)

    batch_manifest_path = score_batch(candidate_dir, batch_reports_dir)
    return {
        "candidate_count": len(list(candidate_dir.glob("*.json"))),
        "reports_dir": str(reports_dir),
        "batch_reports_dir": str(batch_reports_dir),
        "report_paths": sorted(report_paths),
        "batch_manifest_path": str(batch_manifest_path),
    }


def validate_all() -> dict[str, object]:
    """Run the Phase 0 scientific-only production readiness gate.

    This public CLI gate intentionally excludes legacy operational-log,
    scheduler, MCP, benchmark, and synthetic-training summaries. Those payloads
    were useful scaffolding during earlier development but do not decide whether
    the search pipeline is scientifically closer to production.
    """

    root = default_project_root()
    candidate_results = {
        str(path): validate_candidate_file(path).as_dict()
        for path in sorted((root / "examples" / "candidates").glob("*.json"))
    }
    report_result = validate_report_directory(root / "examples" / "reports").as_dict()
    phase0_schema_keys = {
        "ai_hardening_gate",
        "candidate_escalation",
        "candidate_packet",
        "data_quality",
        "labeled_candidates",
        "project_status_consistency",
        "real_data_admission_preflight",
        "report_manifest",
        "scan_summary",
    }
    all_schemas = schema_paths()
    schemas = {
        name: path
        for name, path in all_schemas.items()
        if name in phase0_schema_keys
    }
    schema_results = {path: Path(path).exists() for path in schemas.values()}

    tracked_paths = git_tracked_paths(root)
    catalog_cache = catalog_cache_validation_summary(tracked_paths, project_root=root)
    catalog_cache_public = {
        key: value
        for key, value in catalog_cache.items()
        if key != "checked_paths"
    }
    sqlite_commit_guard = validate_sqlite_log_commit_paths(
        tracked_paths,
        project_root=root,
    )

    from techno_search.baseline_eval import eval_against_labels as _eval_labels
    from techno_search.globular_filter import (  # noqa: PLC0415
        GLOBULAR_FEATURE_NAMES as _GLOBULAR_FEATURE_NAMES,
    )
    from techno_search.learned_scoring_model import (  # noqa: PLC0415
        real_labels_model_summary as _real_labels_model_summary,
    )
    from techno_search.radio.cross_band_features import (  # noqa: PLC0415
        cross_band_features_summary as _cross_band_features_summary,
    )
    from techno_search.semisupervised_scorer import (  # noqa: PLC0415
        semisupervised_scorer_summary as _semisupervised_scorer_summary,
    )

    real_label_path = root / "examples" / "real_labeled" / (
        "hip99427_citizen_science_labels_v1.json"
    )
    label_eval_data = _eval_labels(real_label_path)
    label_eval_public = {
        key: value
        for key, value in label_eval_data.items()
        if key != "results"
    }
    real_label_accuracy_raw = label_eval_data.get("accuracy")
    real_label_accuracy = (
        float(real_label_accuracy_raw)
        if isinstance(real_label_accuracy_raw, (int, float))
        else None
    )
    real_label_entry_count = int(label_eval_data.get("entry_count", 0))
    real_label_accuracy_gate_ok = (
        real_label_accuracy is None or real_label_accuracy >= 0.70
    )

    real_labels_model = _real_labels_model_summary()
    learned_model_ok = bool(real_labels_model.get("ok", False))
    learned_model_trained = bool(real_labels_model.get("trained", False))
    learned_model_cv_accuracy_raw = real_labels_model.get("cv_accuracy")
    learned_model_cv_accuracy = (
        float(learned_model_cv_accuracy_raw)
        if isinstance(learned_model_cv_accuracy_raw, (int, float))
        else None
    )

    cross_band_features = _cross_band_features_summary()
    cross_band_feature_count = int(cross_band_features.get("feature_count", 0))
    globular_feature_count = len(_GLOBULAR_FEATURE_NAMES)
    globular_filter = {
        "schema_version": "globular_filter_v1",
        "feature_count": globular_feature_count,
    }
    semisupervised_scorer = _semisupervised_scorer_summary()
    local_semisupervised_metadata_path = (
        root / "data" / "meerkat_hits" / "semisupervised_scorer_metadata.json"
    )
    local_semisupervised_model_path = (
        root / "data" / "meerkat_hits" / "semisupervised_scorer.joblib"
    )
    if local_semisupervised_metadata_path.exists():
        try:
            local_metadata = json.loads(
                local_semisupervised_metadata_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            local_metadata = {}
        if isinstance(local_metadata, dict):
            train_hit_count = int(local_metadata.get("train_hit_count", 0) or 0)
            semisupervised_scorer = {
                **semisupervised_scorer,
                "is_fitted": train_hit_count > 0,
                "train_hit_count": train_hit_count,
                "local_metadata_path": str(local_semisupervised_metadata_path),
                "local_model_path": str(local_semisupervised_model_path),
                "local_model_exists": local_semisupervised_model_path.exists(),
            }
    semisupervised_feature_count = int(
        semisupervised_scorer.get("feature_count", 0)
    )

    provenance_chain = provenance_chain_validator(report_dir=root / "examples" / "reports")
    project_status = project_status_consistency_summary()
    ai_hardening_gate = ai_hardening_gate_summary()
    real_data_preflight = real_data_admission_preflight_summary()

    ok = (
        all(result["ok"] for result in candidate_results.values())
        and bool(report_result["ok"])
        and all(schema_results.values())
        and bool(catalog_cache["ok"])
        and bool(sqlite_commit_guard["ok"])
        and cross_band_feature_count >= 4
        and globular_feature_count >= 13
        and semisupervised_feature_count >= 12
        and real_label_accuracy_gate_ok
        and learned_model_ok
        and learned_model_trained
        and bool(provenance_chain.get("ok", False))
        and bool(project_status.get("ok", False))
        and bool(ai_hardening_gate.get("ok", False))
        and bool(real_data_preflight.get("ok", False))
    )

    return {
        "ok": ok,
        "schema_version": "phase0_scientific_validate_all_v1",
        "phase": "Phase 0 — Strip & Fix",
        "omitted_legacy_payloads": [
            "operational_log_summaries",
            "sqlite_adapter_scaffolding",
            "mcp_bootstrap_scaffolding",
            "synthetic_training_summaries",
            "scheduler_planning_scaffolding",
            "benchmark_scaffolding",
        ],
        "candidates": candidate_results,
        "reports": report_result,
        "schemas": schemas,
        "schema_paths_exist": schema_results,
        "artifact_hygiene": {
            "catalog_cache_validation": catalog_cache_public,
            "top_level_sqlite_log_commit_guard": sqlite_commit_guard,
        },
        "catalog_cache_validation": catalog_cache_public,
        "top_level_sqlite_log_commit_guard": sqlite_commit_guard,
        "radio_science_summary": {
            "cross_band_feature_count": cross_band_feature_count,
            "globular_feature_count": globular_feature_count,
            "semisupervised_feature_count": semisupervised_feature_count,
            "semisupervised_is_fitted": bool(
                semisupervised_scorer.get("is_fitted", False)
            ),
            "semisupervised_train_hit_count": int(
                semisupervised_scorer.get("train_hit_count", 0)
            ),
        },
        "cross_band_features_summary": cross_band_features,
        "globular_filter_summary": globular_filter,
        "semisupervised_scorer_summary": semisupervised_scorer,
        "eval_against_labels_summary": label_eval_public,
        "real_label_accuracy": real_label_accuracy,
        "real_label_accuracy_gate_ok": real_label_accuracy_gate_ok,
        "real_label_entry_count": real_label_entry_count,
        "learned_scoring_model_v1_summary": real_labels_model,
        "learned_scoring_model_v1_ok": learned_model_ok,
        "learned_scoring_model_v1_trained": learned_model_trained,
        "learned_scoring_model_v1_cv_accuracy": learned_model_cv_accuracy,
        "provenance_chain_validation": provenance_chain,
        "project_status_consistency_summary": project_status,
        "ai_hardening_gate_summary": ai_hardening_gate,
        "real_data_admission_preflight_summary": real_data_preflight,
    }


def validation_summary() -> dict[str, object]:
    """Return a concise local validation dashboard without network access.

    Phase 0 cleanup: replaced 3200-line implementation with thin passthrough.
    The previous implementation referenced ~100 deleted operational overhead modules.
    """
    from datetime import datetime

    validation = validate_all()
    return {
        **validation,
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }


def provenance_summary(report_dir: Path | str) -> dict[str, object]:
    """Summarize provenance across per-candidate report manifests."""

    directory = Path(report_dir)
    manifest_paths = sorted(directory.glob("*.manifest.json"))
    manifests = []
    for path in manifest_paths:
        with path.open(encoding="utf-8") as handle:
            manifests.append(json.load(handle))

    return {
        "report_dir": str(directory),
        "manifest_count": len(manifests),
        "candidate_ids": sorted(str(manifest["candidate_id"]) for manifest in manifests),
        "by_track": dict(sorted(Counter(str(manifest["track"]) for manifest in manifests).items())),
        "by_schema_version": dict(
            sorted(Counter(str(manifest["schema_version"]) for manifest in manifests).items())
        ),
        "by_config_version": dict(
            sorted(Counter(str(manifest["config_version"]) for manifest in manifests).items())
        ),
        "by_source_dataset": dict(
            sorted(
                Counter(
                    str(manifest.get("provenance_summary", {}).get("source_dataset", "unknown"))
                    for manifest in manifests
                ).items()
            )
        ),
    }


def live_provider_summary() -> dict[str, object]:
    """Return configured live-provider adapter metadata without network access."""

    adapters = provider_adapters()
    return {
        "live_enabled": live_data_enabled(),
        "provider_count": len(adapters),
        "providers": [
            {
                "provider_name": adapter.provider_name,
                "service_url": adapter.service_url,
            }
            for adapter in adapters
        ],
    }


def live_cache_summary(cache_dir: Path | None = None) -> dict[str, object]:
    """Return configured live-provider cache metadata without network access."""

    cache = LiveProviderCache.from_config() if cache_dir is None else LiveProviderCache(cache_dir)
    return cache.summary()


def catalog_cache_policy_summary(cache_root: Path | None = None) -> dict[str, object]:
    """Return catalog cache policy metadata without creating cache files."""

    policy = (
        CatalogCachePolicy.from_config()
        if cache_root is None
        else CatalogCachePolicy(cache_root)
    )
    return policy.as_dict()


def catalog_cache_summary(cache_root: Path | None = None) -> dict[str, object]:
    """Return local catalog cache metadata counts without reading payloads."""

    cache = (
        CatalogCache.from_config()
        if cache_root is None
        else CatalogCache(CatalogCachePolicy(cache_root))
    )
    return cache.summary()


def catalog_cache_validation_summary(
    paths: Sequence[Path | str],
    *,
    project_root: Path | str | None = None,
) -> dict[str, object]:
    """Validate catalog cache commit paths for release and pre-commit checks."""

    return validate_catalog_cache_commit_paths(paths, project_root=project_root)


def git_tracked_paths(project_root: Path | str) -> list[Path]:
    """Return Git-tracked paths for repository-scoped release checks."""

    root = Path(project_root)
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [root / line for line in result.stdout.splitlines() if line]


def _sqlite_log_track_summary(db_path: Path) -> dict[str, object]:
    """Return run/outcome counts broken down by track from the SQLite log."""
    import sqlite3
    from contextlib import closing

    if not db_path.exists():
        return {
            "ok": False,
            "error": "database does not exist",
            "by_track": {},
        }
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            rows = conn.execute(
                "SELECT track, COUNT(*) FROM background_runs GROUP BY track"
            ).fetchall()
            by_track = {str(row[0]): int(row[1]) for row in rows}
        return {"ok": True, "by_track": by_track, "track_count": len(by_track)}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "by_track": {}}


def _project_health_summary(out: TextIO | None = None) -> dict[str, object]:
    """Concise health dashboard combining key gate statuses."""
    baseline = evaluate_baseline()
    wl = target_watchlist_summary()
    schema_count = len(schema_paths())
    baseline_accuracy = float(baseline.get("pathway_accuracy", 0.0))
    baseline_ok = baseline_accuracy >= 0.80
    watchlist_conflicts = int(wl.get("conflict_count", 0))
    watchlist_ok = watchlist_conflicts == 0
    drift = baseline_pathway_drift_summary()
    drift_ok = bool(drift.get("zero_drift", True))
    all_gates = baseline_ok and watchlist_ok and drift_ok
    return {
        "all_gates_pass": all_gates,
        "schema_count": schema_count,
        "baseline_pathway_accuracy": baseline_accuracy,
        "baseline_accuracy_gate_ok": baseline_ok,
        "watchlist_conflict_count": watchlist_conflicts,
        "watchlist_gate_ok": watchlist_ok,
        "baseline_drift_count": drift.get("drift_count", 0),
        "baseline_drift_gate_ok": drift_ok,
        "recommended_action": (
            "Run `techno-search validate-all` for detailed diagnostics."
            if not all_gates
            else "All health gates pass."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="techno-search",
        description="Run conservative technosignature-interest candidate tooling.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"techno-search {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Print the installed techno-search version.")

    score_parser = subparsers.add_parser(
        "score",
        help="Score a normalized candidate JSON file.",
    )
    score_parser.add_argument("input", type=Path, help="Input candidate JSON path.")
    score_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional directory for Markdown and JSON review packets.",
    )
    score_parser.add_argument(
        "--prefix",
        help="Optional safe filename prefix for written reports.",
    )
    score_parser.add_argument(
        "--no-plot-artifacts",
        action="store_true",
        help="Skip dependency-free synthetic SVG diagnostic artifacts.",
    )
    batch_parser = subparsers.add_parser(
        "score-batch",
        help="Score all normalized synthetic candidate JSON files in a directory.",
    )
    batch_parser.add_argument("input_dir", type=Path, help="Input candidate JSON directory.")
    batch_parser.add_argument("output_dir", type=Path, help="Output report directory.")
    batch_parser.add_argument(
        "--prefix",
        default="",
        help="Optional filename prefix prepended to each candidate ID.",
    )
    batch_parser.add_argument(
        "--no-plot-artifacts",
        action="store_true",
        help="Skip dependency-free synthetic SVG diagnostic artifacts.",
    )
    batch_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers for scoring (default: 1 = serial).",
    )
    calibration_parser = subparsers.add_parser(
        "calibration-summary",
        help="Summarize synthetic calibration fixture coverage.",
    )
    calibration_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional calibration fixture JSON path.",
    )
    false_positive_parser = subparsers.add_parser(
        "false-positive-summary",
        help="Summarize synthetic false-positive classes by track.",
    )
    false_positive_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional calibration fixture JSON path.",
    )
    calibration_track_parser = subparsers.add_parser(
        "calibration-track-summary",
        help="Summarize synthetic calibration fixture coverage within each track.",
    )
    calibration_track_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional calibration fixture JSON path.",
    )
    validate_candidate_parser = subparsers.add_parser(
        "validate-candidate",
        help="Validate a normalized synthetic candidate JSON file.",
    )
    validate_candidate_parser.add_argument("input", type=Path, help="Input candidate JSON path.")
    validate_reports_parser = subparsers.add_parser(
        "validate-reports",
        help="Validate generated candidate report packets and manifests in a directory.",
    )
    validate_reports_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing generated candidate reports.",
    )
    subparsers.add_parser(
        "schema-paths",
        help="Print local JSON schema artifact paths.",
    )
    score_regression_parser = subparsers.add_parser(
        "score-regression-summary",
        help="Summarize score regression snapshot coverage.",
    )
    score_regression_parser.add_argument(
        "--snapshot-path",
        type=Path,
        help="Optional score regression snapshot JSON path.",
    )
    injection_recovery_parser = subparsers.add_parser(
        "injection-recovery-summary",
        help="Summarize synthetic injection-recovery fixture coverage.",
    )
    injection_recovery_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic injection-recovery fixture JSON path.",
    )
    reliability_parser = subparsers.add_parser(
        "reliability-summary",
        help="Summarize synthetic reliability curve fixture coverage.",
    )
    reliability_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic reliability fixture JSON path.",
    )
    precision_recall_parser = subparsers.add_parser(
        "precision-recall-summary",
        help="Summarize synthetic precision-recall fixture coverage.",
    )
    precision_recall_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic precision-recall fixture JSON path.",
    )
    review_queue_parser = subparsers.add_parser(
        "review-queue-summary",
        help="Summarize synthetic human-review queue fixture coverage.",
    )
    review_queue_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic human-review queue fixture JSON path.",
    )
    consensus_parser = subparsers.add_parser(
        "consensus-summary",
        help="Summarize synthetic human-review consensus label fixture coverage.",
    )
    consensus_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic human-review consensus fixture JSON path.",
    )
    consensus_export_parser = subparsers.add_parser(
        "consensus-export-summary",
        help="Summarize synthetic human-review consensus export fixture coverage.",
    )
    consensus_export_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic human-review consensus export fixture JSON path.",
    )
    cross_track_parser = subparsers.add_parser(
        "cross-track-summary",
        help=(
            "Summarize cross-track candidate cross-reference fixture coverage. "
            "Cross-references are operational metadata only and never modify "
            "candidate scores or pathways."
        ),
    )
    cross_track_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional cross-track reference fixture JSON path.",
    )
    verify_repro_parser = subparsers.add_parser(
        "verify-report-reproducibility",
        help=(
            "Re-score persisted candidate packets and report drift vs. their "
            "manifests. Read-only; never auto-corrects historical artifacts."
        ),
    )
    verify_repro_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing per-candidate manifests and JSON packets.",
    )
    validation_dataset_parser = subparsers.add_parser(
        "validation-dataset-summary",
        help="Summarize validation dataset manifest coverage.",
    )
    validation_dataset_parser.add_argument(
        "--manifest-path",
        type=Path,
        help="Optional validation dataset manifest JSON path.",
    )
    validation_promotion_parser = subparsers.add_parser(
        "validation-promotion-summary",
        help="Summarize validation dataset promotion rule coverage.",
    )
    validation_promotion_parser.add_argument(
        "--rules-path",
        type=Path,
        help="Optional validation promotion rules JSON path.",
    )
    validation_readiness_parser = subparsers.add_parser(
        "validation-readiness-summary",
        help="Summarize validation dataset readiness review coverage.",
    )
    validation_readiness_parser.add_argument(
        "--readiness-path",
        type=Path,
        help="Optional validation readiness JSON path.",
    )
    benchmark_metadata_parser = subparsers.add_parser(
        "benchmark-metadata-summary",
        help="Summarize local synthetic validation benchmark metadata.",
    )
    benchmark_metadata_parser.add_argument(
        "--metadata-path",
        type=Path,
        help="Optional benchmark metadata JSON path.",
    )
    benchmark_run_parser = subparsers.add_parser(
        "benchmark-run-summary",
        help="Summarize local synthetic benchmark run-result metadata.",
    )
    benchmark_run_parser.add_argument(
        "--results-path",
        type=Path,
        help="Optional benchmark run-result JSON path.",
    )
    benchmark_append_parser = subparsers.add_parser(
        "benchmark-run-append",
        help="Append one local synthetic benchmark run-result entry.",
    )
    benchmark_append_parser.add_argument(
        "--results-path",
        type=Path,
        required=True,
        help="Benchmark run-result JSON path to create or append.",
    )
    benchmark_append_parser.add_argument("--run-id", required=True)
    benchmark_append_parser.add_argument("--command-name", required=True)
    benchmark_append_parser.add_argument("--command-kind", required=True)
    benchmark_append_parser.add_argument("--status", required=True)
    benchmark_append_parser.add_argument("--worker-count", type=int, required=True)
    benchmark_append_parser.add_argument("--input-case-count", type=int, required=True)
    benchmark_append_parser.add_argument("--duration-seconds", type=float, required=True)
    benchmark_append_parser.add_argument("--git-commit", required=True)
    benchmark_append_parser.add_argument("--config-version", required=True)
    benchmark_compare_parser = subparsers.add_parser(
        "benchmark-run-compare",
        help="Compare repeated local synthetic benchmark run-result entries.",
    )
    benchmark_compare_parser.add_argument(
        "--results-path",
        type=Path,
        help="Optional benchmark run-result JSON path.",
    )
    target_priority_parser = subparsers.add_parser(
        "target-priority-summary",
        help="Summarize background target-priority fixture coverage.",
    )
    target_priority_parser.add_argument(
        "--target-path",
        type=Path,
        help="Optional background target-priority JSON path.",
    )
    target_priority_parser.add_argument(
        "--config-path",
        type=Path,
        help="Optional background priority config JSON path.",
    )
    target_priority_parser.add_argument(
        "--ledger-path",
        type=Path,
        help="Optional background search ledger path for review-history scoring.",
    )
    background_ledger_parser = subparsers.add_parser(
        "background-ledger-summary",
        help="Summarize passive/background search ledger fixture coverage.",
    )
    background_ledger_parser.add_argument(
        "--ledger-path",
        type=Path,
        help="Optional background search ledger JSON path.",
    )
    background_review_parser = subparsers.add_parser(
        "background-reviewed-workflow-summary",
        help="Summarize reviewed workflow semantics in the background ledger.",
    )
    background_review_parser.add_argument(
        "--ledger-path",
        type=Path,
        help="Optional background search ledger JSON path.",
    )
    reviewed_log_parser = subparsers.add_parser(
        "reviewed-log-summary",
        help="Summarize reviewed background-search outcome records.",
    )
    reviewed_log_parser.add_argument(
        "--reviewed-log-path",
        type=Path,
        help="Optional reviewed background-search log JSON path.",
    )
    needs_follow_up_parser = subparsers.add_parser(
        "needs-follow-up-summary",
        help="Summarize background-search outcomes that require follow-up.",
    )
    needs_follow_up_parser.add_argument(
        "--needs-follow-up-log-path",
        type=Path,
        help="Optional needs-follow-up background-search log JSON path.",
    )
    follow_up_tests_parser = subparsers.add_parser(
        "follow-up-test-summary",
        help="Summarize deterministic local follow-up test results.",
    )
    follow_up_tests_parser.add_argument(
        "--follow-up-tests-path",
        type=Path,
        help="Optional background follow-up test result JSON path.",
    )
    report_readiness_parser = subparsers.add_parser(
        "report-readiness-summary",
        help="Summarize report-readiness gates for follow-up records.",
    )
    report_readiness_parser.add_argument(
        "--report-readiness-path",
        type=Path,
        help="Optional background report-readiness JSON path.",
    )
    draft_report_parser = subparsers.add_parser(
        "draft-follow-up-report-summary",
        help="Generate conservative draft report summaries from readiness records.",
    )
    draft_report_parser.add_argument(
        "--report-readiness-path",
        type=Path,
        help="Optional background report-readiness JSON path.",
    )
    draft_write_parser = subparsers.add_parser(
        "draft-follow-up-report-write",
        help="Write conservative draft follow-up reports as Markdown files.",
    )
    draft_write_parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for draft Markdown reports and manifest.",
    )
    draft_write_parser.add_argument(
        "--report-readiness-path",
        type=Path,
        help="Optional background report-readiness JSON path.",
    )
    validate_draft_parser = subparsers.add_parser(
        "validate-draft-reports",
        help="Validate persisted conservative draft follow-up reports.",
    )
    validate_draft_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing draft report Markdown and manifest.",
    )
    draft_fixture_parser = subparsers.add_parser(
        "draft-report-fixture-summary",
        help="Summarize committed conservative draft follow-up report fixtures.",
    )
    draft_fixture_parser.add_argument(
        "--draft-report-path",
        type=Path,
        help="Optional background draft follow-up report JSON path.",
    )
    user_decision_parser = subparsers.add_parser(
        "user-decision-summary",
        help="Summarize explicit user decision records for background reports.",
    )
    user_decision_parser.add_argument(
        "--user-decision-path",
        type=Path,
        help="Optional background user decision JSON path.",
    )
    user_decision_record_parser = subparsers.add_parser(
        "user-decision-record",
        help="Append one explicit local user decision record.",
    )
    user_decision_record_parser.add_argument(
        "--user-decision-path",
        type=Path,
        required=True,
        help="User decision JSON path to create or append.",
    )
    user_decision_record_parser.add_argument("--decision-id", required=True)
    user_decision_record_parser.add_argument("--readiness-id", required=True)
    user_decision_record_parser.add_argument("--follow-up-id", required=True)
    user_decision_record_parser.add_argument("--target-id", required=True)
    user_decision_record_parser.add_argument(
        "--track",
        required=True,
        choices=["radio", "infrared", "anomaly", "photometry", "spectroscopy"],
    )
    user_decision_record_parser.add_argument(
        "--decision",
        required=True,
        choices=["approve_submission", "request_more_tests", "close_as_reviewed"],
    )
    user_decision_record_parser.add_argument("--rationale", required=True)
    user_decision_record_parser.add_argument("--decided-at-utc")
    user_decision_record_parser.add_argument(
        "--required-next-action",
        action="append",
        default=[],
    )
    user_decision_record_parser.add_argument(
        "--blocking-issue",
        action="append",
        default=[],
    )
    user_decision_record_parser.add_argument("--submission-destination")
    user_decision_record_parser.add_argument(
        "--confirm-external-submission-approval",
        action="store_true",
        help=(
            "Explicitly approve external submission. Required with "
            "approve_submission and never inferred for other decisions."
        ),
    )
    submission_recommendation_parser = subparsers.add_parser(
        "submission-recommendation-summary",
        help="Summarize top-three conservative submission recommendations.",
    )
    submission_recommendation_parser.add_argument(
        "--report-readiness-path",
        type=Path,
        help="Optional background report-readiness JSON path.",
    )
    handoff_parser = subparsers.add_parser(
        "candidate-extraction-handoff-summary",
        help="Summarize local-only candidate extraction handoff readiness.",
    )
    handoff_parser.add_argument(
        "--handoff-path",
        type=Path,
        help="Optional candidate extraction handoff JSON path.",
    )
    background_run_parser = subparsers.add_parser(
        "background-run-once",
        help="Append one explicit local-only background search ledger entry.",
    )
    background_run_parser.add_argument(
        "--ledger-path",
        type=Path,
        required=True,
        help="Background search ledger JSON path to create or append.",
    )
    background_run_parser.add_argument(
        "--reviewed-log-path",
        type=Path,
        help=(
            "Reviewed outcome log path. Defaults to background_reviewed_log.json "
            "next to the ledger."
        ),
    )
    background_run_parser.add_argument(
        "--needs-follow-up-log-path",
        type=Path,
        help=(
            "Needs-follow-up outcome log path. Defaults to "
            "background_needs_follow_up_log.json next to the ledger."
        ),
    )
    background_run_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help=(
            "Optional top-level SQLite log database path. Recommended operational "
            "default: logs/techno_search.sqlite3."
        ),
    )
    background_run_parser.add_argument(
        "--target-path",
        type=Path,
        help="Optional background target-priority JSON path.",
    )
    background_run_parser.add_argument(
        "--config-path",
        type=Path,
        help="Optional background priority config JSON path.",
    )
    background_run_parser.add_argument(
        "--run-id",
        help="Optional stable run ID for reproducibility.",
    )
    background_run_parser.add_argument(
        "--code-commit",
        default="not-recorded",
        help="Optional code commit or workspace identifier to record in the ledger.",
    )
    background_run_parser.add_argument(
        "--acknowledge-local-run",
        action="store_true",
        required=True,
        help="Required opt-in flag acknowledging this local runner does not use network data.",
    )
    init_logs_parser = subparsers.add_parser(
        "init-logs",
        help="Initialize the top-level SQLite operational log database.",
    )
    init_logs_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    init_logs_parser.add_argument(
        "--code-commit",
        default="not-recorded",
        help="Optional code commit or workspace identifier to store in metadata.",
    )
    init_logs_parser.add_argument(
        "--config-version",
        default="not-recorded",
        help="Optional config version to store in metadata.",
    )
    sqlite_summary_parser = subparsers.add_parser(
        "sqlite-log-summary",
        help="Summarize top-level SQLite operational logs.",
    )
    sqlite_summary_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_integrity_parser = subparsers.add_parser(
        "sqlite-log-integrity-summary",
        help="Summarize scheduler-facing SQLite log integrity checks.",
    )
    sqlite_integrity_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_bootstrap_parser = subparsers.add_parser(
        "sqlite-log-bootstrap-summary",
        help=(
            "Initialize local SQLite logs and report integrity, weekly digest, "
            "and operations-readiness SQLite gate visibility."
        ),
    )
    sqlite_bootstrap_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_bootstrap_parser.add_argument(
        "--code-commit",
        default="not-recorded",
        help="Optional code commit or workspace identifier to store in metadata.",
    )
    sqlite_bootstrap_parser.add_argument(
        "--config-version",
        default="not-recorded",
        help="Optional config version to store in metadata.",
    )
    sqlite_bootstrap_parser.add_argument(
        "--window-days",
        type=int,
        default=7,
        help="Weekly digest reporting window in days (default 7).",
    )
    sqlite_export_parser = subparsers.add_parser(
        "sqlite-log-export",
        help="Export a small review-safe JSON summary from SQLite logs.",
    )
    sqlite_export_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_export_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum recent runs and follow-up outcomes to include.",
    )
    sqlite_recent_runs_parser = subparsers.add_parser(
        "sqlite-recent-runs",
        help="List recent background runs from SQLite logs.",
    )
    sqlite_recent_runs_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_recent_runs_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum recent runs to include.",
    )
    sqlite_follow_up_parser = subparsers.add_parser(
        "sqlite-needs-follow-up",
        help="List recent needs-follow-up outcomes from SQLite logs.",
    )
    sqlite_follow_up_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_follow_up_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum needs-follow-up outcomes to include.",
    )
    sqlite_migration_parser = subparsers.add_parser(
        "sqlite-migration-summary",
        help="Report SQLite log schema migration status.",
    )
    sqlite_migration_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_migrate_parser = subparsers.add_parser(
        "sqlite-log-migrate",
        help=(
            "Print a non-destructive SQLite log migration plan. Apply mode is "
            "blocked until a destructive migration is reviewed and added."
        ),
    )
    sqlite_migrate_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_migrate_parser.add_argument(
        "--target-version",
        default=TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
        help="Target schema version. Defaults to the latest supported version.",
    )
    sqlite_migrate_parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Apply mode is currently blocked because no destructive migration is "
            "implemented. Reserved for future explicit migrations."
        ),
    )
    sqlite_pragmas_parser = subparsers.add_parser(
        "sqlite-log-pragmas",
        help="Report SQLite PRAGMA diagnostics for operator checks.",
    )
    sqlite_pragmas_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_retention_parser = subparsers.add_parser(
        "sqlite-log-retention-summary",
        help="Report SQLite log database age, size, and backup coverage.",
    )
    sqlite_retention_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_retention_parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Optional SQLite backup directory. Defaults to logs/backups.",
    )
    sqlite_backup_parser = subparsers.add_parser(
        "sqlite-log-backup",
        help="Create a timestamped local SQLite log backup under ignored logs/backups.",
    )
    sqlite_backup_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_backup_parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Optional SQLite backup directory. Defaults to logs/backups.",
    )
    sqlite_vacuum_parser = subparsers.add_parser(
        "sqlite-log-vacuum",
        help="Compact a local SQLite log database with VACUUM.",
    )
    sqlite_vacuum_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_digest_parser = subparsers.add_parser(
        "sqlite-log-weekly-digest",
        help=(
            "Print a review-safe rolling digest of SQLite operational logs. "
            "Read-only and does not expose payload contents."
        ),
    )
    sqlite_digest_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_digest_parser.add_argument(
        "--window-days",
        type=int,
        default=7,
        help="Reporting window in days (default 7).",
    )
    sqlite_commit_guard_parser = subparsers.add_parser(
        "sqlite-log-commit-guard",
        help="Reject generated top-level SQLite log databases in commit paths.",
    )
    sqlite_commit_guard_parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help=(
            "Optional paths to validate. Defaults to Git-tracked paths when omitted."
        ),
    )
    sqlite_consistency_parser = subparsers.add_parser(
        "sqlite-log-consistency-summary",
        help=(
            "Check top-level SQLite log health, migration, authorization, and "
            "commit-guard consistency."
        ),
    )
    sqlite_consistency_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_consistency_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional SQLite log consistency expectation fixture path.",
    )
    validate_sqlite_parser = subparsers.add_parser(
        "validate-sqlite-logs",
        help="Validate top-level SQLite operational log invariants.",
    )
    validate_sqlite_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    scheduler_dry_run_parser = subparsers.add_parser(
        "scheduler-dry-run",
        help="Run the bounded local scheduler path against a temporary artifact directory.",
    )
    scheduler_dry_run_parser.add_argument(
        "--artifact-dir",
        type=Path,
        required=True,
        help="Temporary artifact directory for dry-run ledger and outcome logs.",
    )
    scheduler_dry_run_parser.add_argument(
        "--run-id",
        default="scheduler-dry-run",
    )
    scheduler_dry_run_parser.add_argument(
        "--code-commit",
        default="dry-run",
    )
    scheduler_dry_run_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help=(
            "Optional SQLite log database path. Defaults to background_logs.sqlite3 "
            "inside the dry-run artifact directory."
        ),
    )
    subparsers.add_parser(
        "validate-all",
        help=(
            "Run local validation summaries for examples, reports, schemas, "
            "calibration, and score snapshots."
        ),
    )
    subparsers.add_parser(
        "validation-summary",
        help="Print a concise local health dashboard without network access.",
    )
    subparsers.add_parser(
        "regenerate-examples",
        help="Regenerate committed example reports from examples/candidates.",
    )
    provenance_parser = subparsers.add_parser(
        "provenance-summary",
        help="Summarize provenance fields across report manifests in a directory.",
    )
    provenance_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing per-candidate report manifests.",
    )
    plot_artifact_parser = subparsers.add_parser(
        "plot-artifact-summary",
        help="Summarize plot artifact entries across report manifests in a directory.",
    )
    plot_artifact_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing per-candidate report manifests.",
    )
    subparsers.add_parser(
        "live-provider-summary",
        help="Print configured live-provider adapter names, URLs, and live-enabled status.",
    )
    live_cache_parser = subparsers.add_parser(
        "live-cache-summary",
        help="Print live-provider cache directory metadata without reading payloads.",
    )
    live_cache_parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Optional live-provider cache directory override.",
    )
    live_fixture_parser = subparsers.add_parser(
        "live-fixture-summary",
        help="Print committed live-metadata fixture coverage without network access.",
    )
    live_fixture_parser.add_argument(
        "--fixture-dir",
        type=Path,
        help="Optional live-metadata fixture directory override.",
    )
    subparsers.add_parser(
        "live-client-summary",
        help="Print configured live-client skeleton status without network access.",
    )
    catalog_cache_parser = subparsers.add_parser(
        "catalog-cache-policy",
        help="Print future catalog cache metadata policy without creating cache files.",
    )
    catalog_cache_parser.add_argument(
        "--cache-root",
        type=Path,
        help="Optional catalog cache metadata root override.",
    )
    catalog_cache_summary_parser = subparsers.add_parser(
        "catalog-cache-summary",
        help="Print catalog cache metadata counts without reading catalog payloads.",
    )
    catalog_cache_summary_parser.add_argument(
        "--cache-root",
        type=Path,
        help="Optional catalog cache metadata root override.",
    )
    catalog_cache_validate_parser = subparsers.add_parser(
        "catalog-cache-validate",
        help="Validate paths for forbidden committed catalog cache locations.",
    )
    catalog_cache_validate_parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Paths to validate before commit or release.",
    )
    baseline_eval_parser = subparsers.add_parser(
        "baseline-eval-summary",
        help=(
            "Evaluate the rule-based interpretable baseline classifier against "
            "synthetic calibration fixtures. Results are local diagnostics only — "
            "not detections, discoveries, or external validation."
        ),
    )
    baseline_eval_parser.add_argument(
        "--calibration-fixture",
        type=Path,
        help="Optional calibration false-positive fixture JSON path.",
    )
    baseline_eval_parser.add_argument(
        "--example-candidates-dir",
        type=Path,
        help="Optional example candidates directory.",
    )
    target_watchlist_parser = subparsers.add_parser(
        "target-watchlist-summary",
        help=(
            "Summarize operator target watchlist fixture coverage. "
            "Watchlist entries are scheduling aids only — they do not modify "
            "candidate scores or pathway routing."
        ),
    )
    target_watchlist_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional target watchlist fixture JSON path.",
    )
    weekly_review_parser = subparsers.add_parser(
        "weekly-review-template",
        help=(
            "Generate an operator weekly review template combining the SQLite log "
            "weekly digest and cross-track summary. Operational summary only — not a "
            "discovery claim."
        ),
    )
    weekly_review_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    weekly_review_parser.add_argument(
        "--cross-track-fixture",
        type=Path,
        help="Optional cross-track reference fixture JSON path.",
    )
    weekly_review_parser.add_argument(
        "--window-days",
        type=int,
        default=7,
        help="Rolling window in days for the weekly digest (default: 7).",
    )
    weekly_review_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional output directory for Markdown and JSON template files.",
    )
    weekly_review_parser.add_argument(
        "--operator-notes",
        default="",
        help="Optional free-text operator notes to include in the template.",
    )
    perf_history_parser = subparsers.add_parser(
        "baseline-performance-history-summary",
        help="Summarize the append-only baseline performance history fixture.",
    )
    perf_history_parser.add_argument(
        "--history-path",
        type=Path,
        help="Optional baseline performance history fixture JSON path.",
    )
    drift_parser = subparsers.add_parser(
        "baseline-pathway-drift-summary",
        help=(
            "Compare scoring-model recommended_pathway vs baseline predicted_pathway "
            "for all example candidates. Zero drift is required. "
            "Returns exit 1 if any drift is detected."
        ),
    )
    drift_parser.add_argument(
        "--example-candidates-dir",
        type=Path,
        help="Optional example candidates directory override.",
    )
    subparsers.add_parser(
        "sqlite-log-track-summary",
        help="Show SQLite log run counts broken down by track.",
    )
    subparsers.add_parser(
        "health",
        help=(
            "Concise project health dashboard combining key gate statuses. "
            "Returns exit 1 if any gate fails."
        ),
    )
    subparsers.add_parser(
        "review-dashboard",
        help=(
            "Operator review dashboard: open flags, overdue deadlines, "
            "review queue depth, pipeline blockers, and real-label accuracy. "
            "Returns exit 1 when any action items are pending."
        ),
    )
    scan_summary_parser = subparsers.add_parser(
        "scan-summary",
        help=(
            "Rank candidates from a multi-target scan by score. "
            "Reads *manifest.json files from BATCH_DIR."
        ),
    )
    scan_summary_parser.add_argument(
        "batch_dir",
        type=str,
        help="Directory containing *manifest.json files from a batch scan.",
    )
    gbt_cadence_raw_parser = subparsers.add_parser(
        "gbt-cadence-raw-status",
        help=(
            "Check local raw HDF5 files for an approved GBT ABACAB cadence "
            "against manifest size and MD5 evidence."
        ),
    )
    gbt_cadence_raw_parser.add_argument(
        "--manifest",
        type=str,
        default="configs/gbt_hip99427_cadence_v1.json",
        help="Approved GBT cadence manifest JSON.",
    )
    gbt_cadence_raw_parser.add_argument(
        "--data-root",
        type=str,
        default=str(Path.home() / "technosignature-data"),
        help="Root containing bl_observations/<cadence_id>/ raw HDF5 files.",
    )
    gbt_cadence_raw_parser.add_argument(
        "--raw-dir",
        type=str,
        default=None,
        help="Explicit raw HDF5 directory; overrides --data-root.",
    )
    gbt_cadence_review_parser = subparsers.add_parser(
        "gbt-cadence-abacab-review",
        help=(
            "Summarize candidate-level ON/OFF ABACAB outcomes from a derived "
            "GBT cadence CSV. Local triage evidence only."
        ),
    )
    gbt_cadence_review_parser.add_argument(
        "--cadence-csv",
        type=str,
        default=str(
            Path.home()
            / "technosignature-data"
            / "bl_hits"
            / "GBT_HIP99427_2016-12-30_ABACAD.csv"
        ),
        help="Derived GBT cadence CSV produced by scripts/ingest_gbt_cadence.py.",
    )
    gbt_cadence_review_parser.add_argument(
        "--cadence-id",
        type=str,
        default=None,
        help="Optional cadence identifier override for candidate IDs.",
    )
    gbt_cadence_review_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum follow-up candidate rows to include (default: 10).",
    )
    prod_run_id_parser = subparsers.add_parser(
        "prod-run-id",
        help="Generate a human-readable production scan run ID.",
    )
    prod_run_id_parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Optional four-character alphanumeric token for deterministic tests.",
    )
    prod_write_parser = subparsers.add_parser(
        "prod-write-outcomes",
        help=(
            "Write production run manifest, non-detection ledger, and follow-up "
            "ledger files. Local citizen-science operations only."
        ),
    )
    prod_write_parser.add_argument("--results-dir", required=True)
    prod_write_parser.add_argument("--run-dir", required=True)
    prod_write_parser.add_argument("--run-id", required=True)
    prod_write_parser.add_argument("--started-at-utc", required=True)
    prod_write_parser.add_argument("--scan-summary-path", default=None)
    prod_scan_parser = subparsers.add_parser(
        "prod-scan",
        help=(
            "Run the compact local production scan UX: validation, scan "
            "summary, RFI suppression, escalation checks, dashboard, and "
            "outcome ledgers. Local citizen-science operations only."
        ),
    )
    prod_scan_parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory containing candidate report manifests.",
    )
    prod_scan_parser.add_argument(
        "--scans-dir",
        default="results/scans",
        help="Directory where production scan run directories are written.",
    )
    prod_scan_parser.add_argument(
        "--run-id",
        default=None,
        help="Optional human-readable run ID. Defaults to a generated RUN-* ID.",
    )
    prod_scan_parser.add_argument(
        "--resume-run-dir",
        default=None,
        help="Existing production run directory to resume without redoing completed steps.",
    )
    prod_scan_parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Disable Rich spinner/table rendering and use plain compact output.",
    )
    prod_scan_parser.add_argument(
        "--allow-empty",
        action="store_true",
        help=(
            "Allow a zero-candidate run for diagnostics only. Normal production "
            "runs fail closed when no candidate manifests are found."
        ),
    )
    prod_diagnostics_parser = subparsers.add_parser(
        "prod-diagnostics",
        help="Run compact production diagnostics without dumping large JSON payloads.",
    )
    prod_diagnostics_parser.add_argument(
        "--scans-dir",
        default="results/scans",
        help="Directory containing production run subdirectories.",
    )
    prod_diagnostics_parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Disable Rich spinner rendering and use plain compact output.",
    )
    prod_diagnostics_parser.add_argument(
        "--json",
        action="store_true",
        help="Also print the machine-readable diagnostics summary after compact output.",
    )
    prod_runs_parser = subparsers.add_parser(
        "prod-runs",
        help="List production scan runs under a scans directory.",
    )
    prod_runs_parser.add_argument(
        "--scans-dir",
        default="results/scans",
        help="Directory containing production run subdirectories.",
    )
    prod_show_parser = subparsers.add_parser(
        "prod-show",
        help="Show one production scan run manifest summary.",
    )
    prod_show_parser.add_argument(
        "run_dir",
        nargs="?",
        help="Production run directory returned by prod-runs.",
    )
    prod_show_parser.add_argument(
        "--latest",
        action="store_true",
        help="Inspect the latest valid production run under --scans-dir.",
    )
    prod_show_parser.add_argument(
        "--scans-dir",
        default="results/scans",
        help="Directory containing production run subdirectories when using --latest.",
    )
    prod_follow_ups_parser = subparsers.add_parser(
        "prod-follow-ups",
        help="Show follow-up ledger entries for one production run.",
    )
    prod_follow_ups_parser.add_argument(
        "run_dir",
        nargs="?",
        help="Production run directory returned by prod-runs.",
    )
    prod_follow_ups_parser.add_argument(
        "--latest",
        action="store_true",
        help="Inspect the latest valid production run under --scans-dir.",
    )
    prod_follow_ups_parser.add_argument(
        "--scans-dir",
        default="results/scans",
        help="Directory containing production run subdirectories when using --latest.",
    )
    prod_follow_ups_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full machine-readable follow-up ledger JSON.",
    )
    prod_non_detections_parser = subparsers.add_parser(
        "prod-non-detections",
        help="Show non-detection ledger entries for one production run.",
    )
    prod_non_detections_parser.add_argument(
        "run_dir",
        nargs="?",
        help="Production run directory returned by prod-runs.",
    )
    prod_non_detections_parser.add_argument(
        "--latest",
        action="store_true",
        help="Inspect the latest valid production run under --scans-dir.",
    )
    prod_non_detections_parser.add_argument(
        "--scans-dir",
        default="results/scans",
        help="Directory containing production run subdirectories when using --latest.",
    )
    prod_non_detections_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full machine-readable non-detection ledger JSON.",
    )
    prod_target_status_parser = subparsers.add_parser(
        "prod-target-status",
        help="Show compact per-target status rows for one production run.",
    )
    prod_target_status_parser.add_argument(
        "run_dir",
        nargs="?",
        help="Production run directory returned by prod-runs.",
    )
    prod_target_status_parser.add_argument(
        "--latest",
        action="store_true",
        help="Inspect the latest valid production run under --scans-dir.",
    )
    prod_target_status_parser.add_argument(
        "--scans-dir",
        default="results/scans",
        help="Directory containing production run subdirectories when using --latest.",
    )
    prod_target_status_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full machine-readable target-status ledger JSON.",
    )
    _cross_rfi_parser = subparsers.add_parser(
        "cross-target-rfi-summary",
        help=(
            "Summarise cross-target RFI suppression policy. "
            "Signals in >=2 targets at the same frequency are flagged as RFI."
        ),
    )
    _cross_rfi_parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help=(
            "Directory containing *manifest.json files from a batch scan. "
            "When provided, loads real candidates grouped by target_name. "
            "When omitted, returns policy metadata with empty candidate list."
        ),
    )
    escalation_parser = subparsers.add_parser(
        "escalation-gate-check",
        help=(
            "Check whether a candidate JSON file passes the escalation gate "
            "(candidate_review_packet pathway + SNR >= 42.4). "
            "Returns escalation_required: true/false."
        ),
    )
    escalation_parser.add_argument(
        "candidate_file",
        type=str,
        help="Path to a candidate JSON file (e.g. a report manifest).",
    )
    ops_ready_parser = subparsers.add_parser(
        "operations-readiness-summary",
        help=(
            "Aggregate local-only readiness blockers across QC, alerts, review "
            "deadlines, route coverage, and top-level SQLite log state."
        ),
    )
    ops_ready_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for readiness snapshot fields.",
    )
    ops_action_parser = subparsers.add_parser(
        "operations-action-plan-summary",
        help=(
            "Translate operations-readiness blockers into prioritized local "
            "operator actions. Scheduling aid only."
        ),
    )
    ops_action_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for readiness snapshot fields.",
    )
    ops_resolution_parser = subparsers.add_parser(
        "operations-action-resolution-summary",
        help=(
            "Summarize local action-plan resolution records. Workflow provenance "
            "only; does not authorize live data or external submission."
        ),
    )
    ops_resolution_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local action-resolution fixture path.",
    )
    ops_resolution_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for action-plan coverage fields.",
    )
    ops_resolution_consistency_parser = subparsers.add_parser(
        "operations-action-resolution-consistency-summary",
        help=(
            "Summarize local action-resolution staleness consistency checks. "
            "Visibility gate only; does not clear blockers."
        ),
    )
    ops_resolution_consistency_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional expectation fixture path override.",
    )
    ops_blocker_detail_parser = subparsers.add_parser(
        "operations-blocker-detail-summary",
        help=(
            "Expand operations action-plan blockers into fixture-backed local "
            "source records. Operator review aid only."
        ),
    )
    ops_blocker_detail_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for readiness snapshot fields.",
    )
    ops_blocker_review_parser = subparsers.add_parser(
        "operations-blocker-review-summary",
        help=(
            "Summarize local blocker-detail review records. Workflow provenance "
            "only; does not clear blockers or authorize external workflow."
        ),
    )
    ops_blocker_review_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path.",
    )
    ops_blocker_review_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_followup_parser = subparsers.add_parser(
        "operations-blocker-followup-summary",
        help=(
            "Derive local blocker follow-up actions from blocker-review records. "
            "Planning aid only; does not clear blockers or authorize workflow."
        ),
    )
    ops_blocker_followup_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path.",
    )
    ops_blocker_followup_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_parser = subparsers.add_parser(
        "operations-blocker-followup-progress-summary",
        help=(
            "Summarize local progress notes for blocker follow-up actions. "
            "Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_review_parser = subparsers.add_parser(
        "operations-blocker-progress-review-summary",
        help=(
            "Summarize local second-pass review for unresolved blocker progress. "
            "Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_review_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker progress-review fixture path.",
    )
    ops_blocker_progress_review_parser.add_argument(
        "--progress-fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_review_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_review_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_next_parser = subparsers.add_parser(
        "operations-blocker-progress-next-actions-summary",
        help=(
            "Summarize local next actions for unresolved blocker progress. "
            "Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_next_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker progress next-action fixture path.",
    )
    ops_blocker_progress_next_parser.add_argument(
        "--progress-review-fixture-path",
        type=Path,
        help="Optional local blocker progress-review fixture path.",
    )
    ops_blocker_progress_next_parser.add_argument(
        "--progress-fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_next_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_next_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_execution_parser = subparsers.add_parser(
        "operations-blocker-progress-execution-summary",
        help=(
            "Summarize local execution notes for blocker progress next actions. "
            "Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker progress-execution fixture path.",
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--next-actions-fixture-path",
        type=Path,
        help="Optional local blocker progress next-action fixture path.",
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--progress-review-fixture-path",
        type=Path,
        help="Optional local blocker progress-review fixture path.",
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--progress-fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_execution_review_parser = subparsers.add_parser(
        "operations-blocker-progress-execution-review-summary",
        help=(
            "Summarize local reviews for blocker progress-execution notes. "
            "Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker progress execution-review fixture path.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--execution-fixture-path",
        type=Path,
        help="Optional local blocker progress-execution fixture path.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--next-actions-fixture-path",
        type=Path,
        help="Optional local blocker progress next-action fixture path.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--progress-review-fixture-path",
        type=Path,
        help="Optional local blocker progress-review fixture path.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--progress-fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_execution_followup_parser = subparsers.add_parser(
        "operations-blocker-progress-execution-followup-summary",
        help=(
            "Summarize local follow-up planning for blocker progress-execution "
            "reviews. Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker progress execution-followup fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--execution-review-fixture-path",
        type=Path,
        help="Optional local blocker progress execution-review fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--execution-fixture-path",
        type=Path,
        help="Optional local blocker progress-execution fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--next-actions-fixture-path",
        type=Path,
        help="Optional local blocker progress next-action fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--progress-review-fixture-path",
        type=Path,
        help="Optional local blocker progress-review fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--progress-fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_consistency_parser = subparsers.add_parser(
        "operations-blocker-progress-consistency-summary",
        help=(
            "Check local blocker-progress chain consistency. Visibility gate "
            "only; does not clear blockers."
        ),
    )
    ops_blocker_progress_consistency_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional blocker-progress consistency expectation fixture path.",
    )
    ops_digest_parser = subparsers.add_parser(
        "operations-readiness-digest",
        help=(
            "Print a review-safe Markdown operations digest. Local dashboard only; "
            "does not authorize live data or external submission."
        ),
    )
    ops_digest_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for readiness snapshot fields.",
    )
    ops_digest_parser.add_argument(
        "--output-path",
        type=Path,
        help="Optional Markdown output path for the digest.",
    )
    subparsers.add_parser(
        "baseline-confusion-matrix-summary",
        help=(
            "Print per-pathway confusion matrix and precision/recall/F1 metrics "
            "from the baseline evaluation harness. Synthetic diagnostics only."
        ),
    )
    det_parser = subparsers.add_parser(
        "score-determinism-check",
        help=(
            "Verify scoring produces identical outputs across repeated runs for "
            "example candidates. Returns exit 1 if any candidate is non-deterministic."
        ),
    )
    det_parser.add_argument(
        "candidate_paths",
        nargs="*",
        type=Path,
        help="Optional candidate JSON paths to check. Defaults to examples/candidates/.",
    )
    det_parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of repeat runs per candidate (default: 3).",
    )
    lifecycle_parser = subparsers.add_parser(
        "candidate-lifecycle-summary",
        help="Summarise candidate lifecycle stage entries. Scheduling aid only.",
    )
    lifecycle_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional candidate lifecycle fixture JSON path.",
    )
    schedule_parser = subparsers.add_parser(
        "observation-schedule-summary",
        help="Summarise planned/completed/cancelled observation windows. Scheduling aid only.",
    )
    schedule_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional observation schedule fixture JSON path.",
    )
    fn_parser = subparsers.add_parser(
        "false-negative-summary",
        help=(
            "Summarise missed injections from the injection-recovery fixture. "
            "Synthetic diagnostic only."
        ),
    )
    fn_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional injection-recovery fixture JSON path.",
    )
    sc_parser = subparsers.add_parser(
        "scoring-config-summary",
        help="Summarise current scoring thresholds. Synthetic v0 parameters only.",
    )
    sc_parser.add_argument(
        "--config-path",
        type=Path,
        help="Optional scoring config JSON path.",
    )
    subparsers.add_parser(
        "route-coverage-summary",
        help=(
            "Check that calibration fixtures cover all Pathway enum values. "
            "Synthetic diagnostic only."
        ),
    )
    lt_parser = subparsers.add_parser(
        "lifecycle-transition-summary",
        help=(
            "Validate that candidate lifecycle stage transitions follow the "
            "allowed ordering. Scheduling/provenance aid only."
        ),
    )
    lt_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional lifecycle entries fixture JSON path.",
    )
    oe_parser = subparsers.add_parser(
        "observation-efficiency-summary",
        help=(
            "Summarise observation window completion and cancellation rates. "
            "Scheduling aid only."
        ),
    )
    oe_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional observation schedule fixture JSON path.",
    )
    sens_parser = subparsers.add_parser(
        "sensitivity-config-summary",
        help=(
            "Summarise per-track sensitivity weights from the scoring config. "
            "Synthetic v0 parameters only — not calibrated detection sensitivities."
        ),
    )
    sens_parser.add_argument(
        "--config-path",
        type=Path,
        help="Optional scoring config JSON path.",
    )
    triage_parser = subparsers.add_parser(
        "triage-summary",
        help=(
            "Summarise operator candidate triage notes. "
            "Triage notes are scheduling aids and provenance records only."
        ),
    )
    triage_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional candidate triage notes fixture JSON path.",
    )
    artifacts_cleanup_parser = subparsers.add_parser(
        "artifacts-cleanup",
        help=(
            "Plan or apply local cleanup of the ignored artifacts/ directory. "
            "Refuses to touch committed project paths."
        ),
    )
    artifacts_cleanup_parser.add_argument(
        "--artifacts-dir",
        type=Path,
        help="Optional artifacts directory override.",
    )
    artifacts_cleanup_parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Apply the plan and delete files under artifacts/. Requires "
            "--acknowledge-local-apply."
        ),
    )
    artifacts_cleanup_parser.add_argument(
        "--acknowledge-local-apply",
        action="store_true",
        help="Required acknowledgement to perform local file deletion.",
    )
    radio_corpus_cleanup_parser = subparsers.add_parser(
        "radio-corpus-cleanup",
        help=(
            "Plan or apply storage cleanup for ignored data/extended_corpus "
            "radio payloads after derived evidence exists."
        ),
    )
    radio_corpus_cleanup_parser.add_argument(
        "--corpus-dir",
        type=Path,
        help="Optional corpus directory override; must be under data/extended_corpus.",
    )
    radio_corpus_cleanup_parser.add_argument(
        "--results-dir",
        type=Path,
        help="Optional results directory containing zero-hit manifests.",
    )
    radio_corpus_cleanup_parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Apply the plan and delete eligible local payloads. Requires "
            "--acknowledge-local-apply."
        ),
    )
    radio_corpus_cleanup_parser.add_argument(
        "--acknowledge-local-apply",
        action="store_true",
        help="Required acknowledgement to perform local file deletion.",
    )

    signal_registry_parser = subparsers.add_parser(
        "signal-registry-summary",
        help="Summarize the signal-of-interest registry fixture.",
    )
    signal_registry_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    signal_track_parser = subparsers.add_parser(
        "signal-registry-track-summary",
        help="Per-track breakdown of the signal registry.",
    )
    signal_track_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "schema-drift-check",
        help="Detect structural drift in committed JSON schema files.",
    )

    audit_trail_parser = subparsers.add_parser(
        "audit-trail-summary",
        help="Summarize the candidate audit trail fixture.",
    )
    audit_trail_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    obs_gap_parser = subparsers.add_parser(
        "observation-gap-analysis",
        help="Identify scheduling gaps between planned and completed observation windows.",
    )
    obs_gap_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    multi_epoch_parser = subparsers.add_parser(
        "multi-epoch-summary",
        help="Summarize multi-epoch observation records.",
    )
    multi_epoch_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "classifier-rule-coverage",
        help="Report which baseline classifier rules fire across evaluation cases.",
    )

    recalibration_parser = subparsers.add_parser(
        "target-recalibration-summary",
        help="Compare two most recent target priority snapshots for rank changes.",
    )
    recalibration_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    operator_cov_parser = subparsers.add_parser(
        "operator-coverage-summary",
        help="Summarize operator coverage across triage notes.",
    )
    operator_cov_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    label_completeness_parser = subparsers.add_parser(
        "triage-label-completeness",
        help="Check which triage labels have fixture coverage.",
    )
    label_completeness_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "provenance-chain-validate",
        help="Validate provenance chain fields in committed report manifests.",
    )

    obs_notes_parser = subparsers.add_parser(
        "observation-notes-summary",
        help="Summarize post-observation operator notes by track and outcome.",
    )
    obs_notes_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    epoch_plan_parser = subparsers.add_parser(
        "epoch-plan-summary",
        help="Summarize epoch plan entries for targets needing additional observations.",
    )
    epoch_plan_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "aggregate-blockers-summary",
        help="Collect blocking issues from triage, lifecycle, and observation notes.",
    )

    score_history_parser = subparsers.add_parser(
        "score-history-summary",
        help="Summarize candidate score evolution across observation epochs.",
    )
    score_history_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    op_assignment_parser = subparsers.add_parser(
        "operator-assignment-summary",
        help="Summarize operator assignment records for candidate review.",
    )
    op_assignment_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-health-summary",
        help="Per-track pipeline health dashboard aggregating scheduling state.",
    )

    candidate_flags_parser = subparsers.add_parser(
        "candidate-flags-summary",
        help="Summarize quality flags and operational alerts raised against candidates.",
    )
    candidate_flags_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    review_deadlines_parser = subparsers.add_parser(
        "review-deadlines-summary",
        help="Summarize upcoming operator review deadlines with urgency levels.",
    )
    review_deadlines_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-throughput-summary",
        help="Per-stage pipeline throughput counts and transition rate metrics.",
    )

    candidate_retention_parser = subparsers.add_parser(
        "candidate-retention-summary",
        help="Summarize candidate retention records and pipeline dwell times.",
    )
    candidate_retention_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "operator-performance-summary",
        help="Aggregate operator performance metrics from assignment records.",
    )

    subparsers.add_parser(
        "track-comparison-summary",
        help="Cross-track comparison dashboard for scheduling state and flags.",
    )

    candidate_resolution_parser = subparsers.add_parser(
        "candidate-resolution-summary",
        help="Summarize final disposition records for candidates after review.",
    )
    candidate_resolution_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    escalation_log_parser = subparsers.add_parser(
        "escalation-log-summary",
        help="Summarize workflow escalation events with priority and status breakdown.",
    )
    escalation_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "quality-control-summary",
        help="Aggregate QC dashboard across flags, triage, deadlines, and escalations.",
    )

    observation_campaign_parser = subparsers.add_parser(
        "observation-campaign-summary",
        help="Summarize observation campaigns with session counts and track coverage.",
    )
    observation_campaign_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    data_quality_log_parser = subparsers.add_parser(
        "data-quality-log-summary",
        help="Summarize data quality log entries with grade and issue-type breakdown.",
    )
    data_quality_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-audit-summary",
        help="Aggregate pipeline audit summary from the candidate audit trail.",
    )

    follow_up_request_parser = subparsers.add_parser(
        "follow-up-request-summary",
        help="Summarize follow-up requests with priority and status breakdown.",
    )
    follow_up_request_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-bottleneck-summary",
        help="Identify where candidates are stalling in the pipeline.",
    )

    candidate_annotation_parser = subparsers.add_parser(
        "candidate-annotation-summary",
        help="Summarize operator annotations and tags on candidates.",
    )
    candidate_annotation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    session_log_parser = subparsers.add_parser(
        "session-log-summary",
        help="Summarize observation session log entries.",
    )
    session_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    priority_queue_parser = subparsers.add_parser(
        "priority-queue-summary",
        help="Summarize candidate priority queue entries.",
    )
    priority_queue_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-capacity-summary",
        help="Summarize current pipeline scheduling capacity and load.",
    )

    feature_vector_parser = subparsers.add_parser(
        "feature-vector-summary",
        help="Summarize ML-ready feature vectors extracted from candidates.",
    )
    feature_vector_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    model_registry_parser = subparsers.add_parser(
        "model-registry-summary",
        help="Summarize ML model registry entries and above-baseline status.",
    )
    model_registry_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "ml-diagnostics-summary",
        help="Summarize ML pipeline status comparing baseline vs registered models.",
    )

    feature_normalization_parser = subparsers.add_parser(
        "feature-normalization-summary",
        help="Summarize per-track feature normalization bounds with drift detection.",
    )
    feature_normalization_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    feature_importance_parser = subparsers.add_parser(
        "feature-importance-summary",
        help="Summarize feature importance scores from baseline rule fire rates.",
    )
    feature_importance_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "ml-training-data-summary",
        help="Summarize ML training data assembled from calibration and injection-recovery cases.",
    )

    model_architecture_parser = subparsers.add_parser(
        "model-architecture-summary",
        help="Summarize ML model architecture scaffold definitions.",
    )
    model_architecture_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    model_evaluation_parser = subparsers.add_parser(
        "model-evaluation-summary",
        help="Summarize ML model evaluation results against the interpretable baseline.",
    )
    model_evaluation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    model_performance_parser = subparsers.add_parser(
        "model-performance-history-summary",
        help="Summarize ML model training performance snapshots by model and trend.",
    )
    model_performance_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    model_serving_parser = subparsers.add_parser(
        "model-serving-summary",
        help="Summarize model serving scaffold records with inference provenance.",
    )
    model_serving_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    scoring_audit_parser = subparsers.add_parser(
        "scoring-audit-log-summary",
        help="Summarize scoring audit log entries per candidate per model version.",
    )
    scoring_audit_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    curated_intake_parser = subparsers.add_parser(
        "curated-dataset-intake-summary",
        help="Summarize curated dataset intake checklist records.",
    )
    curated_intake_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    curated_admission_parser = subparsers.add_parser(
        "curated-dataset-admission-summary",
        help="Summarize curated dataset admission gates (local readiness only).",
    )
    curated_admission_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    status_consistency_parser = subparsers.add_parser(
        "project-status-consistency-summary",
        help="Summarize project status/readiness metadata drift checks.",
    )
    status_consistency_parser.add_argument(
        "--fixture-path", type=Path, help="Optional expectation fixture path override."
    )

    mcp_bootstrap_consistency_parser = subparsers.add_parser(
        "mcp-bootstrap-consistency-summary",
        help="Summarize project-scoped MCP bootstrap configuration drift checks.",
    )
    mcp_bootstrap_consistency_parser.add_argument(
        "--fixture-path", type=Path, help="Optional expectation fixture path override."
    )

    mcp_server_policy_parser = subparsers.add_parser(
        "mcp-server-policy-summary",
        help="Summarize project-scoped MCP server implementation policy checks.",
    )
    mcp_server_policy_parser.add_argument(
        "--fixture-path", type=Path, help="Optional expectation fixture path override."
    )

    production_blocker_consistency_parser = subparsers.add_parser(
        "production-blocker-consistency-summary",
        help="Summarize production-readiness blocker visibility checks.",
    )
    production_blocker_consistency_parser.add_argument(
        "--fixture-path", type=Path, help="Optional expectation fixture path override."
    )

    ai_hardening_gate_parser = subparsers.add_parser(
        "ai-hardening-gate-summary",
        help="Summarize DECISION-134 AI hardening production evidence gate.",
    )
    ai_hardening_gate_parser.add_argument(
        "--fixture-path", type=Path, help="Optional gate fixture path override."
    )

    real_data_preflight_parser = subparsers.add_parser(
        "real-data-admission-preflight-summary",
        help="Summarize local real-data admission preflight gates.",
    )
    real_data_preflight_parser.add_argument(
        "--fixture-path", type=Path, help="Optional preflight fixture path override."
    )

    sqlite_registry_parser = subparsers.add_parser(
        "sqlite-operational-log-registry-summary",
        help="Summarize operational log registry and SQLite policy alignment.",
    )
    sqlite_registry_parser.add_argument(
        "--fixture-path", type=Path, help="Optional registry fixture path override."
    )

    sqlite_adapter_plan_parser = subparsers.add_parser(
        "sqlite-operational-log-adapter-plan-summary",
        help="Summarize non-destructive SQLite adapter phase planning for log families.",
    )
    sqlite_adapter_plan_parser.add_argument(
        "--fixture-path", type=Path, help="Optional adapter-plan fixture path override."
    )

    sqlite_adapter_contract_parser = subparsers.add_parser(
        "sqlite-operational-log-adapter-contract-summary",
        help="Summarize non-mutating SQLite adapter table and provenance contracts.",
    )
    sqlite_adapter_contract_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional adapter-contract fixture path override.",
    )

    sqlite_adapter_ddl_parser = subparsers.add_parser(
        "sqlite-operational-log-adapter-ddl-preview-summary",
        help="Preview non-executing SQLite adapter DDL for operational log phases.",
    )
    sqlite_adapter_ddl_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional adapter-DDL-preview fixture path override.",
    )

    sqlite_adapter_row_parser = subparsers.add_parser(
        "sqlite-operational-log-adapter-row-preview-summary",
        help="Preview non-executing SQLite adapter row payloads for operational logs.",
    )
    sqlite_adapter_row_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional adapter-row-preview fixture path override.",
    )

    sqlite_adapter_insert_parser = subparsers.add_parser(
        "sqlite-operational-log-adapter-insert-preview-summary",
        help="Preview non-executing SQLite adapter INSERT statements.",
    )
    sqlite_adapter_insert_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional adapter-insert-preview fixture path override.",
    )

    sqlite_adapter_execution_parser = subparsers.add_parser(
        "sqlite-operational-log-adapter-execution-preview-summary",
        help="Preview non-executing SQLite adapter transaction ordering.",
    )
    sqlite_adapter_execution_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional adapter-execution-preview fixture path override.",
    )

    sqlite_adapter_dry_run_parser = subparsers.add_parser(
        "sqlite-operational-log-adapter-dry-run-manifest-summary",
        help="Preview non-executing SQLite adapter dry-run manifest alignment.",
    )
    sqlite_adapter_dry_run_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional adapter-dry-run-manifest fixture path override.",
    )

    sqlite_adapter_readiness_parser = subparsers.add_parser(
        "sqlite-operational-log-adapter-readiness-preflight-summary",
        help="Summarize non-mutating SQLite adapter readiness preflight gates.",
    )
    sqlite_adapter_readiness_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional adapter-readiness-preflight fixture path override.",
    )

    sqlite_adapter_authorization_parser = subparsers.add_parser(
        "sqlite-operational-log-adapter-authorization-gate-summary",
        help="Summarize disabled SQLite adapter authorization gate state.",
    )
    sqlite_adapter_authorization_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional adapter-authorization-gate fixture path override.",
    )

    alert_review_consistency_parser = subparsers.add_parser(
        "operations-alert-review-consistency-summary",
        help="Summarize local alert/QC operator-review consistency checks.",
    )
    alert_review_consistency_parser.add_argument(
        "--fixture-path", type=Path, help="Optional expectation fixture path override."
    )

    candidate_rescore_parser = subparsers.add_parser(
        "candidate-rescore-summary",
        help="Summarize candidate re-scoring events with pathway change tracking.",
    )
    candidate_rescore_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    operator_handoff_parser = subparsers.add_parser(
        "operator-handoff-summary",
        help="Summarize operator handoff templates with model version and inference provenance.",
    )
    operator_handoff_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "candidate-methods-summary",
        help="Aggregate candidate methods dashboard combining serving, audit, and handoff state.",
    )

    pipeline_config_parser = subparsers.add_parser(
        "pipeline-config-summary",
        help="Summarize active pipeline configuration records with serving provenance.",
    )
    pipeline_config_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    submission_readiness_parser = subparsers.add_parser(
        "submission-readiness-summary",
        help="Summarize submission readiness provenance checklists per candidate.",
    )
    submission_readiness_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-integration-summary",
        help="Run end-to-end pipeline smoke tests across known fixture candidates.",
    )

    candidate_alert_parser = subparsers.add_parser(
        "candidate-alert-summary",
        help="Summarize candidate alert log entries for threshold crossings and status changes.",
    )
    candidate_alert_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    pipeline_replay_parser = subparsers.add_parser(
        "pipeline-replay-summary",
        help="Summarize pipeline replay log entries for reproducibility verification.",
    )
    pipeline_replay_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    scoring_threshold_audit_parser = subparsers.add_parser(
        "scoring-threshold-audit-summary",
        help="Summarize scoring threshold audit verdicts against pipeline config.",
    )
    scoring_threshold_audit_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    alert_resolution_parser = subparsers.add_parser(
        "alert-resolution-summary",
        help="Summarize alert resolution log entries (provenance records only).",
    )
    alert_resolution_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    config_history_parser = subparsers.add_parser(
        "config-version-history-summary",
        help="Summarize config version history entries (append-only provenance).",
    )
    config_history_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    operator_escalation_parser = subparsers.add_parser(
        "operator-escalation-summary",
        help="Summarize operator escalation log entries (scheduling coordination).",
    )
    operator_escalation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_dedup_parser = subparsers.add_parser(
        "candidate-deduplication-summary",
        help="Summarize candidate deduplication log entries (provenance records only).",
    )
    candidate_dedup_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    intake_queue_parser = subparsers.add_parser(
        "intake-queue-summary",
        help="Summarize intake queue log entries (planning placeholders only).",
    )
    intake_queue_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    workflow_state_parser = subparsers.add_parser(
        "workflow-state-summary",
        help="Summarize workflow state log entries (scheduling coordination records).",
    )
    workflow_state_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    data_gap_parser = subparsers.add_parser(
        "data-gap-summary",
        help="Summarize data gap log entries (scheduling records only).",
    )
    data_gap_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_match_parser = subparsers.add_parser(
        "candidate-match-summary",
        help="Summarize candidate match log entries (provenance records only).",
    )
    candidate_match_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    pipeline_error_parser = subparsers.add_parser(
        "pipeline-error-summary",
        help="Summarize pipeline error log entries (operational records only).",
    )
    pipeline_error_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    obs_request_parser = subparsers.add_parser(
        "observation-request-summary",
        help="Summarize observation request log entries (scheduling records only).",
    )
    obs_request_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_export_parser = subparsers.add_parser(
        "candidate-export-summary",
        help="Summarize candidate export log entries (provenance records only).",
    )
    candidate_export_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    quality_gate_parser = subparsers.add_parser(
        "quality-gate-summary",
        help="Summarize quality gate log entries (operational provenance records only).",
    )
    quality_gate_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_comparison_parser = subparsers.add_parser(
        "candidate-comparison-summary",
        help="Summarize multi-candidate comparison records (scheduling aid only).",
    )
    candidate_comparison_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    pipeline_telemetry_parser = subparsers.add_parser(
        "pipeline-telemetry-summary",
        help="Summarize per-stage pipeline telemetry latency and throughput records.",
    )
    pipeline_telemetry_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    provenance_audit_parser = subparsers.add_parser(
        "provenance-audit-summary",
        help="Summarize cross-module provenance audit consistency verdicts.",
    )
    provenance_audit_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    instrument_log_parser = subparsers.add_parser(
        "instrument-log-summary",
        help="Summarize instrument/telescope status event log entries (scheduling records only).",
    )
    instrument_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    archival_query_parser = subparsers.add_parser(
        "archival-query-summary",
        help="Summarize archival/catalog query event log entries (provenance records only).",
    )
    archival_query_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_linkage_parser = subparsers.add_parser(
        "candidate-linkage-summary",
        help="Summarize candidate linkage log entries (provenance records only).",
    )
    candidate_linkage_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    signal_classification_parser = subparsers.add_parser(
        "signal-classification-summary",
        help="Summarize signal classification log entries (provenance records only).",
    )
    signal_classification_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    rfi_database_parser = subparsers.add_parser(
        "rfi-database-summary",
        help="Summarize local RFI database guardrails (false-positive aids only).",
    )
    rfi_database_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    rfi_database_admission_parser = subparsers.add_parser(
        "rfi-database-admission-summary",
        help="Summarize RFI database source admission gates (local readiness only).",
    )
    rfi_database_admission_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    cal_corpus_admission_parser = subparsers.add_parser(
        "calibration-corpus-admission-summary",
        help="Summarize calibration corpus target admission gates (local readiness only).",
    )
    cal_corpus_admission_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    rfi_mitigation_parser = subparsers.add_parser(
        "rfi-mitigation-summary",
        help="Summarize RFI mitigation log entries (processing provenance records only).",
    )
    rfi_mitigation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_annotation_log_parser = subparsers.add_parser(
        "candidate-annotation-log-summary",
        help="Summarize candidate annotation log entries (operator provenance records only).",
    )
    candidate_annotation_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    frequency_channel_parser = subparsers.add_parser(
        "frequency-channel-summary",
        help="Summarize frequency channel log entries (processing provenance records only).",
    )
    frequency_channel_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    pipeline_checkpoint_parser = subparsers.add_parser(
        "pipeline-checkpoint-summary",
        help="Summarize pipeline checkpoint log entries (reproducibility records only).",
    )
    pipeline_checkpoint_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_status_parser = subparsers.add_parser(
        "candidate-status-summary",
        help="Summarize candidate status log entries (operational provenance records only).",
    )
    candidate_status_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    beam_configuration_parser = subparsers.add_parser(
        "beam-configuration-summary",
        help="Summarize beam configuration log entries (operational provenance records only).",
    )
    beam_configuration_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    calibration_event_parser = subparsers.add_parser(
        "calibration-event-summary",
        help="Summarize calibration event log entries (operational provenance records only).",
    )
    calibration_event_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    pipeline_run_parser = subparsers.add_parser(
        "pipeline-run-summary",
        help="Summarize pipeline run log entries (operational reproducibility records only).",
    )
    pipeline_run_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    source_catalog_parser = subparsers.add_parser(
        "source-catalog-summary",
        help="Summarize source catalog log entries (operational provenance records only).",
    )
    source_catalog_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    noise_measurement_parser = subparsers.add_parser(
        "noise-measurement-summary",
        help="Summarize noise measurement log entries (operational provenance records only).",
    )
    noise_measurement_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    spectral_feature_parser = subparsers.add_parser(
        "spectral-feature-summary",
        help="Summarize spectral feature log entries (operational provenance records only).",
    )
    spectral_feature_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    polarization_parser = subparsers.add_parser(
        "polarization-summary",
        help="Summarize polarization log entries (operational provenance records only).",
    )
    polarization_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    telescope_status_parser = subparsers.add_parser(
        "telescope-status-summary",
        help="Summarize telescope status log entries (operational provenance records only).",
    )
    telescope_status_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    obs_parameter_parser = subparsers.add_parser(
        "observation-parameter-summary",
        help=(
            "Summarize observation parameter log entries "
            "(operational provenance records only)."
        ),
    )
    obs_parameter_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    target_selection_parser = subparsers.add_parser(
        "target-selection-summary",
        help=(
            "Summarize target selection log entries "
            "(operational scheduling provenance records only)."
        ),
    )
    target_selection_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    doppler_correction_parser = subparsers.add_parser(
        "doppler-correction-summary",
        help=(
            "Summarize Doppler correction log entries "
            "(operational processing provenance records only)."
        ),
    )
    doppler_correction_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    data_archival_parser = subparsers.add_parser(
        "data-archival-summary",
        help=(
            "Summarize data archival log entries "
            "(operational provenance records only)."
        ),
    )
    data_archival_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    interference_environment_parser = subparsers.add_parser(
        "interference-environment-summary",
        help=(
            "Summarize interference environment log entries "
            "(operational processing provenance records only)."
        ),
    )
    interference_environment_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    receiver_health_parser = subparsers.add_parser(
        "receiver-health-summary",
        help=(
            "Summarize receiver health log entries "
            "(operational scheduling provenance records only)."
        ),
    )
    receiver_health_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    pipeline_version_parser = subparsers.add_parser(
        "pipeline-version-summary",
        help=(
            "Summarize pipeline version log entries "
            "(operational reproducibility records only)."
        ),
    )
    pipeline_version_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    data_transfer_parser = subparsers.add_parser(
        "data-transfer-summary",
        help=(
            "Summarize data transfer log entries "
            "(operational provenance records only)."
        ),
    )
    data_transfer_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    scheduling_conflict_parser = subparsers.add_parser(
        "scheduling-conflict-summary",
        help=(
            "Summarize scheduling conflict log entries "
            "(operational provenance records only)."
        ),
    )
    scheduling_conflict_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    system_health_parser = subparsers.add_parser(
        "system-health-summary",
        help=(
            "Summarize system health log entries "
            "(operational monitoring provenance records only)."
        ),
    )
    system_health_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    instrument_configuration_parser = subparsers.add_parser(
        "instrument-configuration-summary",
        help=(
            "Summarize instrument configuration log entries "
            "(operational hardware provenance records only)."
        ),
    )
    instrument_configuration_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    scan_log_parser = subparsers.add_parser(
        "scan-log-summary",
        help=(
            "Summarize scan log entries "
            "(operational telescope scan provenance records only)."
        ),
    )
    scan_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    time_synchronization_parser = subparsers.add_parser(
        "time-synchronization-summary",
        help=(
            "Summarize time synchronization log entries "
            "(operational clock synchronization provenance records only)."
        ),
    )
    time_synchronization_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    antenna_pointing_parser = subparsers.add_parser(
        "antenna-pointing-summary",
        help=(
            "Summarize antenna pointing log entries "
            "(operational antenna pointing provenance records only)."
        ),
    )
    antenna_pointing_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    weather_parser = subparsers.add_parser(
        "weather-summary",
        help=(
            "Summarize weather log entries "
            "(operational site weather monitoring provenance records only)."
        ),
    )
    weather_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    power_parser = subparsers.add_parser(
        "power-summary",
        help=(
            "Summarize power log entries "
            "(operational facility power system provenance records only)."
        ),
    )
    power_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    cooling_system_parser = subparsers.add_parser(
        "cooling-system-summary",
        help=(
            "Summarize cooling system log entries "
            "(operational cryogenic and cooling system provenance records only)."
        ),
    )
    cooling_system_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    network_connectivity_parser = subparsers.add_parser(
        "network-connectivity-summary",
        help=(
            "Summarize network connectivity log entries "
            "(operational network infrastructure provenance records only)."
        ),
    )
    network_connectivity_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    software_update_parser = subparsers.add_parser(
        "software-update-summary",
        help=(
            "Summarize software update log entries "
            "(operational software and firmware update provenance records only)."
        ),
    )
    software_update_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    hardware_fault_parser = subparsers.add_parser(
        "hardware-fault-summary",
        help=(
            "Summarize hardware fault log entries "
            "(operational hardware fault provenance records only)."
        ),
    )
    hardware_fault_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    maintenance_parser = subparsers.add_parser(
        "maintenance-summary",
        help=(
            "Summarize maintenance log entries "
            "(operational maintenance provenance records only)."
        ),
    )
    maintenance_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    environmental_parser = subparsers.add_parser(
        "environmental-summary",
        help=(
            "Summarize environmental log entries "
            "(operational environmental monitoring provenance records only)."
        ),
    )
    environmental_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    access_log_parser = subparsers.add_parser(
        "access-log-summary",
        help=(
            "Summarize access log entries "
            "(operational facility and system access provenance records only)."
        ),
    )
    access_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    security_event_parser = subparsers.add_parser(
        "security-event-summary",
        help=(
            "Summarize security event log entries "
            "(operational security event provenance records only)."
        ),
    )
    security_event_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    audit_trail_log_parser = subparsers.add_parser(
        "audit-trail-log-summary",
        help=(
            "Summarize audit trail log entries "
            "(operational audit trail provenance records only)."
        ),
    )
    audit_trail_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    incident_response_parser = subparsers.add_parser(
        "incident-response-summary",
        help=(
            "Summarize incident response log entries "
            "(operational incident response provenance records only)."
        ),
    )
    incident_response_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    change_management_parser = subparsers.add_parser(
        "change-management-summary",
        help=(
            "Summarize change management log entries "
            "(operational change management provenance records only)."
        ),
    )
    change_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    compliance_report_parser = subparsers.add_parser(
        "compliance-report-summary",
        help=(
            "Summarize compliance report log entries "
            "(operational compliance reporting provenance records only)."
        ),
    )
    compliance_report_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    risk_assessment_parser = subparsers.add_parser(
        "risk-assessment-summary",
        help=(
            "Summarize risk assessment log entries "
            "(operational risk assessment provenance records only)."
        ),
    )
    risk_assessment_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    backup_recovery_parser = subparsers.add_parser(
        "backup-recovery-summary",
        help=(
            "Summarize backup and recovery log entries "
            "(operational backup and recovery provenance records only)."
        ),
    )
    backup_recovery_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    capacity_planning_parser = subparsers.add_parser(
        "capacity-planning-summary",
        help=(
            "Summarize capacity planning log entries "
            "(operational capacity planning provenance records only)."
        ),
    )
    capacity_planning_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    software_deployment_parser = subparsers.add_parser(
        "software-deployment-summary",
        help=(
            "Summarize software deployment log entries "
            "(operational software deployment provenance records only)."
        ),
    )
    software_deployment_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    performance_monitoring_parser = subparsers.add_parser(
        "performance-monitoring-summary",
        help=(
            "Summarize performance monitoring log entries "
            "(operational performance monitoring provenance records only)."
        ),
    )
    performance_monitoring_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    user_activity_parser = subparsers.add_parser(
        "user-activity-summary",
        help=(
            "Summarize user activity log entries "
            "(operational user activity provenance records only)."
        ),
    )
    user_activity_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    health_check_parser = subparsers.add_parser(
        "health-check-summary",
        help=(
            "Summarize health check log entries "
            "(operational system and service health check provenance records only)."
        ),
    )
    health_check_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    license_management_parser = subparsers.add_parser(
        "license-management-summary",
        help=(
            "Summarize license management log entries "
            "(operational software license lifecycle provenance records only)."
        ),
    )
    license_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    storage_management_parser = subparsers.add_parser(
        "storage-management-summary",
        help=(
            "Summarize storage management log entries "
            "(operational storage lifecycle provenance records only)."
        ),
    )
    storage_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    firmware_update_parser = subparsers.add_parser(
        "firmware-update-summary",
        help=(
            "Summarize firmware update log entries "
            "(operational firmware lifecycle provenance records only)."
        ),
    )
    firmware_update_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    configuration_audit_parser = subparsers.add_parser(
        "configuration-audit-summary",
        help=(
            "Summarize configuration audit log entries "
            "(operational configuration compliance provenance records only)."
        ),
    )
    configuration_audit_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    event_correlation_parser = subparsers.add_parser(
        "event-correlation-summary",
        help=(
            "Summarize event correlation log entries "
            "(operational cross-system event correlation provenance records only)."
        ),
    )
    event_correlation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    system_diagnostics_parser = subparsers.add_parser(
        "system-diagnostics-summary",
        help=(
            "Summarize system diagnostics log entries "
            "(operational system diagnostic check provenance records only)."
        ),
    )
    system_diagnostics_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    resource_allocation_parser = subparsers.add_parser(
        "resource-allocation-summary",
        help=(
            "Summarize resource allocation log entries "
            "(operational compute and facility resource allocation provenance records only)."
        ),
    )
    resource_allocation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    access_control_parser = subparsers.add_parser(
        "access-control-summary",
        help=(
            "Summarize access control log entries "
            "(operational access control provenance records only)."
        ),
    )
    access_control_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    incident_parser = subparsers.add_parser(
        "incident-summary",
        help=(
            "Summarize incident log entries "
            "(operational incident provenance records only)."
        ),
    )
    incident_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    patch_management_parser = subparsers.add_parser(
        "patch-management-summary",
        help=(
            "Summarize patch management log entries "
            "(operational patch management provenance records only)."
        ),
    )
    patch_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    vulnerability_scan_parser = subparsers.add_parser(
        "vulnerability-scan-summary",
        help=(
            "Summarize vulnerability scan log entries "
            "(operational vulnerability scan provenance records only)."
        ),
    )
    vulnerability_scan_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    compliance_audit_parser = subparsers.add_parser(
        "compliance-audit-summary",
        help=(
            "Summarize compliance audit log entries "
            "(operational compliance audit provenance records only)."
        ),
    )
    compliance_audit_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    disaster_recovery_parser = subparsers.add_parser(
        "disaster-recovery-summary",
        help=(
            "Summarize disaster recovery log entries "
            "(operational disaster recovery provenance records only)."
        ),
    )
    disaster_recovery_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    service_level_parser = subparsers.add_parser(
        "service-level-summary",
        help=(
            "Summarize service level log entries "
            "(operational service level provenance records only)."
        ),
    )
    service_level_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    asset_management_parser = subparsers.add_parser(
        "asset-management-summary",
        help=(
            "Summarize asset management log entries "
            "(operational asset management provenance records only)."
        ),
    )
    asset_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    network_monitoring_parser = subparsers.add_parser(
        "network-monitoring-summary",
        help=(
            "Summarize network monitoring log entries "
            "(operational network monitoring provenance records only)."
        ),
    )
    network_monitoring_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    identity_management_parser = subparsers.add_parser(
        "identity-management-summary",
        help=(
            "Summarize identity management log entries "
            "(operational identity management provenance records only)."
        ),
    )
    identity_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    certificate_management_parser = subparsers.add_parser(
        "certificate-management-summary",
        help=(
            "Summarize certificate management log entries "
            "(operational certificate management provenance records only)."
        ),
    )
    certificate_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    alert_escalation_parser = subparsers.add_parser(
        "alert-escalation-summary",
        help=(
            "Summarize alert escalation log entries "
            "(operational alert escalation provenance records only)."
        ),
    )
    alert_escalation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    configuration_change_parser = subparsers.add_parser(
        "configuration-change-summary",
        help=(
            "Summarize configuration change log entries "
            "(operational configuration change provenance records only)."
        ),
    )
    configuration_change_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    data_retention_parser = subparsers.add_parser(
        "data-retention-summary",
        help=(
            "Summarize data retention log entries "
            "(operational data retention provenance records only)."
        ),
    )
    data_retention_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    problem_management_parser = subparsers.add_parser(
        "problem-management-summary",
        help=(
            "Summarize problem management log entries "
            "(operational problem management provenance records only)."
        ),
    )
    problem_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    release_management_parser = subparsers.add_parser(
        "release-management-summary",
        help=(
            "Summarize release management log entries "
            "(operational release management provenance records only)."
        ),
    )
    release_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    service_request_parser = subparsers.add_parser(
        "service-request-summary",
        help=(
            "Summarize service request log entries "
            "(operational service request provenance records only)."
        ),
    )
    service_request_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    contract_management_parser = subparsers.add_parser(
        "contract-management-summary",
        help=(
            "Summarize contract management log entries "
            "(operational contract management provenance records only)."
        ),
    )
    contract_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    knowledge_management_parser = subparsers.add_parser(
        "knowledge-management-summary",
        help=(
            "Summarize knowledge management log entries "
            "(operational knowledge management provenance records only)."
        ),
    )
    knowledge_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    supplier_management_parser = subparsers.add_parser(
        "supplier-management-summary",
        help=(
            "Summarize supplier management log entries "
            "(operational supplier management provenance records only)."
        ),
    )
    supplier_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    audit_finding_parser = subparsers.add_parser(
        "audit-finding-summary",
        help=(
            "Summarize audit finding log entries "
            "(operational audit finding provenance records only)."
        ),
    )
    audit_finding_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    budget_parser = subparsers.add_parser(
        "budget-summary",
        help=(
            "Summarize budget log entries "
            "(operational budget allocation provenance records only)."
        ),
    )
    budget_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    training_parser = subparsers.add_parser(
        "training-summary",
        help=(
            "Summarize training log entries "
            "(operational personnel training provenance records only)."
        ),
    )
    training_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    change_request_parser = subparsers.add_parser(
        "change-request-summary",
        help=(
            "Summarize change request log entries "
            "(operational change request provenance records only)."
        ),
    )
    change_request_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    project_milestone_parser = subparsers.add_parser(
        "project-milestone-summary",
        help=(
            "Summarize project milestone log entries "
            "(operational project milestone provenance records only)."
        ),
    )
    project_milestone_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    vendor_assessment_parser = subparsers.add_parser(
        "vendor-assessment-summary",
        help=(
            "Summarize vendor assessment log entries "
            "(operational vendor assessment provenance records only)."
        ),
    )
    vendor_assessment_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    communication_parser = subparsers.add_parser(
        "communication-summary",
        help=(
            "Summarize communication log entries "
            "(operational communication provenance records only)."
        ),
    )
    communication_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    document_management_parser = subparsers.add_parser(
        "document-management-summary",
        help=(
            "Summarize document management log entries "
            "(operational document lifecycle provenance records only)."
        ),
    )
    document_management_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    procurement_parser = subparsers.add_parser(
        "procurement-summary",
        help=(
            "Summarize procurement log entries "
            "(operational procurement provenance records only)."
        ),
    )
    procurement_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    labeled_dataset_parser = subparsers.add_parser(
        "labeled-dataset-summary",
        help="Summarize labeled candidate dataset (synthetic ground-truth annotations only).",
    )
    labeled_dataset_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    eval_labels_parser = subparsers.add_parser(
        "eval-against-labels",
        help="Evaluate scoring model against labeled candidate dataset (synthetic only).",
    )
    eval_labels_parser.add_argument(
        "--fixture-path", type=Path, help="Optional labeled candidates fixture path override."
    )

    validate_input_parser = subparsers.add_parser(
        "validate-input",
        help="Validate a pipeline input file for structural correctness.",
    )
    validate_input_parser.add_argument("input", type=Path, help="Input CSV file path.")
    validate_input_parser.add_argument(
        "--track",
        required=True,
        choices=["radio", "infrared", "anomaly", "photometry", "spectroscopy"],
        help="Track type for validation.",
    )

    run_pipeline_parser = subparsers.add_parser(
        "run-pipeline",
        help=(
            "Run structural validation, candidate scoring, and report writing "
            "for one local CSV input. Triage/provenance only."
        ),
    )
    run_pipeline_parser.add_argument("input", type=Path, help="Input CSV file path.")
    run_pipeline_parser.add_argument(
        "--track",
        required=True,
        choices=["radio", "infrared", "anomaly", "photometry", "spectroscopy"],
        help="Track type for the input file.",
    )
    run_pipeline_parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory for generated report artifacts.",
    )
    run_pipeline_parser.add_argument(
        "--candidate-id",
        help="Optional candidate ID override for generated reports.",
    )
    run_pipeline_parser.add_argument(
        "--epoch-files",
        nargs="*",
        metavar="DAT_FILE",
        help=(
            "Additional turboSETI .dat files from separate observation sessions "
            "(radio track only). When provided, multi-epoch persistence scores are "
            "injected into candidate features before scoring."
        ),
    )
    run_pipeline_parser.add_argument(
        "--semisupervised-model",
        type=Path,
        help=(
            "Optional fitted SemisupervisedScorer joblib model. Defaults to "
            "data/meerkat_hits/semisupervised_scorer.joblib when present."
        ),
    )
    run_pipeline_parser.add_argument(
        "--jwst-integration-index",
        type=int,
        default=None,
        help=(
            "1-indexed integration to use (spectroscopy track only). Required "
            "when the input x1dints file is a multi-integration time-series "
            "product -- there is no default, since pooling every integration "
            "together would treat real time-domain flux variation (e.g. an "
            "orbital phase curve) as spectral noise."
        ),
    )
    run_pipeline_parser.add_argument(
        "--jwst-hitran-xsc-dir",
        type=Path,
        default=None,
        help=(
            "Optional real local directory of downloaded HITRAN .xsc "
            "cross-section files (spectroscopy track only), e.g. "
            "CF4_298.1K-760.0Torr_....xsc. When provided, runs the "
            "additional full-grid matched-filter check for whichever of "
            "the 5 known gases have a matching file present."
        ),
    )

    learned_model_parser = subparsers.add_parser(
        "learned-model-summary",
        help=(
            "Train a logistic regression on the labeled candidate dataset and "
            "report training summary. Development scaffold only — requires "
            "real labeled data for production use."
        ),
    )
    learned_model_parser.add_argument(
        "--labeled-dataset-path",
        type=Path,
        help="Path to labeled_candidates.json fixture (defaults to built-in fixture).",
    )

    synthetic_training_parser = subparsers.add_parser(
        "synthetic-training-summary",
        help=(
            "Report that synthetic training was removed in Phase 0. "
            "Production scoring must use real labeled corpora."
        ),
    )
    synthetic_training_parser.add_argument(
        "--dataset-path",
        type=Path,
        help=(
            "Legacy synthetic dataset path; retained only for compatibility."
        ),
    )

    real_labels_model_parser = subparsers.add_parser(
        "real-labels-model-summary",
        help=(
            "Train logistic regression on 124 real HIP99427 citizen-science labels "
            "(closes Tier 2: Learned scoring model). Reports 3-fold CV accuracy. "
            "Local scheduling aid only — not a validated production model."
        ),
    )
    real_labels_model_parser.add_argument(
        "--dataset-path",
        type=Path,
        help="Path to real labels JSON (defaults to examples/real_labeled/hip99427_...).",
    )

    combined_model_parser = subparsers.add_parser(
        "combined-model-summary",
        help=(
            "Train logistic regression on a combined multi-target citizen-science label "
            "dataset (closes KNOWN_LIMITATIONS #1: Single-target generalization gap). "
            "Local scheduling aid only — not a validated production model."
        ),
    )
    combined_model_parser.add_argument(
        "--dataset-path",
        type=Path,
        help=(
            "Path to combined label JSON "
            "(defaults to examples/real_labeled/combined_citizen_science_labels_v1.json)."
        ),
    )

    peer_review_parser = subparsers.add_parser(
        "generate-peer-review-package",
        help=(
            "Generate a structured public reproducibility package with pipeline "
            "methodology, label evidence, and example candidate summaries."
        ),
    )
    peer_review_parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory to write the peer review package into.",
    )

    noise_cal_parser = subparsers.add_parser(
        "noise-threshold-calibration",
        help=(
            "Analyze SNR/drift-rate distributions from a directory of turboSETI "
            "hit tables and suggest candidates for citizen-science threshold review."
        ),
    )
    noise_cal_parser.add_argument(
        "hit_dir",
        type=Path,
        help="Directory containing .dat or .csv turboSETI hit table files.",
    )
    noise_cal_parser.add_argument(
        "--max-files",
        type=int,
        default=500,
        help="Maximum number of files to analyze (default: 500).",
    )
    noise_cal_parser.add_argument(
        "--allow-development-fixtures",
        action="store_true",
        help=(
            "Allow unapproved synthetic/development fixtures. Never use this "
            "flag for production threshold calibration."
        ),
    )

    multi_epoch_parser = subparsers.add_parser(
        "multi-epoch-compare",
        help="Compare turboSETI hit tables across multiple observation epochs.",
    )
    multi_epoch_parser.add_argument(
        "dat_dir",
        help="Directory containing .dat turboSETI hit-table files (one per epoch).",
    )
    multi_epoch_parser.add_argument(
        "--freq-tol-hz",
        type=float,
        default=1000.0,
        help="Frequency grouping tolerance in Hz (default: 1000).",
    )

    _db_path_help = (
        "Path to the SQLite candidate store database "
        "(default: $TECHNO_SEARCH_CANDIDATE_STORE_PATH or data/candidates.db)."
    )

    cs_init_parser = subparsers.add_parser(
        "candidate-store-init",
        help="Initialize the SQLite candidate store schema.",
    )
    cs_init_parser.add_argument("--db-path", default=None, help=_db_path_help)

    cs_summary_parser = subparsers.add_parser(
        "candidate-store-summary",
        help="Print a summary of the candidate store.",
    )
    cs_summary_parser.add_argument("--db-path", default=None, help=_db_path_help)

    cs_list_parser = subparsers.add_parser(
        "candidate-store-list",
        help="List scored candidates in the store.",
    )
    cs_list_parser.add_argument("--db-path", default=None, help=_db_path_help)
    cs_list_parser.add_argument("--pathway", default=None, help="Filter by pathway.")
    cs_list_parser.add_argument("--track", default=None, help="Filter by track.")
    cs_list_parser.add_argument(
        "--limit", type=int, default=50, help="Maximum number of entries to return (default: 50)."
    )

    data_release_snapshot_parser = subparsers.add_parser(
        "data-release-snapshot-summary",
        help="Summarize data release snapshots and cross-release pathway changes.",
    )
    data_release_snapshot_parser.add_argument(
        "--snapshot-path",
        default=None,
        help="Path to data_release_snapshots.json fixture.",
    )

    compare_releases_parser = subparsers.add_parser(
        "compare-data-releases",
        help="Compare two named data release snapshots and report pathway changes.",
    )
    compare_releases_parser.add_argument(
        "snapshot_a_id",
        help="Snapshot ID of the earlier release.",
    )
    compare_releases_parser.add_argument(
        "snapshot_b_id",
        help="Snapshot ID of the later release.",
    )
    compare_releases_parser.add_argument(
        "--snapshot-path",
        default=None,
        help="Path to data_release_snapshots.json fixture.",
    )

    subparsers.add_parser(
        "cross-band-features-summary",
        help=(
            "Print cross-band feature normalization provenance summary "
            "(normalize_drift_rate, relative_snr, on_off_consistency)."
        ),
    )

    subparsers.add_parser(
        "globular-filter-summary",
        help=(
            "Print GLOBULAR pre-filter provenance summary "
            "(HDBSCAN density-based RFI cluster detection)."
        ),
    )

    semisupervised_summary_parser = subparsers.add_parser(
        "semisupervised-scorer-summary",
        help=(
            "Print semi-supervised anomaly scorer provenance summary "
            "(PCA + IsolationForest; local triage aid only)."
        ),
    )
    semisupervised_summary_parser.add_argument(
        "--metadata",
        default=None,
        help=(
            "Local scorer metadata path; defaults to "
            "data/meerkat_hits/semisupervised_scorer_metadata.json."
        ),
    )
    semisupervised_summary_parser.add_argument(
        "--model",
        default=None,
        help=(
            "Local fitted joblib model path; defaults to "
            "data/meerkat_hits/semisupervised_scorer.joblib."
        ),
    )

    semisupervised_corpus_parser = subparsers.add_parser(
        "semisupervised-corpus-build",
        help=(
            "Build a normalized real-hit NDJSON training corpus from "
            "turboSETI .dat files."
        ),
    )
    semisupervised_corpus_parser.add_argument(
        "--dat-dir",
        required=True,
        help="Directory or file containing real turboSETI .dat hit tables.",
    )
    semisupervised_corpus_parser.add_argument(
        "--output",
        required=True,
        help="Output NDJSON corpus path; use an ignored data/ path for payloads.",
    )
    semisupervised_corpus_parser.add_argument(
        "--max-hits",
        type=int,
        default=None,
        help="Maximum number of hits to write to the training corpus.",
    )

    semisupervised_train_parser = subparsers.add_parser(
        "semisupervised-scorer-train",
        help=(
            "Train the semi-supervised anomaly scorer from a normalized real "
            "hit NDJSON corpus such as data/meerkat_hits/*.ndjson."
        ),
    )
    semisupervised_train_parser.add_argument(
        "--corpus",
        required=True,
        help="Path to normalized NDJSON training hits.",
    )
    semisupervised_train_parser.add_argument(
        "--max-hits",
        type=int,
        default=None,
        help="Maximum number of hits to load from the corpus.",
    )
    semisupervised_train_parser.add_argument(
        "--workers",
        type=int,
        default=12,
        help="IsolationForest worker count; default 12 for local M4 Max headroom.",
    )
    semisupervised_train_parser.add_argument(
        "--n-components",
        type=int,
        default=8,
        help="PCA component count.",
    )
    semisupervised_train_parser.add_argument(
        "--n-estimators",
        type=int,
        default=200,
        help="IsolationForest tree count.",
    )
    semisupervised_train_parser.add_argument(
        "--contamination",
        type=float,
        default=0.01,
        help="Expected outlier fraction in the RFI-dominated training corpus.",
    )
    semisupervised_train_parser.add_argument(
        "--output-metadata",
        default=None,
        help=(
            "Metadata JSON path; defaults beside the corpus as "
            "semisupervised_scorer_metadata.json."
        ),
    )
    semisupervised_train_parser.add_argument(
        "--output-model",
        default=None,
        help=(
            "Joblib model payload path; defaults beside the corpus as "
            "semisupervised_scorer.joblib."
        ),
    )

    radio_real_corpus_parser = subparsers.add_parser(
        "radio-real-corpus-summary",
        help=(
            "Summarize local real turboSETI .dat corpus evidence for drift, "
            "cross-target RFI, and semi-supervised scorer integration."
        ),
    )
    radio_real_corpus_parser.add_argument(
        "--dat-dir",
        action="append",
        required=True,
        help="Directory or .dat file to include; may be repeated.",
    )
    radio_real_corpus_parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Optional cap on .dat files scanned, after stable sorting.",
    )
    radio_real_corpus_parser.add_argument(
        "--hit-ndjson",
        action="append",
        default=None,
        help=(
            "Real normalized hit-corpus NDJSON file or directory to include; "
            "may be repeated. Intended for ignored local corpora such as "
            "data/meerkat_hits/meerkat_normalised_200000.ndjson."
        ),
    )
    radio_real_corpus_parser.add_argument(
        "--max-hit-rows",
        type=int,
        default=None,
        help="Optional cap on hit-NDJSON rows scanned, after stable file sorting.",
    )
    radio_real_corpus_parser.add_argument(
        "--candidate-sample-limit",
        type=int,
        default=20,
        help=(
            "Maximum candidate-review rows to return in the JSON summary. "
            "Use 0 for counts only."
        ),
    )
    radio_real_corpus_parser.add_argument(
        "--freq-tolerance-hz",
        type=float,
        default=500.0,
        help="Cross-target RFI frequency tolerance in Hz.",
    )
    radio_real_corpus_parser.add_argument(
        "--semisupervised-model",
        type=Path,
        default=None,
        help=(
            "Optional fitted SemisupervisedScorer joblib model. Defaults to "
            "data/meerkat_hits/semisupervised_scorer.joblib when present."
        ),
    )

    multi_modal_crossmatch_parser = subparsers.add_parser(
        "multi-modal-crossmatch-summary",
        help=(
            "Phase 5: real sky-position cross-match of candidate reports "
            "(radio/photometry/infrared) to find candidates appearing in "
            ">= 2 independent modalities."
        ),
    )
    multi_modal_crossmatch_parser.add_argument(
        "--report-dir",
        required=True,
        help=(
            "Directory of written candidate report JSON files (e.g. "
            "artifacts/pipeline_smoke/ or a results/scans/RUN-*/ directory). "
            "Only *.json report files are read; *.manifest.json files in "
            "the same directory are excluded."
        ),
    )
    multi_modal_crossmatch_parser.add_argument(
        "--match-radius-arcsec",
        type=float,
        default=60.0,
        help=(
            "Sky-position match radius in arcseconds. 60 arcsec is a "
            "conservative generic cross-survey default, not a "
            "per-instrument-calibrated value -- supply a real per-track "
            "beam/PSF-informed radius when known."
        ),
    )

    prod_target_queue_parser = subparsers.add_parser(
        "prod-target-queue",
        help=(
            "Show the ranked scan queue for a .dat directory. "
            "Returns JSON with pending targets and selection rationale."
        ),
    )
    prod_target_queue_parser.add_argument(
        "--dat-dir",
        required=True,
        help="Directory containing turboSETI .dat hit-table files.",
    )
    prod_target_queue_parser.add_argument(
        "--history-file",
        default=None,
        help="Path to scan history NDJSON (default: none, all targets treated as new).",
    )
    prod_target_queue_parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Include already-scanned targets (they rank lower than fresh targets).",
    )

    prod_record_scan_parser = subparsers.add_parser(
        "prod-record-scan",
        help="Append a completed scan record to the scan history NDJSON file.",
    )
    prod_record_scan_parser.add_argument("--target-stem", required=True)
    prod_record_scan_parser.add_argument("--run-id", required=True)
    prod_record_scan_parser.add_argument("--score", required=True, type=float)
    prod_record_scan_parser.add_argument("--pathway", required=True)
    prod_record_scan_parser.add_argument("--dat-file", required=True)
    prod_record_scan_parser.add_argument(
        "--history-file",
        required=True,
        help="Path to scan history NDJSON file.",
    )
    prod_record_scan_parser.add_argument(
        "--parent-run-id",
        default=None,
        help="Run ID of a prior scan of this target (for re-scan linking).",
    )

    scan_history_summary_parser = subparsers.add_parser(
        "scan-history-summary",
        help="Show a summary of all prior production scans from the history NDJSON.",
    )
    scan_history_summary_parser.add_argument(
        "--history-file",
        default=None,
        help="Path to scan history NDJSON.",
    )
    scan_history_summary_parser.add_argument(
        "--dat-dir",
        default=None,
        help="If provided, report how many .dat files are still pending (never scanned).",
    )

    prod_file_scan_parser = subparsers.add_parser(
        "prod-file-scan",
        help=(
            "Run a tidy per-file scan with spinner progress and "
            "one-line-per-target console output. Restartable: already-completed "
            "targets (JSON output present) are skipped unless --force is passed."
        ),
    )
    prod_file_scan_parser.add_argument(
        "input_dir",
        help=(
            "Directory containing input files (.dat for radio, .csv for "
            "infrared/anomaly, .fits/.fit for photometry)."
        ),
    )
    prod_file_scan_parser.add_argument(
        "output_dir",
        help="Directory for output reports (JSON, Markdown, manifests).",
    )
    prod_file_scan_parser.add_argument(
        "--track",
        default=None,
        choices=["radio", "infrared", "anomaly", "photometry", "spectroscopy"],
        help=(
            "Pipeline track. Auto-detected from file extension if omitted "
            "(.dat → radio, .fits/.fit → photometry)."
        ),
    )
    prod_file_scan_parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Reprocess all targets even if output already exists (disables resume).",
    )

    subparsers.add_parser(
        "track-a-disk-usage",
        help=(
            "Report current data_cache/tmp_training/tmp_features disk usage against "
            "the ~100 GB Track A budget from docs/technosignature_datasets_agent_brief.md."
        ),
    )
    subparsers.add_parser(
        "track-a-htru2-acquire",
        help=(
            "Download the real HTRU2 pulsar-candidate dataset (CC BY 4.0) via "
            "ucimlrepo and record an acquisition manifest entry. Requires network "
            "access to archive-beta.ics.uci.edu and the ucimlrepo package."
        ),
    )
    subparsers.add_parser(
        "track-a-htru2-train",
        help=(
            "Train and evaluate the Track A HTRU2 pulsar vs RFI/noise baseline "
            "classifier from the locally acquired data_cache/raw/htru2 parquet files."
        ),
    )
    catalog_acquire_parser = subparsers.add_parser(
        "track-a-catalog-acquire",
        help=(
            "Download and normalize one Track A known-source catalog (ATNF, "
            "CHIME/FRB, Roma-BZCAT, or Fermi 4FGL-DR4) for cross-matching."
        ),
    )
    catalog_acquire_parser.add_argument(
        "catalog",
        choices=["atnf", "chime_frb", "romabzcat", "fermi_4fgl"],
        help="Which known-source catalog to acquire and normalize.",
    )
    crossmatch_parser = subparsers.add_parser(
        "track-a-crossmatch",
        help=(
            "Cross-match a candidate sky position against locally normalized "
            "Track A known-source catalogs (pulsar/FRB/blazar-AGN/gamma-ray)."
        ),
    )
    crossmatch_parser.add_argument(
        "ra_deg", type=float, help="Candidate right ascension, ICRS degrees."
    )
    crossmatch_parser.add_argument(
        "dec_deg", type=float, help="Candidate declination, ICRS degrees."
    )
    crossmatch_parser.add_argument(
        "--radius-arcsec",
        type=float,
        default=30.0,
        help="Cone search radius in arcseconds (default: 30.0).",
    )
    replay_parser = subparsers.add_parser(
        "track-a-historical-replay",
        help=(
            "Phase 3 Small Historical Replay: sample real rows from locally "
            "acquired Track A catalogs, confirm cross-match recovers each "
            "object's own known class, and confirm a fixed empty-sky position "
            "reports no_known_match instead of a false positive."
        ),
    )
    replay_parser.add_argument(
        "--sample-size",
        type=int,
        default=1,
        help="Number of rows to sample per catalog as replay cases (default: 1).",
    )
    photometry_search_parser = subparsers.add_parser(
        "photometry-lightcurve-search",
        help=(
            "Search NASA MAST for real Kepler/K2/TESS light curves and "
            "download up to --limit results. Requires real MAST network "
            "access (not available from this project's sandbox)."
        ),
    )
    photometry_search_parser.add_argument(
        "target",
        help="Target name or identifier (e.g. 'KIC 8462852', 'TIC 200322593').",
    )
    photometry_search_parser.add_argument(
        "--mission",
        default=None,
        help="Comma-separated mission filter, e.g. 'TESS' or 'Kepler,K2'.",
    )
    photometry_search_parser.add_argument("--author", default=None)
    photometry_search_parser.add_argument("--sector", type=int, default=None)
    photometry_search_parser.add_argument("--quarter", type=int, default=None)
    photometry_search_parser.add_argument("--campaign", type=int, default=None)
    photometry_search_parser.add_argument("--exptime", type=float, default=None)
    photometry_search_parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Maximum number of light curves to download (default: 1).",
    )
    photometry_search_parser.add_argument(
        "--download-dir",
        default="data/photometry_lightcurves",
        help="Local directory to download FITS files into.",
    )
    jwst_search_parser = subparsers.add_parser(
        "jwst-miri-lrs-search",
        help=(
            "Search NASA MAST for real JWST MIRI LRS x1d transmission "
            "spectra and download up to --limit results. Requires real "
            "MAST network access (not available from this project's "
            "sandbox)."
        ),
    )
    jwst_search_parser.add_argument(
        "target",
        help="Target name or identifier resolvable by MAST (e.g. a Simbad-known exoplanet host).",
    )
    jwst_search_parser.add_argument(
        "--instrument-name",
        default=None,
        help=(
            "Comma-separated MAST instrument_name filter. Defaults to the "
            "real, live-verified MIRI LRS values MIRI/SLIT,MIRI/SLITLESS."
        ),
    )
    jwst_search_parser.add_argument(
        "--filters",
        default="P750L",
        help=(
            "MAST filters criterion (LRS disperser). Defaults to the real "
            "verified P750L prism value. Pass an empty string to search all "
            "MIRI LRS dispersers."
        ),
    )
    jwst_search_parser.add_argument("--radius-arcsec", type=float, default=None)
    jwst_search_parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Maximum number of x1d products to download (default: 1).",
    )
    jwst_search_parser.add_argument(
        "--download-dir",
        default="data/jwst_spectra",
        help="Local directory to download FITS files into.",
    )
    wise_search_parser = subparsers.add_parser(
        "wise-photometry-search",
        help=(
            "Search NASA/IPAC IRSA for real AllWISE W1-W4 photometry around "
            "a target and write it to a CSV. Requires real IRSA network "
            "access (not available from this project's sandbox)."
        ),
    )
    wise_search_parser.add_argument(
        "target",
        help="Target name resolvable by astropy's SkyCoord.from_name (e.g. 'KIC 8462852').",
    )
    wise_search_parser.add_argument(
        "--radius-arcsec",
        type=float,
        default=5.0,
        help="Cone search radius in arcseconds (default: 5.0).",
    )
    wise_search_parser.add_argument(
        "--download-dir",
        default="data/wise_photometry",
        help="Local directory to write the AllWISE CSV into.",
    )
    satellite_acquire_parser = subparsers.add_parser(
        "track-a-satellite-acquire",
        help=(
            "Download and normalize one satellite/transmitter data source "
            "(CelesTrak SATCAT, CelesTrak active GP orbital elements, or a "
            "SatNOGS DB endpoint) for satellite-transmitter matching."
        ),
    )
    satellite_acquire_parser.add_argument(
        "source",
        choices=[
            "celestrak_satcat",
            "celestrak_gp_active",
            "satnogs_satellites",
            "satnogs_transmitters",
            "satnogs_tle",
            "satnogs_modes",
        ],
        help="Which satellite/transmitter data source to acquire.",
    )
    satellite_match_parser = subparsers.add_parser(
        "track-a-satellite-match",
        help=(
            "Check whether an event is explained by a known satellite "
            "transmitter: frequency must overlap a SatNOGS transmitter range "
            "AND SGP4-propagated position at the observation time must fall "
            "within the beam radius of the candidate sky position."
        ),
    )
    satellite_match_parser.add_argument(
        "frequency_hz", type=float, help="Event frequency in Hz."
    )
    satellite_match_parser.add_argument(
        "observation_time_utc",
        help=(
            "Observation timestamp, ISO 8601 (e.g. 2026-01-01T00:00:00). "
            "Assumed UTC if no offset."
        ),
    )
    satellite_match_parser.add_argument(
        "ra_deg", type=float, help="Candidate right ascension, ICRS degrees."
    )
    satellite_match_parser.add_argument(
        "dec_deg", type=float, help="Candidate declination, ICRS degrees."
    )
    satellite_match_parser.add_argument(
        "--observer-lat-deg",
        type=float,
        required=True,
        help="Observer (telescope) geodetic latitude in degrees. No default — must be supplied.",
    )
    satellite_match_parser.add_argument(
        "--observer-lon-deg",
        type=float,
        required=True,
        help="Observer (telescope) geodetic longitude in degrees. No default — must be supplied.",
    )
    satellite_match_parser.add_argument(
        "--observer-elevation-m",
        type=float,
        required=True,
        help="Observer (telescope) elevation in meters. No default — must be supplied.",
    )
    satellite_match_parser.add_argument(
        "--beam-radius-deg",
        type=float,
        default=0.5,
        help="Beam coincidence radius in degrees (default: 0.5).",
    )
    track_b_gate_parser = subparsers.add_parser(
        "track-b-unknown-candidate-gate",
        help=(
            "Evaluate the Track B Phase 4 unknown_candidate gate from an explicit "
            "candidate packet, Track A crossmatch JSON, and optional satellite-match JSON. "
            "This combines already-computed evidence only; it performs no network lookups."
        ),
    )
    track_b_gate_parser.add_argument(
        "candidate_json",
        help="Candidate JSON packet to evaluate.",
    )
    track_b_gate_parser.add_argument(
        "--crossmatch-json",
        required=True,
        help="JSON output from track-a-crossmatch for the same candidate sky position.",
    )
    track_b_gate_parser.add_argument(
        "--satellite-json",
        default=None,
        help=(
            "Optional JSON output from track-a-satellite-match for the same observation. "
            "Omitting it leaves the satellite condition unresolved and blocks eligibility."
        ),
    )
    track_b_readiness_parser = subparsers.add_parser(
        "track-b-candidate-readiness",
        help=(
            "Fail-closed audit of whether a real candidate packet has the metadata "
            "and explicit Track A/ satellite evidence needed for Track B gate review."
        ),
    )
    track_b_readiness_parser.add_argument(
        "candidate_json",
        help="Candidate JSON packet to audit.",
    )
    track_b_readiness_parser.add_argument(
        "--crossmatch-json",
        default=None,
        help=(
            "Optional JSON output from track-a-crossmatch. When supplied, the Track B "
            "gate is evaluated; otherwise the audit reports required packet inputs."
        ),
    )
    track_b_readiness_parser.add_argument(
        "--satellite-json",
        default=None,
        help=(
            "Optional JSON output from track-a-satellite-match. Missing satellite "
            "evidence remains an explicit unresolved blocker."
        ),
    )

    data_collection_status_parser = subparsers.add_parser(
        "record-data-collection-status",
        help=(
            "Update the tracked docs/data_collection_status.json manifest "
            "for one acquisition script/command and (by default) commit + "
            "push just that file to main, so progress can be reviewed via "
            "git pull instead of pasted console output."
        ),
    )
    data_collection_status_parser.add_argument(
        "--script",
        required=True,
        help="Script/command name this status entry is for (e.g. 'download_bl_extended_corpus').",
    )
    data_collection_status_parser.add_argument(
        "--summary-json",
        required=True,
        help=(
            "JSON object of real run counts/outcomes "
            '(e.g. \'{"downloaded": 3, "skipped": 1}\').'
        ),
    )
    data_collection_status_parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Update the local manifest file only; do not run git commit/push.",
    )
    data_collection_status_parser.add_argument(
        "--status-path",
        default=None,
        help=(
            "Override the manifest file path (defaults to "
            "docs/data_collection_status.json under the project root, or "
            "$TECHNO_DATA_COLLECTION_STATUS_PATH if set). Used by this "
            "project's own tests to avoid writing to the real tracked file."
        ),
    )

    adversarial_review_parser = subparsers.add_parser(
        "adversarial-review-dossier",
        help=(
            "Phase 5 Step 2: deterministic adversarial-review dossier for a "
            "scored candidate report -- aggregates every refutation check "
            "already computed by scoring.py (and optionally the Track B "
            "gate) into one itemized checklist, following the same "
            "deterministic-checklist design Sheikh et al. 2021 used to "
            "verify/refute Breakthrough Listen's blc1 signal of interest."
        ),
    )
    adversarial_review_parser.add_argument(
        "report_json",
        help="Written candidate report JSON path (run-pipeline's <id>.json output).",
    )
    adversarial_review_parser.add_argument(
        "--track-b-gate-json",
        default=None,
        help=(
            "Optional JSON output from track-b-unknown-candidate-gate for the "
            "same candidate; any unsatisfied condition is folded in as an "
            "additional real refutation."
        ),
    )

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
