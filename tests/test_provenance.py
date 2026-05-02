from techno_search import Candidate, Track
from techno_search.provenance import (
    build_cache_key,
    build_provenance_record,
    candidate_provenance_record,
)


def test_build_provenance_record_preserves_versions_and_query_parameters() -> None:
    record = build_provenance_record(
        input_path="candidate.json",
        provider_name="gaia",
        service_url="https://example.test/gaia",
        query_parameters={"radius_arcsec": "5", "target": "synthetic"},
        cache_key="cache-123",
        source_ids=("source-a",),
        source_dataset="synthetic",
    )

    data = record.as_dict()

    assert data["schema_version"] == "techno_search_packet_v1"
    assert data["config_version"] == "scoring_v0"
    assert data["provider_name"] == "gaia"
    assert data["service_url"] == "https://example.test/gaia"
    assert data["query_parameters"] == {"radius_arcsec": "5", "target": "synthetic"}
    assert data["cache_key"] == "cache-123"
    assert data["source_ids"] == ["source-a"]
    assert data["source_dataset"] == "synthetic"
    assert data["generated_at_utc"]


def test_candidate_provenance_record_uses_candidate_metadata() -> None:
    candidate = Candidate(
        candidate_id="prov-candidate",
        track=Track.RADIO,
        source_ids=("source-a", "source-b"),
        provenance={"source_dataset": "synthetic", "config_version": "custom_config"},
        features={},
    )

    record = candidate_provenance_record(candidate, input_path="candidate.json")
    data = record.as_dict()

    assert data["input_path"] == "candidate.json"
    assert data["source_ids"] == ["source-a", "source-b"]
    assert data["source_dataset"] == "synthetic"
    assert data["config_version"] == "custom_config"


def test_build_cache_key_is_deterministic_for_sorted_parameters() -> None:
    first = build_cache_key(
        provider_name="gaia",
        query="synthetic target",
        purpose="unit-test",
        parameters={"b": "2", "a": "1"},
    )
    second = build_cache_key(
        provider_name="gaia",
        query="synthetic target",
        purpose="unit-test",
        parameters={"a": "1", "b": "2"},
    )

    assert first == second
    assert len(first) == 64
