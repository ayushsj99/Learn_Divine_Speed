def due_for_reinforcement(mastery_entry: dict) -> bool:
    """Stub no-op for v1: scheduling interleaved review questions needs a
    multi-session/multi-day notion of 'due' that the current single-session
    v1 slice doesn't model yet. `last_reinforced_at` is already tracked on
    mastery_entries as the hook for this."""
    return False
