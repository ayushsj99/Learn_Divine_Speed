# Architecture

## Overview

The system teaches software frameworks/libraries through a goal-conditioned, doc-grounded, hands-on curriculum. It is built from five pieces — one conversational orchestrator, one knowledge index, one syllabus structure, one stateless lesson/exercise generator, and one real code sandbox — plus a small set of pedagogy rules layered on top. No piece holds more context than it needs; nothing is regenerated that can be cached.

```
User
 │
 ▼
Orchestrator  ──reads/writes──▶  Session State (per user)
 │        │
 │        ├──▶ Diagnostic (pre-check)
 │        ├──▶ Syllabus Builder ──▶ Syllabus (per user, structured)
 │        ├──▶ Retriever ──▶ Doc Knowledge Base (per framework+version, shared)
 │        ├──▶ Lesson/Exercise Generator (stateless, per concept)
 │        └──▶ Sandbox Executor (deterministic code runner)
```

## Deployment Architecture (microservices, Docker-deployable)

The five logical pieces above map to independently deployable services, communicating over plain REST/JSON — no message broker, no gRPC, kept debuggable even as a multi-container system. Local dev runs via Docker Compose; each service is its own container.

```
                        ┌─────────────┐
                        │   Frontend   │  (Next.js/React, own container)
                        └──────┬───────┘
                               │ REST + WebSocket (streaming)
                        ┌──────▼───────┐
                        │  API Gateway  │  FastAPI — auth, session routing, the only
                        │   (BFF)       │  service the frontend talks to
                        └──────┬───────┘
                               │
                   ┌───────────┼────────────────┬───────────────┐
                   ▼                            ▼               ▼
          ┌─────────────────┐         ┌──────────────────┐  ┌──────────────┐
          │  Orchestrator    │◀──────▶│   LLM Router      │  │  Retrieval    │
          │  Service         │         │   Service         │  │  Service      │
          │  (state machine, │         │  (Ollama/Anthropic│  │  (vector DB   │
          │   pedagogy rules)│         │   /OpenAI routing,│  │   query API)  │
          └────────┬─────────┘         │   escalation)     │  └──────▲───────┘
                    │                  └──────────┬────────┘         │
                    ▼                             │                  │
          ┌─────────────────┐                     ▼                  │
          │  Sandbox Service │            ┌──────────────────┐        │
          │  (isolated code  │            │ Doc Ingestion     │───────┘
          │   execution)     │            │ Worker (batch job,│
          └─────────────────┘             │ writes to vector  │
                                            │ DB, runs offline) │
                                            └──────────────────┘
                    ┌─────────────────────────────┐
                    │  State Store: Postgres        │  session state, syllabus,
                    │  (+ Redis for ephemeral cache)│  mastery map — shared by
                    └─────────────────────────────┘  Orchestrator + Gateway
```

### Service responsibilities

| Service | Responsibility | Notes |
|---|---|---|
| **Frontend** | Chat/lesson UI, code editor (Monaco-based) for exercises, progress/mastery dashboard | Talks only to API Gateway; streams orchestrator responses over WebSocket |
| **API Gateway (BFF)** | Auth, session creation/lookup, request routing to Orchestrator, response streaming back to frontend | The only externally-exposed service besides frontend |
| **Orchestrator Service** | The state machine: intake → diagnostic → syllabus walk → lesson → sandbox → reinforcement. Applies pedagogy rules (prereq detour, difficulty step-down, spacing) | Calls LLM Router and Sandbox Service; reads/writes State Store |
| **LLM Router Service** | Single internal API (`POST /generate {task_type, payload}`) that decides Ollama vs hosted API per task_type, handles confidence-based escalation fallback | Provider-agnostic by design — swapping/mixing Anthropic, OpenAI, or local models per task never touches orchestrator logic |
| **Retrieval Service** | Wraps the vector DB (e.g. Qdrant/pgvector); exposes `query(framework, version, concept)` → relevant chunks | Read path only; ingestion writes are separate |
| **Doc Ingestion Worker** | Runs the ingestion pipeline (fetch → validate → chunk → embed → eval-check) per framework/version, offline/on-demand, not in the request path | Runs as a one-off job/cron container, not a long-running server |
| **Sandbox Service** | Spins up an isolated, per-language execution container for submitted code, runs tests, returns deterministic pass/fail + output | Security boundary — most locked-down service (no network egress, resource/time limits) |
| **State Store** | Postgres for durable state (session, syllabus, mastery), Redis for short-lived cache/locks | Shared dependency, not a service with logic of its own |

