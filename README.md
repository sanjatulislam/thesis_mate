# ThesisMate

A multi-agent assistant for master's students at the IT Department, Uppsala University. It answers questions about the official degree project (thesis) guidelines and finds open thesis positions in Sweden.

- **Thesis rules** come from the department's guidelines PDF, through RAG.
- **Thesis positions** come live from the JobTech JobSearch API.
- A **Supervisor** plans each message and hands the work to two specialist agents, which can work together on one question.

---

## Assignment requirements

| Requirement | How ThesisMate meets it |
|---|---|
| LLM | Qwen 3.8 27B (instruct mode) on Groq |
| Small RAG knowledge base | The IT Department's thesis guidelines PDF, chunked and stored in Weaviate |
| At least 3 tools | 4 tools: `search_guidelines`, `search_jobtech`, `get_job_details`, `check_deadlines` (see below) |
| At least 2 agents with different responsibilities | Thesis Advisor (research on the guidelines) and Job Scout (finding and analysing positions), coordinated by a Supervisor (planning) |
| Agentic framework | LangGraph |
| Simple frontend | React + Vite chat |
| Dynamic decisions | The Supervisor decides which agent(s) handle a message, in what order and whether RAG is needed at all. each agent chooses its own tools |
| Backend handles LLM calls, orchestration, tools, RAG and state | FastAPI + LangGraph, conversation memory per `thread_id` |

**Tools mapped to the example tool types in the brief**

| Tool type in the brief | Tool |
|---|---|
| Search the knowledge base | `search_guidelines`: RAG over the thesis guidelines |
| Call a public API | `search_jobtech`: searches the JobTech JobSearch API (Arbetsförmedlingen) |
| Query structured data | `get_job_details`: looks up one position by id and returns its structured fields |
| Perform a calculation | `check_deadlines`: computes the days left to apply |

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
WEAVIATE_VIEWER_API_KEY=your-read-key
WEAVIATE_ADMIN_API_KEY=your-admin-key   # only needed for ingestion
COHERE_API_KEY=your-cohere-key
HF_TOKEN=your-huggingface-token
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
| Embeddings | `BAAI/bge-base-en-v1.5` (Hugging Face) |
| Reranking | Cohere Rerank |
| PDF processing | PyMuPDF, `RecursiveCharacterTextSplitter` |
| Public API | JobTech JobSearch API |
| Backend | FastAPI, Pydantic |
| Frontend | React + Vite, `react-markdown` |

---

## Agentic architecture and their responsibilities

| Agent | Role | Tools |
|---|---|---|
| **Supervisor** (planner) | Reads the conversation and decides who answers: it replies itself (greetings, unclear or off-topic messages, asking for the programme) or plans 1-3 steps for the agents. It rewrites each step as a standalone task (resolving "it", "the first one") and remembers the student's programme. | none (structured output) |
| **Thesis Advisor** (research) | Answers questions about the thesis rules: deadlines, project plan, roles, eligibility, programme requirements. It answers only from the guidelines and points to the thesis coordinator when something isn't covered. | `search_guidelines` |
| **Job Scout** (analysis) | Finds open thesis positions, sorts and filters them, checks application deadlines and summarizes single positions. | `search_jobtech`, `get_job_details`, `check_deadlines` |

Both specialists are ReAct agents: they decide themselves which tools to call and in which order.

**Conversation state.** Each chat has a `thread_id`. LangGraph's `MemorySaver` checkpointer stores the messages. Memory is in-memory and resets when the server restarts.

---

## RAG pipeline
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

Example: *"Find machine learning thesis positions in Goteborg and tell me if I can do one at a company as my thesis"*
```
Supervisor plan:
  1. job_scout  "Find machine learning thesis positions in Goteborg"
  2. advisor    "Can a master's thesis be done at a company?"
Job Scout   -> searches JobTech, lists positions
Advisor     -> receives the positions as context, checks the guidelines, answers about these positions
finish      -> one combined reply
```

---

## Example questions

Use a new chat for each group.

