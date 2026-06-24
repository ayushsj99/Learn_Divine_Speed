def should_skip_remaining_drill(passed_on_first_attempt: bool) -> bool:
    """Stub no-op for v1: there is currently only one exercise per concept, so
    there is no further drill to skip. Real once multi-exercise-per-concept
    drilling is added."""
    return False
