# PRD — Learn Divine Speed

## Problem

People want to learn a software framework/library fast, but generic tutorials don't adapt to *why* someone is learning (apply to a project vs. interview prep vs. general understanding), don't verify real skill level, and rarely give grounded, hands-on, goal-relevant practice tied to the actual current documentation.

## Goal

Build an agent-driven learning experience that: takes a framework/library + a learning goal, diagnoses real current skill, builds a personalized syllabus from the latest official docs, and teaches through worked examples and hands-on coding exercises in a real sandbox — adapting as the learner progresses, optimized for fast, durable learning and low token cost.

## Target users

Anyone learning a new framework/library/SDK who wants either: to apply it in a specific project/use case, to prepare for interviews, or to quickly understand what it is/does.

## Scope (v1)

In scope:
- Intake: framework/library name, learning goal, goal context (free text).
- Diagnostic pre-check (replaces self-rated level) to calibrate starting depth.
- Doc ingestion pipeline for one framework/version at a time (official docs + official examples/cookbook pages).
- Goal-conditioned syllabus generation (structured, not prose).
- Lesson delivery: worked example → guided practice → independent exercise, per concept.
- Sandboxed code execution with deterministic grading + hint-then-explain failure flow.
- Mastery tracking with prerequisite detours, difficulty step-down/up, and spaced reinforcement.
- Mid-session goal refinement (syllabus patching, not full regeneration).

Out of scope (v1):
- Multiple frameworks/languages simultaneously in one session.
- Community/social features (sharing progress, leaderboards).
- Non-code-based subjects (this is scoped to frameworks/libraries that involve writing code).
- Mobile-native client (web-first).

## User flow

1. User states what they want to learn and why (apply to project / interview prep / understand only), plus any context (e.g. "building a CLI tool").
2. System runs a short diagnostic instead of asking the user to self-rate.
3. System builds a personalized syllabus from the latest official docs for that framework/version, ordered and scoped to the stated goal.
4. For each concept: worked example (in the user's context) → guided practice → independent exercise in the sandbox.
5. On failure: hint first, fuller explanation on repeated failure. On pass: a short "why did this work" check to catch shallow passes.
6. System reinforces older concepts at intervals rather than treating "passed once" as done.
7. If the user reveals new goal context mid-session, the remaining syllabus adjusts without restarting.

## Success metrics

- **Time-to-competence**: time/exercises needed to reach passing mastery on syllabus-required concepts, vs. baseline (self-study/tutorial).
- **Retention**: pass rate on spaced-reinforcement checks for previously "mastered" concepts.
- **Relevance**: % of exercises directly tied to stated goal context (should be ~100% by design).
- **Cost efficiency**: average tokens per learner-session, and doc-ingestion cost amortized across users of the same framework/version.
- **Drop-off rate**: where in the syllabus users disengage (signals difficulty miscalibration).

## Non-functional requirements

- Lesson/exercise content must be grounded in retrieved official doc chunks — minimize hallucinated APIs.
- Doc indexing must be versioned and reusable across users; never re-fetched per session.
- Sandbox execution must be isolated (no cross-user code execution risk).
- Each LLM call should be small/stateless where possible — session/mastery state carries continuity, not chat history.
- System should clearly track per-concept mastery in a way that supports resuming a session later.

## Open questions

- Which framework/library to launch with first (pick one for v1 to validate the full loop end-to-end before generalizing the doc-ingestion pipeline to others)?
- How is "official docs + examples" sourced/scraped per framework — is there a uniform method, or framework-by-framework adapters?
- What's the sandbox execution environment (per-language container strategy) for the first supported framework(s)?
- Auth/persistence model for resuming a learning session across days?