**RAG (Thesis Advisor)**
- When is the deadline for the project plan?
- Who is responsible for finding a subject reviewer?
- I'm in Data Science. What are the requirements to start my thesis?

  <img width="556" height="484" alt="advisor_agent_ans" src="https://github.com/user-attachments/assets/fd9813e1-0195-4122-9b4b-76822e12116f" />


**Tool use (Job Scout)**
- Find machine learning thesis positions in Stockholm
- Can you tell me more about Reinforcement Learning (RL) one?
- How many days left for applying in this?

<img width="392" height="469" alt="job_scout_agent_ans_1" src="https://github.com/user-attachments/assets/ccef00f5-7c25-49d7-a456-1871d59f0c18" />
<img width="475" height="466" alt="job_scout_agent_ans_2" src="https://github.com/user-attachments/assets/e35c4be9-a6b4-41bf-bcef-7ff7a3c6328c" />
<img width="463" height="475" alt="job_scout_agent_ans_3" src="https://github.com/user-attachments/assets/6ada88f3-10b9-478f-8c1c-05b315ba08a2" />


**Multi-agent collaboration**
- Find machine learning thesis positions in Goteborg and tell me if I can do one at a company as my thesis

<img width="385" height="473" alt="multi_agent_collaboration" src="https://github.com/user-attachments/assets/8594b19d-c2ec-4796-9dac-d90fa722d4c7" />


**Supervisor decisions**
- Hi → replies directly
- Find thesis jobs in Sweden → asks which subject area (no programme known yet)
<img width="557" height="479" alt="direct_ans" src="https://github.com/user-attachments/assets/f9006c1b-280b-4645-94cd-3f17f264233c" />

---

## What I would improve with more time

- **Synthesis and verification:** instead of joining the agents' answers, let an LLM merge them into one coherent reply (keeping dates and links unchanged), then let a verifier check that every part of the question is answered and every claim is supported by the agents' results, retrying or re-planning when the check fails.
- **Re-planning:** let the Supervisor review the plan after each step (e.g. skip the Advisor step when no positions were found). The plan is currently fixed per message to keep it to one planning call.
- **Structured job memory:** keep the ids of the positions shown to the student in the graph state, so follow-ups about "the first one" or "these" never depend on text copied between agents.
- **Long-conversation memory:** summarize older messages, or store more key facts as state fields (like the programme), so details from early in a long chat are kept.
- **Persistent memory:** a SQLite/Postgres checkpointer instead of in-memory state.
- **Evaluation:** an automated test set for routing decisions and RAG answers (correctness, faithfulness). Use LLM-as-judge scoring of RAG answers for correctness against reference answers and faithfulness to the retrieved excerpts.
- **Programme-aware search:** derive several search topics from the student's programme (e.g. Embedded Systems → "embedded systems", "IoT", "real-time systems") and combine the results, instead of one topic per search.
- **Smarter thesis detection:** also check the ad description for clear thesis phrases, or classify ads with a small LLM call, so thesis positions are found even when the title doesn't say so.
- **Citations** linking each rule to its section in the guidelines PDF.
- **Richer UI:** stream responses and show each agent's tool calls live, display job positions as cards with deadline badges, and add example questions to start a chat.
- **Deployment:** Docker Compose for backend and frontend.

## Known limitations

- **Incomplete job follow-ups:** for questions like "when do these close?", the Supervisor copies the earlier positions' titles and links into the Job Scout's task. With long lists, this copied text is sometimes cut off, so the answer covers only some of the positions and the Job Scout asks the student for the missing links. 
- **Groq token limits:** groq's free tier has a daily token limit, so long test sessions can hit rate limits.
- **Limited conversation window:** the Supervisor only sees the last 20 messages, so details mentioned early in a long chat (e.g. a name given in the first message) are forgotten. The student's programme is not affected: it is stored as its own state field and included in every Supervisor prompt.
- **Thesis ad detection:** jobTech ads are not tagged as thesis positions, so a keyword filter decides; a few false positives or misses are possible.
