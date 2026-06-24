STEP_DOWN_THRESHOLD = 2


def should_step_down(attempts: int) -> bool:
    """After 2+ failed attempts on the independent exercise, the next
    response should fall back toward guided-practice-level difficulty rather
    than repeating the same independent-level prompt."""
    return attempts >= STEP_DOWN_THRESHOLD
