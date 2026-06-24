from uuid import UUID

from orchestrator.store import repository


def resolve_startable_concept(concept: dict) -> dict:
    """If `concept` has an incomplete prerequisite, detour to the first
    incomplete prereq instead — recursively, so a chain of prereqs is walked
    to its earliest incomplete link before any lesson content is generated."""
    for prereq_id in concept.get("prereq_concept_ids") or []:
        prereq = repository.get_concept(prereq_id)
        if prereq and prereq["status"] != "completed":
            return resolve_startable_concept(prereq)
    return concept