### Why this decomposition (not finer-grained, not monolith)

- **Sandbox is its own service** because it executes arbitrary user code and needs fundamentally different hardening/isolation than everything else.
- **LLM Router is its own service** because provider/model choice is a cross-cutting, frequently-tuned concern (cost/quality tradeoffs) — isolating it means swapping models/providers never requires redeploying the orchestrator.
- **Doc Ingestion is a worker, not a server** — it's offline/batch by design; running it as an always-on service would be wasted overhead.
- Everything else stays inside the **Orchestrator** rather than being split further (e.g. diagnostic and syllabus-walk logic stay together) — splitting them would add network hops for what's still orchestration over the same state, with no independent scaling/security reason to separate them.

### Tooling

- **uv** manages every Python service — each service has its own `pyproject.toml`/`uv.lock` (or a shared `uv` workspace for common internal libs like state models), Dockerfiles use `uv sync --frozen` for reproducible installs.
- **Docker Compose** for local dev — all services + Postgres + Redis + vector DB, one `Dockerfile` per service, minimal slim-base multi-stage builds.
- **Frontend** is a separate Node-based container, not Python-managed.

## Components

### 1. Orchestrator
The only component the user talks to. Cheap/fast model. Holds no framework knowledge in-context — only the session state object. Each turn: read state → decide next action → call the relevant component → update state → respond.

Responsibilities:
- Run intake (goal, target framework/library, level).
- Trigger diagnostic, syllabus build, lesson delivery, sandbox grading.
- Apply the pedagogy rules (below) as simple branches over state — not as separate agents.

### 2. Session State (datastore)
Structured, not conversational. Fields:
```
{
  goal: "apply_to_project" | "interview_prep" | "understand_only",
  goal_context: free text, can be appended/patched mid-session,
  level: inferred from diagnostic, not self-reported,
  syllabus_ref: pointer to this user's syllabus,
  current_concept: node id,
  mastery_map: { concept_id: { status, confidence_flag, last_reinforced, fail_count } },
}
```
This is what makes every other call stateless and small — no component needs chat history, only this object.

