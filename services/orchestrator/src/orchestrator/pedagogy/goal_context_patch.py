def patch_goal_context(existing: dict | None, new_detail: str) -> dict:
    """Stub no-op for v1: appends new context rather than re-deriving syllabus
    node depth/examples from it. Wiring this into an actual remaining-syllabus
    JSON patch is deferred — the gateway contract for mid-session context
    edits doesn't exist yet either."""
    existing = dict(existing or {})
    notes = existing.get("notes", [])
    notes.append(new_detail)
    existing["notes"] = notes
    return existing
