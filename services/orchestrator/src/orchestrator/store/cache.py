import os
from functools import lru_cache
from uuid import UUID

import redis

EXERCISE_TEST_TTL_SECONDS = 60 * 60  # 1 hour scratch — never the source of truth


@lru_cache
def _client() -> redis.Redis:
    url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    return redis.Redis.from_url(url, decode_responses=True)


def _exercise_test_key(session_id: UUID, concept_id: UUID) -> str:
    return f"session:{session_id}:concept:{concept_id}:exercise_test_code"


def set_pending_exercise_test_code(session_id: UUID, concept_id: UUID, test_code: str) -> None:
    _client().set(_exercise_test_key(session_id, concept_id), test_code, ex=EXERCISE_TEST_TTL_SECONDS)


def get_pending_exercise_test_code(session_id: UUID, concept_id: UUID) -> str | None:
    return _client().get(_exercise_test_key(session_id, concept_id))