### 3. Doc Knowledge Base
Built once per framework+version, reused by every user. This is a pipeline with a quality gate, not a one-shot script — see [Doc Ingestion Pipeline](#doc-ingestion-pipeline) below for the full detail.
- Chunks, tags with metadata (section, concept, difficulty, version), embeds into a vector index.
- Re-run only on new framework versions. Never fetched live per session.

### 4. Diagnostic
Replaces self-rated level. A short adaptive pre-check: 3-5 concept-tagged questions or a small "predict the output" snippet. Produces real per-concept signal instead of "novice/intermediate/advanced," feeding directly into the syllabus builder and mastery_map.

### 5. Syllabus Builder
Runs once per user. Input: goal + goal_context + diagnostic results + doc concept list. Output: an ordered list of concept nodes, structured data, not prose:
```
[{ concept, required, depth, prereq? }, ...]
```
Cheap to store, cheap to patch — the orchestrator walks this list rather than re-asking an LLM "what's next."
Mid-session goal refinement (e.g. user reveals they're building a CLI, not a web app) is handled as a small JSON patch to remaining nodes, not a full regeneration.

### 6. Lesson/Exercise Generator
Stateless, called once per concept. Input: one concept node + retrieved doc chunks + goal/goal_context. Output follows a fixed 3-step scaffold, not just "explain then quiz":
1. **Worked example** — short, annotated, in the user's goal-context.
2. **Guided practice** — near-copy of the worked example with one deliberate gap to fill.
3. **Independent exercise** — original problem in the same goal-context.

Grounded entirely in retrieved chunks to minimize hallucination.

### 7. Sandbox Executor
Containerized code runner — not an LLM. Executes submitted code, runs tests, returns pass/fail + raw output deterministically.
- On first failure: LLM gives a hint only, using the real error/output as context.
- On second failure: LLM gives a fuller explanation.
- On pass: orchestrator asks one short "why did this work?" free-text question; a lightweight check flags shallow answers as `confidence_flag: shaky` rather than `mastered`.

## Doc Ingestion Pipeline

Per-framework, per-version. Runs offline/async, never blocks a live session. Modeled as a pipeline with a quality gate at the end, not a single scrape-and-go script.

### Source selection (per-framework adapter)

Each supported framework/library has a thin adapter declaring its source type, checked in this priority order:

1. **`llms_txt`** — if the framework's docs site publishes an `llms.txt`/`llms-full.txt`, use it. It's a sanctioned, plain-text export meant specifically for AI consumption — prefer it over everything else when available.
2. **`github_markdown`** — pull the docs source (markdown/MDX) directly from the project's repo at a release tag, covered by the repo's OSS license. Usually more reliable than scraping the rendered site, and sidesteps most robots.txt/ToS restrictions on the rendered docs domain.
3. **`package_metadata`** — README/CHANGELOG/docstrings from the published package (npm/PyPI/etc.). Thinner coverage, safe fallback.
4. **`api`** — if the docs platform exposes a docs-as-JSON/OpenAPI export meant for tooling, use it over HTML scraping.
5. **`scrape`** — only if the site's `robots.txt`/ToS permit it. Requires a headless-browser fetch (most modern doc sites are JS-rendered; plain HTTP fetch returns an empty shell), rate-limited and honestly identified.
6. **`unsupported`** — if none of the above are available or permitted, the framework is marked unsupported rather than ingested via a disallowed method. Degraded fallback (model's pretrained knowledge, no version grounding) is allowed only as an explicit, visibly-labeled last resort — never silent.

### Pipeline steps

1. **Fetch** — via the adapter's source type, with fallback to the next priority tier on failure.
2. **Render** (if `scrape`) — headless browser, not raw HTTP, to handle JS-rendered sites.
3. **Extract** — strip nav/boilerplate, keep headings/prose/code blocks intact (code blocks preserved as code, not flattened).
4. **Validate (quality gate)** — automated checks: reasonable chunk count, code blocks look like real code, headings present. Pages failing this are flagged for retry/skip, never silently indexed.
5. **Dedup** — canonicalize URLs, hash content, drop near-duplicate pages (old version mirrors, redirects, translations).
6. **Chunk + tag** — split by section/heading (not arbitrary token windows), tag with `concept`, `section`, `difficulty`, `version`, `source_url`.
7. **Embed + index** — store in a versioned, namespaced vector index (`framework@version`), never overwriting a prior version in place.
8. **Eval check** — run a fixed set of known-answer queries against the new index (e.g. "useEffect cleanup" → does retrieval surface the right chunk?) before the version is marked ready for use. Acts as a regression test on every re-ingestion.
9. **Publish** — mark `framework@version` as ready; log ingestion timestamp, page success/fail counts, eval pass rate.

### Operational notes

- Respect `robots.txt` and ToS; rate-limit and identify the crawler honestly. Never bypass an explicit disallow.
- Detect new releases via changelog/RSS/GitHub releases API, not by polling the docs site; re-ingest asynchronously when a new version is adopted.
- Observability: per-page fetch/quality status, chunk counts, last successful ingestion, eval pass rate — a silently broken adapter (e.g. site redesign) should surface immediately, not show up as bad lessons downstream.

## Pedagogy rules (implemented as orchestrator branches, not new components)

| Rule | Trigger | Action |
|---|---|---|
| Prerequisite detour | Concept fails and has a `prereq` tag | Insert prereq concept before retrying |
| Difficulty step-down | 2+ failures on independent exercise | Re-attempt at guided-practice level before retrying independent |
| Fast-path skip | Pass on first attempt | Skip remaining drill for that concept, advance |
| Spaced reinforcement | Concept `mastered` and `last_reinforced` older than N sessions/turns | Interleave one review question before next new concept |
| Shaky-mastery flag | Sandbox pass but weak self-explanation | Treat as not-yet-mastered for reinforcement scheduling |
| Goal-context patch | New goal detail surfaces mid-conversation | Patch remaining syllabus nodes' depth/examples, no full rebuild |

## Why this stays simple and token-efficient

- Heavy work (doc indexing) happens once per framework+version, amortized across all users.
- Structured state (session state, syllabus) replaces conversational memory — every LLM call is short and mostly stateless.
- Retrieval keeps lesson generation grounded without stuffing full docs into context.
- Grading is deterministic (real code execution), not LLM judgment — cheaper and more correct; LLM is only used to explain failures.
- All adaptivity (prereqs, difficulty, spacing) is implemented as simple rules/branches over a small state object, not additional agents or planners.

## Model Deployment Strategy (local Ollama vs hosted API, provider-agnostic)

Routed entirely through the **LLM Router Service** via `task_type` — split by call frequency and quality-sensitivity, not by hardcoded provider. "Hosted API" means whichever provider (Anthropic, OpenAI, or other) is configured for that task — chosen and swappable per task, not fixed system-wide.

| Component / Task | Engine | Model suggestion | Why |
|---|---|---|---|
| Orchestrator — routing, state decisions, next-action selection | **Ollama (local)** | `qwen2.5:3b-instruct` or `llama3.2:3b` (4-bit) | Every turn, narrow structured decisions — cheap is fine, keeps the main loop free of API cost/latency. |
| Diagnostic — pre-check question selection | **Ollama (local)** | same 3B model | Templated, low creative burden, runs once per session. |
| Grading check — "why did this work" shallow-vs-real classification | **Ollama (local)**, fine-tune/LoRA candidate later | same 3B model | Narrow classification task. |
| Hint generation (1st sandbox failure) | **Ollama (local)**, escalate to hosted API on low confidence | 3B model, grounded in actual error/stack trace | Frequent, low-stakes nudge. |
| Fuller explanation (2nd sandbox failure) | **Hosted API** (provider configurable) | — | Less frequent, higher quality bar — user is already stuck. |
| Syllabus Builder | **Hosted API** (provider configurable) | — | Reasons over many concepts + goal context at once; a wrong structure derails the whole session; exceeds a 6GB-class context window. |
| Lesson/Exercise Generator (worked example → guided → independent) | **Hosted API** (provider configurable) | — | Highest quality-sensitivity in the system — a hallucinated API in a worked example actively teaches the wrong thing. Runs once per concept, so cost is bounded. |
| Doc ingestion — chunk concept/difficulty tagging | **Hosted API** (rest of pipeline is non-LLM) | — | Batch job, once per framework/version, shared across all users. |
| Sandbox Executor | **Neither (deterministic)** | — | Real code execution, no LLM involved. |

**Resulting cost profile**: per-turn cost is near-zero (local orchestrator/diagnostic/hints handle the high-frequency traffic). Hosted-API spend scales with *concepts taught* and *frameworks/users onboarded* (syllabus + lesson generation + ingestion tagging), not with conversational back-and-forth.

**Escalation safety net**: if a local model's output for a "local" task is malformed, low-confidence, or references something outside the retrieved chunk, the LLM Router falls back to the configured hosted API rather than silently shipping a bad local response.

**Provider-agnostic interface**: the LLM Router exposes one internal contract — `POST /generate {task_type, payload} → {text | json}` — and resolves `task_type` to a specific provider+model via config, not code. Adding/swapping a provider (e.g. trying a different model for the Lesson Generator) is a config change, never a refactor of the Orchestrator or any other service.
