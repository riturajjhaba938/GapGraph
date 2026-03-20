# 🧠 GapGraph — AI-Adaptive Onboarding Engine

> **Bridges the gap between a candidate's resume and a target Job Description using a multi-agent AI pipeline, NetworkX knowledge graph, and O\*NET skill taxonomy.**

GapGraph is a hackathon project built for CodeForge. It generates a **non-linear, personalized training roadmap** that eliminates "training bloat" — skipping content already mastered by the candidate and enforcing strict prerequisite logic. The output is a **Directed Acyclic Graph (DAG)** of courses with full reasoning traces.

---

## 📋 Table of Contents

1. [How It Works](#how-it-works)
2. [Tech Stack](#tech-stack)
3. [Folder Structure](#folder-structure)
4. [File-by-File Reference](#file-by-file-reference)
5. [Data Schemas](#data-schemas)
6. [API Reference](#api-reference)
7. [Running Locally](#running-locally)
8. [Running Tests](#running-tests)
9. [Key Concepts](#key-concepts)

---

## How It Works

GapGraph runs a **3-agent LangGraph pipeline**. Each agent is a Python function that receives and returns a shared `GapGraphState` object.

```
POST /analyze  (resume file + job description text)
       │
       ▼
┌─────────────────────────────────────────────────────┐
│                 LangGraph Pipeline                  │
│                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐   │
│  │ Agent A  │──▶│ Agent B  │──▶│   Agent C    │   │
│  │Diagnoser │   │ Planner  │   │   Critic     │   │
│  └──────────┘   └──────────┘   └──────┬───────┘   │
│                      ▲          pass  │  fail      │
│                      └───────────────┘            │
└─────────────────────────────────────────────────────┘
       │
       ▼
  JSON Response:
  • skill_gap_vector
  • roadmap DAG (nodes + edges)
  • reasoning_trace (4-step per course)
  • impact_metric (% curriculum bypassed)
```

### Step-by-Step Flow

| Step | Agent | What happens |
|------|-------|-------------|
| 1 | **Agent A — Diagnoser** | Parses the resume and JD. Extracts skills using GPT-4o-mini (or regex fallback). Normalizes all skills to **O\*NET SOC codes**. Computes `P(L₀)` mastery probability per skill. Builds the **Skill-Gap Vector**. |
| 2 | **Agent B — Planner** | Loads `catalog.json` into a **NetworkX DiGraph** (courses = nodes, prerequisites = edges). Runs **Multi-Source Multi-Sink (MSMS)** search to find all courses needed to cover the skill gaps. Applies **skip logic**: if `P(L₀) ≥ 0.85` for all skills a course teaches, that course is marked `skipped=True`. Generates 4-step **Reasoning Trace** per course. |
| 3 | **Agent C — Critic** | Validates every course UUID in the roadmap against `catalog.json` (detects "hallucination gaps"). Checks prerequisite edges are valid. Verifies every node has exactly 4 trace steps. Computes `impact_metric` = `(skipped / total) × 100`. If any check fails → routes back to Agent B for re-planning (max 2 retries). |

---

## Tech Stack

| Technology | Version | Why It's Used |
|------------|---------|---------------|
| **Python** | ≥ 3.11 | Core language |
| **FastAPI** | ≥ 0.110 | HTTP API layer — exposes `/analyze` and debug endpoints |
| **Uvicorn** | latest | ASGI server to run FastAPI |
| **LangGraph** | ≥ 0.1.0 | Orchestrates the 3-agent pipeline as a stateful graph with conditional routing |
| **LangChain / langchain-openai** | ≥ 0.1.0 | LLM integration layer for GPT-4o-mini |
| **OpenAI Python SDK** | ≥ 1.0.0 | Calls GPT-4o-mini for skill extraction from resume/JD text |
| **NetworkX** | ≥ 3.2 | Builds the course Knowledge Graph (DiGraph), runs topological sort, ancestor traversal for MSMS search |
| **Pydantic** | ≥ 2.0 | Type-safe data models and input validation |
| **PyPDF2** | latest | Extracts plain text from uploaded PDF resumes |
| **python-multipart** | latest | Enables `multipart/form-data` file uploads in FastAPI |
| **python-dotenv** | latest | Loads `.env` file (API keys) |
| **pytest** | ≥ 7.0 | Test framework |
| **pytest-asyncio** | latest | Async test support |
| **httpx** | latest | Async HTTP client used in integration tests |

---

## Folder Structure

```
GapGraph/
│
├── README.md                   ← You are here — full project documentation
├── requirements.txt            ← All Python dependencies
├── pytest.ini                  ← Pytest configuration
│
├── data/                       ← Static data files (the "ground truth")
│   ├── catalog.json            ← Course catalog (20 courses with prerequisites)
│   └── onet_taxonomy.json      ← O*NET SOC skill code lookup table
│
├── backend/                    ← All server-side Python code
│   ├── __init__.py
│   ├── main.py                 ← FastAPI app entry point
│   ├── state.py                ← Shared LangGraph state schema (TypedDicts)
│   ├── graph.py                ← LangGraph pipeline builder & compiler
│   │
│   ├── models/                 ← Pydantic API schemas
│   │   ├── __init__.py
│   │   ├── request.py          ← API Request models
│   │   ├── response.py         ← API Response models
│   │   ├── skill.py            ← Skill gap schemas
│   │   ├── roadmap.py          ← DAG Course nodes & edges schemas
│   │   └── critique.py         ← Critic validation report schema
│   │
│   ├── agents/                 ← The 3 AI agents
│   │   ├── __init__.py
│   │   ├── diagnoser.py        ← Agent A: skill extraction + O*NET normalization
│   │   ├── planner.py          ← Agent B: NetworkX MSMS search + roadmap DAG
│   │   └── critic.py           ← Agent C: validation, hallucination detection, impact metric
│   │
│   └── routers/                ← FastAPI route handlers
│       ├── __init__.py
│       └── analyze.py          ← /analyze, /diagnose, /plan, /critique endpoints
│
└── tests/                      ← All test files
    ├── __init__.py
    ├── test_diagnoser.py        ← Unit tests for Agent A
    ├── test_planner.py          ← Unit tests for Agent B
    ├── test_critic.py           ← Unit tests for Agent C
    ├── test_e2e.py              ← End-to-end integration test
    └── fixtures/
        ├── resume.txt           ← Sample candidate resume (John Doe, Python/Docker/SQL)
        └── jd.txt               ← Sample job description (Senior ML Engineer)
```

---

## File-by-File Reference

### `requirements.txt`
Lists all Python package dependencies. Install with:
```bash
pip install -r requirements.txt
```
Key packages: `fastapi`, `langgraph`, `networkx`, `openai`, `pypdf2`, `pydantic`.

---

### `data/catalog.json`
The **course catalog** — the single source of truth for all courses. Contains **20 courses** across beginner → advanced levels.

Each entry has:
```json
{
  "uuid": "c-005",
  "title": "Containerization 101 — Docker",
  "skills_taught": ["ONET-2.B.3.k"],
  "prerequisites": ["c-001"],
  "level": "intermediate",
  "duration_hours": 10
}
```

| Field | Description |
|-------|-------------|
| `uuid` | Unique identifier (e.g., `c-001` to `c-020`) |
| `title` | Human-readable course name |
| `skills_taught` | O\*NET codes this course delivers |
| `prerequisites` | UUIDs of courses that must be completed first |
| `level` | `beginner` / `intermediate` / `advanced` |
| `duration_hours` | Estimated completion time |

Full list of courses:

| UUID | Course | Level | Hours | Prereqs |
|------|--------|-------|-------|---------|
| c-001 | Linux Fundamentals | beginner | 8 | — |
| c-002 | Git & Version Control | beginner | 4 | — |
| c-003 | Python Programming Fundamentals | beginner | 20 | — |
| c-004 | SQL & Relational Databases | beginner | 12 | — |
| c-005 | Containerization 101 — Docker | intermediate | 10 | c-001 |
| c-006 | REST API Design with FastAPI | intermediate | 14 | c-003 |
| c-007 | Data Structures & Algorithms | intermediate | 24 | c-003 |
| c-008 | Cloud Computing Basics (AWS/GCP) | intermediate | 16 | c-001, c-002 |
| c-009 | Kubernetes & Container Orchestration | advanced | 20 | c-005 |
| c-010 | Machine Learning Fundamentals | intermediate | 30 | c-003, c-004 |
| c-011 | Deep Learning & Neural Networks | advanced | 40 | c-010 |
| c-012 | Data Engineering & ETL Pipelines | intermediate | 18 | c-003, c-004 |
| c-013 | CI/CD & DevOps Practices | intermediate | 14 | c-002, c-005 |
| c-014 | TypeScript & Modern JavaScript | beginner | 16 | — |
| c-015 | React Frontend Development | intermediate | 20 | c-014 |
| c-016 | System Design & Distributed Systems | advanced | 30 | c-006, c-008 |
| c-017 | Natural Language Processing (NLP) | advanced | 25 | c-010 |
| c-018 | Cybersecurity Fundamentals | intermediate | 16 | c-001, c-006 |
| c-019 | Agile & Scrum Methodology | beginner | 4 | — |
| c-020 | MLOps & Model Deployment | advanced | 20 | c-010, c-013 |

---

### `data/onet_taxonomy.json`
An **offline O\*NET SOC skill code lookup table**. Maps common skill names to standardized O\*NET codes.

Example:
```json
{
  "Docker": "ONET-2.B.3.k",
  "Python": "ONET-2.B.3.b",
  "Linux command line": "ONET-4.C.1.a",
  "Kubernetes": "ONET-2.B.3.l"
}
```

Used by Agent A to normalize raw skill strings extracted from the resume/JD into consistent codes that can be matched against `catalog.json`.

---

### `backend/main.py`
**FastAPI application entry point.** Responsibilities:
- Creates the `FastAPI` app with title, description, and version metadata.
- Adds **CORS middleware** (allows all origins — suitable for hackathon, restrict in production).
- Mounts the `analyze_router` from `backend/routers/analyze.py`.
- Exposes `/health` and `/` system endpoints.
- Auto-generates interactive API docs at `/docs` (Swagger UI) and `/redoc`.

---

### `backend/state.py`
**Shared state schema** for the LangGraph pipeline. All agents read from and write to a `GapGraphState` dict — no global variables, no direct agent-to-agent calls.

Key TypedDicts:

| Type | Purpose |
|------|---------|
| `NormalizedSkill` | A single skill with O\*NET code, years of experience, required level, and mastery probability `P(L₀)` |
| `ReasoningStep` | One of the 4 auditable steps in the reasoning trace (`step`, `label`, `description`) |
| `RoadmapNode` | A course in the final roadmap: UUID, title, skipped flag, level, hours, skills taught, trace |
| `RoadmapEdge` | A prerequisite relationship: `source` UUID → `target` UUID |
| `CritiqueReport` | Critic's validation output: `passed`, `hallucination_flags`, `missing_prerequisites`, `message` |
| `GapGraphState` | The full pipeline state containing all of the above, passed between every agent |

---

### `backend/graph.py`
**LangGraph pipeline definition.** Builds and compiles the stateful agent graph:

```
diagnose → plan → critique
                    │
            ┌───────┴────────┐
           pass            fail
            │                │
           END       increment_retry → plan
                     (max 2 retries)
```

Key functions:
- `build_graph()` — registers nodes, sets entry point, adds edges and conditional routing.
- `get_graph()` — returns a singleton compiled graph (lazy initialization, avoids rebuilding on every request).
- `_increment_retry()` — increments the `retry_count` in state when Critic fails, preventing infinite loops.

---

### `backend/agents/diagnoser.py` — Agent A
**The Diagnoser.** Extracts skills and computes the Skill-Gap Vector.

Key functions:

| Function | What it does |
|----------|-------------|
| `normalize_to_onet(skill_name)` | Maps a raw skill string to an O\*NET code using exact match → case-insensitive → substring → synthetic fallback |
| `compute_mastery_prob(years, freq)` | Calculates `P(L₀) = min(1.0, (years/3) × frequency_score)` |
| `_extract_skills_with_llm(text, mode)` | Calls **GPT-4o-mini** to extract structured skills from resume or JD text. Falls back to regex if no API key |
| `_extract_skills_regex(text, mode)` | Regex-based fallback that scans for known skills from `onet_taxonomy.json` |
| `diagnose(state)` | **Main agent function.** Orchestrates extraction → normalization → gap vector computation |

**Skill-Gap Vector format:**
```json
{
  "Docker": {"onet_code": "ONET-2.B.3.k", "candidate": 0.667, "required": 0.8, "gap": 0.133},
  "Python": {"onet_code": "ONET-2.B.3.b", "candidate": 1.0, "required": 1.0, "gap": 0.0}
}
```

---

### `backend/agents/planner.py` — Agent B
**The Planner.** Builds the knowledge graph, finds paths, applies skip logic.

Key functions:

| Function | What it does |
|----------|-------------|
| `load_catalog()` | Reads `data/catalog.json` into a Python list |
| `build_knowledge_graph(catalog)` | Builds a NetworkX `DiGraph`: each course = node, each prerequisite = directed edge |
| `msms_search(G, sink_uuids)` | **Multi-Source Multi-Sink search** — finds all ancestor courses (transitive prerequisites) for every sink course using `nx.ancestors()` |
| `plan(state)` | **Main agent function.** Determines sink courses from skill gaps, runs MSMS, applies skip logic, generates 4-step reasoning trace per course, builds edges between roadmap courses |

**Skip logic:**
- For each course in the roadmap, compute the average `P(L₀)` across all skills it teaches.
- If the average ≥ 0.85 → `skipped = True` (candidate already knows this material).

**Reasoning Trace (4 steps per course):**
```
Step 1: "Target Skill" → what JD skill this course addresses
Step 2: "Catalog Match" → course title and UUID found
Step 3: "Dependency Check" → list of prerequisite courses
Step 4: "Final Action" → INCLUDE or SKIP with justification
```

---

### `backend/agents/critic.py` — Agent C
**The Critic.** Validates the roadmap and computes the impact metric.

Key functions:

| Function | What it does |
|----------|-------------|
| `_load_valid_uuids()` | Reads `catalog.json` and returns `{uuid: course_dict}` |
| `critique(state)` | **Main agent function.** Runs 4 checks, computes impact metric, returns `CritiqueReport` |
| `route_critique(state)` | **LangGraph routing function.** Returns `"pass"` → END or `"fail"` → increment_retry. Caps retries at 2. |

**4 Validation Checks:**
1. Every node UUID must exist in `catalog.json` → detects **hallucinated courses**
2. Every edge endpoint must exist in `catalog.json` and be a defined prerequisite → detects **invalid prerequisite edges**
3. Every node's trace must have **exactly 4 steps** with step numbers 1–4
4. `impact_metric = (skipped_courses / total_courses) × 100`

---

### `backend/routers/analyze.py`
**FastAPI route handlers.** Manages HTTP request parsing and delegates to the LangGraph graph.

| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/analyze` | POST | **Full pipeline** — runs all 3 agents. Accepts `resume` (file upload) + `jd` (form text). Returns full JSON response. |
| `/diagnose` | POST | **Debug** — runs Agent A only. Returns skill lists and gap vector. |
| `/plan` | POST | **Debug** — runs Agent A + B. Returns roadmap nodes/edges and reasoning trace. |
| `/critique` | POST | **Debug** — runs all 3 agents, returns critique report and impact metric. |

Helper function `_extract_text_from_file()` handles both **PDF** (via `PyPDF2`) and **plain text** resume files.

---

### `tests/test_diagnoser.py`
Unit tests for Agent A:
- O\*NET normalization (exact match, case-insensitive, substring, fallback)
- Mastery probability calculation (`P(L₀)` formula)
- Skill-Gap Vector structure validation

### `tests/test_planner.py`
Unit tests for Agent B:
- Knowledge graph build → asserts `nx.is_directed_acyclic_graph(G) == True`
- MSMS path finding
- Skip logic (high mastery → `skipped=True`)

### `tests/test_critic.py`
Unit tests for Agent C:
- Hallucination detection (fake UUID injected → flagged)
- Invalid prerequisite edge detection
- Reasoning trace format validation (exactly 4 steps)

### `tests/test_e2e.py`
Full integration test using `httpx.AsyncClient`:
- POSTs `resume.txt` + `jd.txt` to `/analyze`
- Asserts all 4 response keys: `skill_gap_vector`, `roadmap`, `reasoning_trace`, `impact_metric`
- Verifies roadmap is a valid DAG

### `tests/fixtures/resume.txt`
Sample candidate resume: **John Doe**, a Python/FastAPI/Docker engineer with 3 years of experience. Has: Python (3yr), Docker (2yr), SQL (3yr), FastAPI (2yr), Git (4yr), Linux (2yr), AWS (1yr).

### `tests/fixtures/jd.txt`
Sample job description: **Senior ML Engineer at TechCorp AI Division**. Requires: Python (expert), ML/scikit-learn, Deep Learning/PyTorch, Kubernetes, Docker, SQL, ETL, MLOps, REST APIs, Linux, Git, CI/CD.

---

## Data Schemas

### `GapGraphState` — full pipeline context
```python
class GapGraphState(TypedDict):
    resume_text: str                              # raw resume input
    jd_text: str                                  # raw JD input
    candidate_skills: List[NormalizedSkill]       # extracted from resume
    jd_skills: List[NormalizedSkill]              # extracted from JD
    skill_gap_vector: Dict[str, Dict[str, float]] # gap per skill
    roadmap_nodes: List[RoadmapNode]              # ordered courses
    roadmap_edges: List[RoadmapEdge]              # prerequisite edges
    reasoning_trace: List[ReasoningStep]          # all traces combined
    critique_result: Optional[CritiqueReport]     # validation results
    impact_metric: float                          # % curriculum bypassed
    retry_count: int                              # loop guard (max 2)
```

### API Response `/analyze`
```json
{
  "skill_gap_vector": {
    "Docker": {"onet_code": "ONET-2.B.3.k", "candidate": 0.667, "required": 0.8, "gap": 0.133}
  },
  "roadmap": {
    "nodes": [
      {
        "uuid": "c-005",
        "title": "Containerization 101 — Docker",
        "skipped": false,
        "level": "intermediate",
        "duration_hours": 10,
        "skills_taught": ["ONET-2.B.3.k"],
        "trace": [
          {"step": 1, "label": "Target Skill", "description": "Docker"},
          {"step": 2, "label": "Catalog Match", "description": "Found 'Containerization 101 — Docker' (c-005)"},
          {"step": 3, "label": "Dependency Check", "description": "Prerequisites: Linux Fundamentals"},
          {"step": 4, "label": "Final Action", "description": "INCLUDE in roadmap"}
        ]
      }
    ],
    "edges": [
      {"source": "c-001", "target": "c-005"}
    ]
  },
  "reasoning_trace": [...],
  "impact_metric": 40.0,
  "critique": {"passed": true, "hallucination_flags": [], "missing_prerequisites": [], "message": "..."}
}
```

---

## API Reference

### `POST /analyze` ← Main endpoint
**Request** (`multipart/form-data`):
- `resume`: File — PDF or plain `.txt` resume
- `jd`: Text — Job description (plain text, pasted directly)

**Response**: Full JSON with `skill_gap_vector`, `roadmap`, `reasoning_trace`, `impact_metric`, `critique`.

### `POST /diagnose` — Debug
Runs Agent A only. Returns `candidate_skills`, `jd_skills`, `skill_gap_vector`.

### `POST /plan` — Debug
Runs Agent A + B. Returns `roadmap` (nodes + edges) and `reasoning_trace`.

### `POST /critique` — Debug
Runs all 3 agents. Returns `critique_result` and `impact_metric`.

### `GET /health`
Returns `{"status": "ok", "version": "1.0.0", "openai_key_set": true/false}`.

### Interactive Docs
Visit **`http://localhost:8000/docs`** for the full Swagger UI.

---

## Running Locally

### 1. Clone & install dependencies
```bash
cd GapGraph
pip install -r requirements.txt
```

### 2. Set up environment variables
```bash
# Create a .env file
OPENAI_API_KEY=sk-your-key-here
```
> **Without an API key**, the system will automatically fall back to a regex-based extractor — no crash, just less accurate skill extraction.

### 3. Start the server
```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Test it
Open your browser at **`http://localhost:8000/docs`** and use the `/analyze` endpoint:
- Upload `tests/fixtures/resume.txt`
- Paste the contents of `tests/fixtures/jd.txt` as the JD

---

## Running Tests

```bash
cd GapGraph
pytest tests/ -v
```

Run a specific test file:
```bash
pytest tests/test_diagnoser.py -v
pytest tests/test_planner.py -v
pytest tests/test_critic.py -v
pytest tests/test_e2e.py -v
```

---

## Key Concepts

### O\*NET SOC Normalization
All skills extracted from resumes and JDs are mapped to **O\*NET Standard Occupational Classification** codes (e.g., `ONET-2.B.3.k` = Docker). This ensures:
- A candidate's "containers" and a JD's "Docker" map to the same code.
- Cross-domain skills (e.g., "Python" mentioned differently) are unified.
- The `onet_taxonomy.json` acts as an offline fallback; a live O\*NET API can replace it.

### Mastery Probability `P(L₀)`
```
P(L₀) = min(1.0, (years_of_experience / 3) × frequency_score)
```
- 3+ years → full mastery (1.0)
- `frequency_score` defaults to 1.0 (skill appears in resume)
- If `P(L₀) ≥ 0.85` for all skills a course teaches → course is **skipped**

### Multi-Source Multi-Sink (MSMS) Search
Uses `networkx.ancestors()` to find all transitive prerequisite courses for each "sink" (JD-required course). The union of all ancestors + sinks = the complete required learning path. This ensures you never skip a prerequisite, even if it's 3 levels deep.

### Hallucination Grounding
Agent C cross-validates every course UUID in the generated roadmap against the real `catalog.json`. Any UUID that doesn't exist in the catalog = hallucination. If found, the pipeline routes back to Agent B for a corrected plan (up to 2 retries).

### Impact Metric
```
impact_metric = (skipped_courses / total_courses) × 100
```
Represents the **percentage of the standard curriculum bypassed** for this specific candidate. A higher number = more efficient, personalized roadmap.