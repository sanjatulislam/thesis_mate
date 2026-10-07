# ThesisMate

A multi-agent assistant for master's students at the IT Department, Uppsala University. It answers questions about the official degree project (thesis) guidelines and finds open thesis positions in Sweden.

- **Thesis rules** come from the department's guidelines PDF, through RAG.
- **Thesis positions** come live from the JobTech JobSearch API (Arbetsförmedlingen).
- A **Supervisor** plans each message and hands the work to two specialist agents, which can work together on one question.

---

## How to run

### Prerequisites
- Python 3.13+ and [uv](https://docs.astral.sh/uv/)
- Node.js 22+ (tested with 22.18)
- API keys: Groq (LLM), Weaviate Cloud (vector database), Cohere (reranking)

### 1. Backend
Create a file `backend/.env` with these variables:

```
GROQ_API_KEY=your-groq-key
WEAVIATE_URL=https://your-cluster.weaviate.cloud
WEAVIATE_API_KEY=your-read-key
WEAVIATE_ADMIN_API_KEY=your-admin-key   # only needed for ingestion
COHERE_API_KEY=your-cohere-key
```

Then install the dependencies:
```bash
cd backend
uv sync                      # creates .venv and installs from uv.lock
```

### 2. Load the knowledge base (once)
```bash
uv run python -m ingestion.ingestion_pipeline
```
This chunks the guidelines PDF, embeds the chunks and stores them in Weaviate. If the collection already has data, it is skipped; use `rebuild=True` to re-ingest after changing the chunking.

### 3. Start the API
```bash
uv run python main.py        # http://127.0.0.1:8000  (Swagger UI at /docs)
```

### 4. Start the frontend
```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```
The Vite dev server forwards `/api` to the backend, so no CORS setup is needed.

---

## Technologies

| Area | Choice |
|---|---|
| Agent framework | LangGraph (StateGraph, conditional edges, MemorySaver), LangChain `create_agent` |
| LLM | Qwen model served by Groq (`langchain-groq`) |
| Vector database | Weaviate Cloud, hybrid search (BM25 + vectors) |
| Embeddings | `BAAI/bge-base-en-v1.5` (Hugging Face, normalized, query instruction prefix) |
| Reranking | Cohere Rerank |
| PDF processing | PyMuPDF, `RecursiveCharacterTextSplitter` |
| Public API | JobTech JobSearch API (Arbetsförmedlingen) |
| Backend | FastAPI, Pydantic |
| Frontend | React + Vite, `react-markdown` |

---

## Architecture

The React chat sends each message to the FastAPI backend (`POST /api/chat`), which runs a LangGraph graph:

1. **Supervisor** reads the conversation and either replies itself or creates a plan of 1–3 steps.
2. **Thesis Advisor** and **Job Scout** carry out the steps in order. The Advisor searches the guidelines in Weaviate; the Job Scout calls the JobTech API.
3. **finish** joins the agents' answers into one reply, which goes back to the UI together with the plan.

<!-- Demo screenshots -->

```
backend/
  main.py              FastAPI app (/api/chat, /api/health)
  agents/              graph, Supervisor, Thesis Advisor, Job Scout, state, tools, prompts
  retrival/            retriever (hybrid search + rerank) and RAG answer generation
  job_search/          JobTech client, thesis filtering, deadline helpers
  ingestion/           PDF loading, chunking and storing in Weaviate
  dto/                 request/response models
frontend/
  src/App.jsx          chat UI
```

**Conversation state.** Each chat has a `thread_id`. LangGraph's `MemorySaver` checkpointer stores the messages, the student's programme and the current plan per thread, so follow-ups like "tell me more about the first one" work. Memory is in-memory and resets when the server restarts.

---

## Agents and their responsibilities

| Agent | Role | Tools |
|---|---|---|
| **Supervisor** (planner) | Reads the conversation and decides who answers: it replies itself (greetings, unclear or off-topic messages, asking for the programme) or plans 1–3 steps for the agents. It rewrites each step as a standalone task (resolving "it", "the first one") and remembers the student's programme. | none (structured output) |
| **Thesis Advisor** (research) | Answers questions about the thesis rules: deadlines, project plan, roles, eligibility, programme requirements. It answers only from the guidelines and points to the thesis coordinator when something isn't covered. | `search_guidelines` |
| **Job Scout** (analysis) | Finds open thesis positions, sorts and filters them, checks application deadlines and summarizes single positions. | `search_jobtech`, `get_job_details`, `check_deadlines` |

Both specialists are ReAct agents: they decide themselves which tools to call and in which order.

---

## Tools and RAG

| Tool | Type | What it does |
|---|---|---|
| `search_guidelines` | Knowledge base search | Runs the RAG pipeline over the guidelines and returns a grounded answer |
| `search_jobtech` | Public API | Searches JobTech for thesis positions by topic and city; supports `sort="newest"` and published-date filters; keeps only open thesis ads |
| `get_job_details` | Public API lookup | Fetches the full description, deadline and link of one position |
| `check_deadlines` | Calculation + filter | Computes days left to apply, filters by `within_days`, sorts by urgency |

**RAG pipeline**
1. **Ingestion:** PyMuPDF extracts the PDF; pages are merged and page numbers removed so sections are not cut at page breaks. Chunks of 1500 characters with 300 overlap, split on programme headings first, so each programme's rules stay together. Each chunk gets a `chunk_id`.
2. **Query decomposition:** the question is split into focused English sub-queries (structured output), e.g. a question about two topics becomes two searches.
3. **Hybrid retrieval:** Weaviate combines BM25 (exact terms like "VT27" or "TDA2M") with vector search (meaning).
4. **Reranking:** Cohere reranks the candidates per sub-query; duplicates are merged by `chunk_id`.
5. **Grounded answer:** the LLM answers only from the retrieved excerpts, with dates and programme rules kept exact; if the answer isn't there, it says so.

---

## How the agents coordinate

ThesisMate uses **Plan-and-Execute** at the top level and **ReAct** inside each specialist.

1. The **Supervisor** creates a plan: a list of steps, each with an agent and a standalone task. One message can need zero, one or several steps.
2. LangGraph runs the steps in order. A routing function sends each step to its agent and, when the plan is done, to `finish`.
3. **Results are passed along:** each agent receives the answers of the earlier steps together with its own task, so a later agent can build on an earlier one.
4. `finish` joins the answers into one reply, which is saved to the conversation.

Example: *"Find data science thesis positions in Uppsala and tell me if I can do one at a company."*
```
Supervisor plan:
  1. job_scout  "Find data science thesis positions in Uppsala"
  2. advisor    "Can a master's thesis be done at a company?"
Job Scout   -> searches JobTech, lists positions
Advisor     -> receives the positions as context, checks the guidelines, answers about these positions
finish      -> one combined reply
```
The UI shows the route above each reply, e.g. `[Supervisor → Job Scout → Thesis Advisor]`; hovering shows each step's task.

---

## Example questions

Use a new chat for each group.

**RAG (Thesis Advisor)**
- When is the deadline for the project plan?
- Who is responsible for finding a subject reviewer?
- I'm in Data Science. What are the requirements to start my thesis?

**Tool use (Job Scout)**
- Find machine learning thesis positions in Stockholm
- Which of these close within 7 days?
- Tell me more about the first one
- Show the newest data science thesis positions posted this week

**Multi-agent collaboration**
- Find data science thesis positions in Uppsala and tell me if I can do one at a company as my thesis
- What do I need to start my thesis, and are there AI thesis jobs in Uppsala?

**Supervisor decisions**
- Hi → replies directly
- Find thesis jobs in Sweden → asks which subject area (no programme known yet)
- My friend studies Embedded Systems, what are her requirements? → answers about TIS2M without changing your stored programme

---

## What I would improve with more time

- **Verifier agent** that checks the Advisor's answer against the retrieved excerpts before replying.
- **Re-planning:** let the Supervisor review the plan after each step (e.g. skip the Advisor step when no positions were found). The plan is currently fixed per message to keep it to one planning call.
- **Persistent memory:** a SQLite/Postgres checkpointer instead of in-memory state.
- **Structured job memory:** keep the ids of the positions shown to the student in the graph state, so follow-ups about "the first one" or "these" never depend on text copied between agents.
- **Streaming responses** and showing tool calls live in the UI.
- **Evaluation:** an automated test set for routing decisions and RAG answers (correctness, faithfulness), run on every change.
- **Better job relevance:** rank positions by similarity to the student's programme, and cache JobTech results.
- **Citations** linking each rule to its section in the guidelines PDF.
- **Deployment:** Docker Compose for backend and frontend.

## Known limitations

- Groq's free tier has a daily token limit; long test sessions can hit rate limits.
- JobTech ads are not tagged as thesis positions, so a keyword filter decides; a few false positives or misses are possible.
- The guidelines cover six programmes; other programmes are out of scope.
- Job follow-ups ("when does the third one close?") depend on the Supervisor copying the earlier positions' links into the Job Scout's task. If that text is incomplete, the Job Scout may miss a position or ask the student for the link. Storing the last shown job ids in the graph state would make follow-ups independent of the task text.
