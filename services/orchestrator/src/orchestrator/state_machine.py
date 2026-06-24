import json
import logging
from uuid import UUID

from orchestrator.clients import llm_router_client, retrieval_client, sandbox_client
from orchestrator.pedagogy.difficulty_step_down import should_step_down
from orchestrator.pedagogy.prereq_detour import resolve_startable_concept
from orchestrator.store import cache, repository

logger = logging.getLogger("orchestrator.state_machine")

DIAGNOSTIC_QUESTION_COUNT = 4


async def start_session(framework: str, goal: str, goal_context: dict | None) -> dict:
    user_id = repository.get_or_create_demo_user()
    session = repository.create_session(user_id, framework, goal, goal_context)
    session = repository.update_session(session["id"], phase="diagnostic")
    return session


async def get_session(session_id: UUID) -> dict | None:
    return repository.get_session(session_id)


def _level_from_ratio(correct: int, total: int) -> str:
    if total == 0:
        return "beginner"
    ratio = correct / total
    if ratio >= 0.8:
        return "advanced"
    if ratio >= 0.4:
        return "intermediate"
    return "beginner"


async def handle_diagnostic(session_id: UUID, answer: str | None) -> dict:
    session = repository.get_session(session_id)
    if session is None:
        raise ValueError("session not found")

    pending = repository.get_pending_diagnostic_question(session_id)

    if pending is not None and answer is not None:
        grading_prompt = (
            f"Question: {pending['question_text']}\nLearner answer: {answer}\n"
            f"Is this answer correct? Respond with JSON: {{\"correct\": true|false}}."
        )
        try:
            graded = await llm_router_client.generate_json("diagnostic_grading_check", grading_prompt)
            correct = bool(graded.get("correct", False))
        except (json.JSONDecodeError, KeyError):
            correct = False
        repository.answer_diagnostic_question(pending["id"], answer, correct)

    answered_count, correct_count = repository.count_answered_diagnostics(session_id)

    if answered_count >= DIAGNOSTIC_QUESTION_COUNT:
        level = _level_from_ratio(correct_count, answered_count)
        repository.update_session(session_id, level=level, phase="syllabus_building")
        await build_syllabus(session_id)
        return {"level_assigned": level}

    question_prompt = (
        f"Generate diagnostic question #{answered_count + 1} of {DIAGNOSTIC_QUESTION_COUNT} "
        f"to assess a learner's real skill level in '{session['framework']}'. "
        f"Their stated goal is '{session['goal']}'. "
        f"Ask a short, concrete question (concept check or predict-the-output snippet), "
        f"plain text only, no preamble."
    )
    question_text = await llm_router_client.generate_text("diagnostic_question_gen", question_prompt)
    repository.insert_diagnostic_question(session_id, question_text)
    return {"next_question": question_text}


async def build_syllabus(session_id: UUID) -> dict:
    session = repository.get_session(session_id)
    syllabus_prompt = (
        f"Build a syllabus for learning '{session['framework']}'. "
        f"Learner goal: {session['goal']}. Goal context: {session.get('goal_context')}. "
        f"Learner level: {session['level']}. "
        f"Respond with JSON: {{\"concepts\": [{{\"name\": str, \"description\": str, "
        f"\"difficulty\": \"beginner|intermediate|advanced\", \"prereq_names\": [str]}}]}}. "
        f"Order concepts so prerequisites come before what depends on them. 5-8 concepts."
    )
    result = await llm_router_client.generate_json("syllabus_builder", syllabus_prompt)
    concepts_spec = result.get("concepts", [])

    syllabus = repository.create_syllabus(session_id, session["framework"])

    name_to_id: dict[str, UUID] = {}
    inserted: list[dict] = []
    for ordinal, spec in enumerate(concepts_spec):
        row = repository.add_syllabus_concept(
            syllabus["id"], ordinal, spec["name"], spec.get("description", ""),
            spec.get("difficulty", "beginner"), prereq_concept_ids=[],
        )
        name_to_id[spec["name"]] = row["id"]
        inserted.append((row["id"], spec.get("prereq_names", [])))

    # Second pass: resolve prereq names to ids now that every concept has an id.
    with repository.get_conn() as conn, conn.cursor() as cur:
        for concept_id, prereq_names in inserted:
            prereq_ids = [name_to_id[n] for n in prereq_names if n in name_to_id]
            if prereq_ids:
                cur.execute(
                    "UPDATE syllabus_concepts SET prereq_concept_ids = %s WHERE id = %s",
                    (prereq_ids, concept_id),
                )

    first_concept = repository.next_pending_concept(syllabus["id"])
    repository.update_session(
        session_id, syllabus_id=syllabus["id"],
        current_concept_id=first_concept["id"] if first_concept else None,
        phase="lesson_worked_example",
    )
    return repository.get_syllabus_with_concepts(syllabus["id"])


