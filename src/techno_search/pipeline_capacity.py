"""Pipeline capacity module — aggregate scheduling load dashboard."""

from __future__ import annotations

from typing import Any

PIPELINE_CAPACITY_DISCLAIMER = (
    "Pipeline capacity summaries are local operational scheduling dashboards only. "
    "Capacity status reflects current workflow load against scheduling resources — "
    "it does not reflect candidate scientific priority and does not constitute "
    "evidence of a technosignature. 'overloaded' status means the scheduling queue "
    "is deep relative to operator capacity, not that any discovery is imminent."
)


def pipeline_capacity_summary() -> dict[str, Any]:
    from techno_search.candidate_annotation import candidate_annotation_summary
    from techno_search.candidate_priority_queue import priority_queue_summary
    from techno_search.follow_up_request import follow_up_request_summary
    from techno_search.operator_assignment import operator_assignment_summary

    assignments = operator_assignment_summary()
    requests = follow_up_request_summary()
    annotations = candidate_annotation_summary()
    queue = priority_queue_summary()

    open_assignments = int(assignments.get("pending_count", 0))
    open_requests = int(requests.get("open_count", 0))
    unresolved_annotations = int(annotations.get("unresolved_count", 0))
    queue_depth = int(queue.get("queue_depth", 0))

    total_load = open_assignments + open_requests + queue_depth

    if total_load >= 10 or unresolved_annotations >= 5:
        capacity_status = "overloaded"
    elif total_load >= 5 or unresolved_annotations >= 3:
        capacity_status = "strained"
    else:
        capacity_status = "nominal"

    return {
        "disclaimer": PIPELINE_CAPACITY_DISCLAIMER,
        "open_assignment_count": open_assignments,
        "open_request_count": open_requests,
        "unresolved_annotation_count": unresolved_annotations,
        "queue_depth": queue_depth,
        "total_scheduling_load": total_load,
        "capacity_status": capacity_status,
    }
