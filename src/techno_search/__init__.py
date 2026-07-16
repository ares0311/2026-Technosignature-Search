"""Technosignature-interest candidate search tools."""

__version__ = "1.2.17"

from techno_search.ai_hardening_gate import (
    AI_HARDENING_GATE_DISCLAIMER,
    AI_HARDENING_GATE_SCHEMA_VERSION,
    ai_hardening_gate_summary,
    load_ai_hardening_gate,
)
from techno_search.artifact_cleanup import (
    ARTIFACT_CLEANUP_DISCLAIMER,
    ARTIFACT_CLEANUP_SCHEMA_VERSION,
    apply_artifact_cleanup,
    plan_artifact_cleanup,
)
from techno_search.background_search import (
    BACKGROUND_FOLLOW_UP_TEST_DISCLAIMER,
    BACKGROUND_FOLLOW_UP_TEST_SCHEMA_VERSION,
    BACKGROUND_NEEDS_FOLLOW_UP_DISCLAIMER,
    BACKGROUND_NEEDS_FOLLOW_UP_SCHEMA_VERSION,
    BACKGROUND_PRIORITY_CONFIG_VERSION,
    BACKGROUND_REPORT_READINESS_DISCLAIMER,
    BACKGROUND_REPORT_READINESS_SCHEMA_VERSION,
    BACKGROUND_REVIEWED_LOG_DISCLAIMER,
    BACKGROUND_REVIEWED_LOG_SCHEMA_VERSION,
    BACKGROUND_SEARCH_LEDGER_DISCLAIMER,
    BACKGROUND_SEARCH_LEDGER_SCHEMA_VERSION,
    CANDIDATE_EXTRACTION_HANDOFF_DISCLAIMER,
    CANDIDATE_EXTRACTION_HANDOFF_SCHEMA_VERSION,
    DEFAULT_PRIORITY_WEIGHTS,
    LOCAL_BACKGROUND_EXECUTION_MODE,
    LOCAL_BACKGROUND_REVIEW_STATUS,
    TARGET_PRIORITY_DISCLAIMER,
    TARGET_PRIORITY_SCHEMA_VERSION,
    BackgroundFollowUpTestResult,
    BackgroundNeedsFollowUpEntry,
    BackgroundPriorityConfig,
    BackgroundReportReadinessRecord,
    BackgroundReviewedLogEntry,
    BackgroundSearchLedgerEntry,
    BackgroundTarget,
    CandidateExtractionHandoffRecord,
    append_background_needs_follow_up_entry,
    append_background_reviewed_log_entry,
    append_background_search_ledger_entry,
    background_follow_up_test_summary,
    background_needs_follow_up_summary,
    background_report_readiness_summary,
    background_review_workflow_summary,
    background_reviewed_log_summary,
    background_search_ledger_summary,
    candidate_extraction_handoff_summary,
    load_background_follow_up_tests,
    load_background_needs_follow_up_log,
    load_background_priority_config,
    load_background_report_readiness,
    load_background_reviewed_log,
    load_background_search_ledger,
    load_background_targets,
    load_candidate_extraction_handoffs,
    run_local_background_search_once,
    target_priority_score,
    target_priority_summary,
    target_selection_score,
)
from techno_search.baseline_eval import (
    BASELINE_EVAL_DISCLAIMER,
    BASELINE_PERFORMANCE_HISTORY_SCHEMA_VERSION,
    baseline_pathway_drift_summary,
    baseline_performance_history_summary,
    classifier_rule_coverage_summary,
    evaluate_baseline,
    route_coverage_summary,
    score_determinism_check,
)
from techno_search.baseline_model import (
    ALL_BASELINE_RULES,
    BASELINE_MODEL_DISCLAIMER,
    BASELINE_MODEL_VERSION,
    RuleBasedBaselineClassifier,
    predict_pathway,
)
from techno_search.calibration import (
    CALIBRATION_TRACK_DISCLAIMER,
    CALIBRATION_TRACK_SCHEMA_VERSION,
    FALSE_POSITIVE_ANALYSIS_DISCLAIMER,
    calibration_track_summary,
    false_positive_class_summary,
    load_calibration_fixtures,
)
from techno_search.candidate_annotation import (
    ALLOWED_ANNOTATION_TYPES,
    CANDIDATE_ANNOTATION_DISCLAIMER,
    CANDIDATE_ANNOTATION_SCHEMA_VERSION,
    CandidateAnnotation,
    candidate_annotation_summary,
    load_candidate_annotations,
)
from techno_search.candidate_audit_trail import (
    CANDIDATE_AUDIT_TRAIL_DISCLAIMER,
    CANDIDATE_AUDIT_TRAIL_SCHEMA_VERSION,
    CandidateAuditAction,
    audit_trail_summary,
    load_audit_trail,
)
from techno_search.candidate_feature_vector import (
    ALLOWED_NORMALIZATION_KINDS,
    CANDIDATE_FEATURE_VECTOR_DISCLAIMER,
    CANDIDATE_FEATURE_VECTOR_SCHEMA_VERSION,
    CandidateFeatureVector,
    feature_vector_summary,
    load_feature_vectors,
)
from techno_search.candidate_methods_summary import (
    CANDIDATE_METHODS_DISCLAIMER,
    candidate_methods_summary,
)
from techno_search.candidate_observation_notes import (
    ALLOWED_OBSERVATION_OUTCOMES,
    CANDIDATE_OBSERVATION_NOTES_DISCLAIMER,
    CANDIDATE_OBSERVATION_NOTES_SCHEMA_VERSION,
    CandidateObservationNote,
    load_observation_notes,
    observation_notes_summary,
)
from techno_search.candidate_priority_queue import (
    ALLOWED_QUEUE_REASONS,
    CANDIDATE_PRIORITY_QUEUE_DISCLAIMER,
    CANDIDATE_PRIORITY_QUEUE_SCHEMA_VERSION,
    CandidatePriorityQueueEntry,
    load_priority_queue_entries,
    priority_queue_summary,
)
from techno_search.candidate_resolution import (
    ALLOWED_RESOLUTION_STATUSES,
    CANDIDATE_RESOLUTION_DISCLAIMER,
    CANDIDATE_RESOLUTION_SCHEMA_VERSION,
    CandidateResolutionRecord,
    candidate_resolution_summary,
    load_resolution_records,
)
from techno_search.candidate_retention import (
    ALLOWED_RETENTION_STATUSES,
    CANDIDATE_RETENTION_DISCLAIMER,
    CANDIDATE_RETENTION_SCHEMA_VERSION,
    CandidateRetentionRecord,
    candidate_retention_summary,
    load_retention_records,
)
from techno_search.config import TrackConfig, load_scoring_config, load_track_config
from techno_search.cross_track import (
    CROSS_TRACK_REFERENCE_DISCLAIMER,
    CROSS_TRACK_REFERENCE_SCHEMA_VERSION,
    CrossTrackReference,
    cross_track_summary,
    load_cross_track_references,
)
from techno_search.curated_dataset_admission import (
    ALLOWED_CURATED_DATASET_ADMISSION_STATUSES,
    CURATED_DATASET_ADMISSION_DISCLAIMER,
    CURATED_DATASET_ADMISSION_SCHEMA_VERSION,
    CuratedDatasetAdmissionRecord,
    curated_dataset_admission_summary,
    load_curated_dataset_admission_records,
    validate_curated_dataset_admission_records,
)
from techno_search.curated_dataset_intake import (
    ALLOWED_DATA_KINDS,
    ALLOWED_INTAKE_STATUSES,
    CURATED_DATASET_INTAKE_DISCLAIMER,
    CURATED_DATASET_INTAKE_SCHEMA_VERSION,
    CuratedDatasetIntakeRecord,
    curated_dataset_intake_summary,
    load_intake_records,
)
from techno_search.feature_importance import (
    FEATURE_IMPORTANCE_DISCLAIMER,
    FEATURE_IMPORTANCE_SCHEMA_VERSION,
    FeatureImportanceEntry,
    feature_importance_summary,
    load_feature_importance_entries,
)
from techno_search.feature_normalization import (
    FEATURE_NORMALIZATION_DISCLAIMER,
    FEATURE_NORMALIZATION_SCHEMA_VERSION,
    FeatureNormalizationBounds,
    feature_normalization_summary,
    load_normalization_bounds,
)
from techno_search.follow_up_request import (
    ALLOWED_REQUEST_PRIORITIES,
    ALLOWED_REQUEST_STATUSES,
    FOLLOW_UP_REQUEST_DISCLAIMER,
    FOLLOW_UP_REQUEST_SCHEMA_VERSION,
    FollowUpRequest,
    follow_up_request_summary,
    load_follow_up_requests,
)
from techno_search.injection_recovery import (
    INJECTION_RECOVERY_DISCLAIMER,
    false_negative_summary,
    injection_recovery_summary,
    load_injection_recovery_cases,
)
from techno_search.live_data import live_data_enabled, require_live_data_enabled
from techno_search.model_architecture import (
    ALLOWED_ARCHITECTURE_KINDS,
    ALLOWED_ARCHITECTURE_STATUSES,
    MODEL_ARCHITECTURE_DISCLAIMER,
    MODEL_ARCHITECTURE_SCHEMA_VERSION,
    ModelArchitectureEntry,
    load_architecture_entries,
    model_architecture_summary,
)
from techno_search.model_evaluation import (
    MODEL_EVALUATION_DISCLAIMER,
    MODEL_EVALUATION_SCHEMA_VERSION,
    ModelEvaluationResult,
    load_model_evaluation_results,
    model_evaluation_summary,
)
from techno_search.multi_epoch_summary import (
    MULTI_EPOCH_DISCLAIMER,
    MULTI_EPOCH_SCHEMA_VERSION,
    MultiEpochRecord,
    load_multi_epoch_records,
    multi_epoch_summary,
)
from techno_search.observation_campaign import (
    ALLOWED_CAMPAIGN_STATUSES,
    OBSERVATION_CAMPAIGN_DISCLAIMER,
    OBSERVATION_CAMPAIGN_SCHEMA_VERSION,
    ObservationCampaign,
    load_observation_campaigns,
    observation_campaign_summary,
)
from techno_search.pathway import classify_pathway
from techno_search.pipeline_audit_summary import (
    PIPELINE_AUDIT_DISCLAIMER,
    pipeline_audit_summary,
)
from techno_search.pipeline_config import (
    ALLOWED_PIPELINE_STATUSES,
    PIPELINE_CONFIG_DISCLAIMER,
    PIPELINE_CONFIG_SCHEMA_VERSION,
    PipelineConfigRecord,
    load_pipeline_configs,
    pipeline_config_summary,
)
from techno_search.plotting import (
    PLOT_ARTIFACT_DISCLAIMER,
    PlotArtifact,
    plot_artifact_summary,
    write_synthetic_plot_artifacts,
)
from techno_search.radio_corpus_cleanup import (
    RADIO_CORPUS_CLEANUP_DISCLAIMER,
    RADIO_CORPUS_CLEANUP_SCHEMA_VERSION,
    apply_radio_corpus_cleanup,
    plan_radio_corpus_cleanup,
)
from techno_search.real_data_admission_preflight import (
    REAL_DATA_ADMISSION_PREFLIGHT_DISCLAIMER,
    REAL_DATA_ADMISSION_PREFLIGHT_SCHEMA_VERSION,
    RealDataAdmissionPreflightCategory,
    load_real_data_admission_preflight_categories,
    load_real_data_admission_preflight_expectations,
    real_data_admission_preflight_summary,
    validate_real_data_admission_preflight_categories,
)
from techno_search.reporting import (
    REQUIRED_DISCLAIMER,
    ReportPaths,
    candidate_markdown_report,
    candidate_packet,
    candidate_packet_json,
    report_manifest,
    report_manifest_json,
    write_candidate_reports,
)
from techno_search.reproducibility import (
    REPRODUCIBILITY_VERIFICATION_DISCLAIMER,
    REPRODUCIBILITY_VERIFICATION_SCHEMA_VERSION,
    verify_packet_against_manifest,
    verify_report_directory,
)
from techno_search.schemas import Candidate, Pathway, ScoredCandidate, Track
from techno_search.scoring import score_candidate
from techno_search.signal_registry import (
    SIGNAL_REGISTRY_DISCLAIMER,
    SIGNAL_REGISTRY_SCHEMA_VERSION,
    SignalOfInterest,
    load_signal_registry,
    signal_registry_summary,
    signal_registry_track_summary,
)
from techno_search.submission_readiness import (
    ALLOWED_READINESS_STATUSES,
    REQUIRED_PROVENANCE_FIELDS,
    SUBMISSION_READINESS_DISCLAIMER,
    SUBMISSION_READINESS_SCHEMA_VERSION,
    SubmissionReadinessRecord,
    load_submission_readiness_records,
    submission_readiness_summary,
)
from techno_search.target_recalibration_summary import (
    TARGET_RECALIBRATION_DISCLAIMER,
    TARGET_RECALIBRATION_SCHEMA_VERSION,
    TargetPrioritySnapshot,
    load_priority_snapshots,
    target_recalibration_summary,
)
from techno_search.validation_datasets import (
    VALIDATION_DATASET_DISCLAIMER,
    VALIDATION_DATASET_SCHEMA_VERSION,
    VALIDATION_PROMOTION_DISCLAIMER,
    VALIDATION_PROMOTION_SCHEMA_VERSION,
    VALIDATION_READINESS_DISCLAIMER,
    VALIDATION_READINESS_SCHEMA_VERSION,
    ValidationDatasetEntry,
    ValidationPromotionRule,
    ValidationReadinessRecord,
    load_validation_dataset_entries,
    load_validation_promotion_rules,
    load_validation_readiness_records,
    validation_dataset_summary,
    validation_promotion_summary,
    validation_readiness_summary,
)