async def get_syllabus(session_id: UUID) -> dict | None:
    session = repository.get_session(session_id)
    if session is None or session["syllabus_id"] is None:
        return None
    return repository.get_syllabus_with_concepts(session["syllabus_id"])


async def start_lesson(session_id: UUID, concept_id: UUID) -> dict:
    session = repository.get_session(session_id)
    concept = repository.get_concept(concept_id)
    if concept is None:
        raise ValueError("concept not found")

    # Prerequisite detour: never generate a lesson for a concept whose
    # prereqs aren't completed — redirect to the earliest incomplete prereq.
    startable = resolve_startable_concept(concept)

    chunks = await retrieval_client.query_chunks(
        framework=session["framework"],
        version=session.get("framework_version") or "0.115",
        query=startable["name"],
        concept=startable["name"],
    )
    chunks_text = "\n---\n".join(c["text"] for c in chunks[:5]) if chunks else "(no grounded docs found)"

    lesson_prompt = (
        f"Teach the concept '{startable['name']}' ({startable['description']}) for "
        f"'{session['framework']}', in the context of the learner's goal: {session['goal']} "
        f"({session.get('goal_context')}).\n"
        f"Ground your answer in this official documentation excerpt:\n{chunks_text}\n\n"
        f"Respond with JSON: {{\"worked_example\": str, \"guided_practice\": str, "
        f"\"exercise_prompt\": str, \"exercise_test_code\": str}}. "
        f"worked_example is a short annotated example. guided_practice is a near-copy with "
        f"one deliberate gap to fill. exercise_prompt is an original problem in the learner's "
        f"goal-context. exercise_test_code is a pytest snippet (using `from solution import ...` "
        f"is NOT needed — assume the learner's code defines the needed names directly) that "
        f"grades the exercise."
    )
    lesson = await llm_router_client.generate_json("lesson_generator", lesson_prompt)

    cache.set_pending_exercise_test_code(session_id, startable["id"], lesson.get("exercise_test_code", ""))
    repository.update_concept_status(startable["id"], "active")
    repository.update_session(session_id, current_concept_id=startable["id"], phase="lesson_exercise")
    repository.get_or_create_mastery_entry(session_id, startable["id"])

    return {
        "concept_id": str(startable["id"]),
        "concept_name": startable["name"],
        "worked_example": lesson.get("worked_example", ""),
        "guided_practice": lesson.get("guided_practice", ""),
        "exercise_prompt": lesson.get("exercise_prompt", ""),
    }


async def submit_solution(session_id: UUID, concept_id: UUID, code: str) -> dict:
    session = repository.get_session(session_id)
    mastery = repository.get_or_create_mastery_entry(session_id, concept_id)
    test_code = cache.get_pending_exercise_test_code(session_id, concept_id)

    result = await sandbox_client.execute(code=code, test_code=test_code)
    attempts = mastery["attempts"] + 1

    if result["status"] == "pass":
        repository.update_mastery_entry(mastery["id"], mastery_score=1.0, attempts=attempts)
        repository.update_concept_status(concept_id, "completed")
        repository.insert_submission(
            session_id, concept_id, code, result["status"], result.get("stdout", ""), result.get("stderr", ""), None,
        )

        syllabus = repository.get_syllabus_with_concepts(session["syllabus_id"])
        next_concept = repository.next_pending_concept(syllabus["id"])
        repository.update_session(
            session_id,
            current_concept_id=next_concept["id"] if next_concept else None,
            phase="lesson_worked_example" if next_concept else "completed",
        )
        return {"status": "pass", "next_concept_id": str(next_concept["id"]) if next_concept else None}

    # Failure path: hint on first attempt, fuller explanation + difficulty
    # step-down signal once the 2+ failure threshold is hit.
    step_down = should_step_down(attempts)
    error_context = result.get("stderr") or result.get("stdout") or "no output captured"
    task_type = "fuller_explanation" if step_down else "first_pass_hint"
    explain_prompt = (
        f"The learner's code for concept '{concept_id}' failed with:\n{error_context}\n\n"
        f"Their code:\n{code}\n\n"
        + (
            "Give a fuller explanation of what's wrong and how to fix it — they've already failed twice."
            if step_down
            else "Give a short hint only — do not give the full solution."
        )
    )
    feedback = await llm_router_client.generate_text(task_type, explain_prompt)

    repository.update_mastery_entry(mastery["id"], attempts=attempts)
    repository.insert_submission(
        session_id, concept_id, code, result["status"], result.get("stdout", ""), result.get("stderr", ""), feedback,
    )
    return {"status": result["status"], "hint" if not step_down else "explanation": feedback}


async def list_mastery(session_id: UUID) -> list[dict]:
    return repository.list_mastery_entries(session_id)
