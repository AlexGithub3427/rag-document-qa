# Architecture Decision Records

A running log of key technical decisions made during development, including the reasoning
and tradeoffs at the time. Updated as the project evolves.

---

## ADR-001: ChromaDB over pgvector for V1 and V2

**Date:** June 2026
**Status:** Active (revisit at V3)

**Decision:**
Use ChromaDB as the vector store for V1 and V2, with a planned migration to pgvector in V3.

**Reasoning:**
ChromaDB has near-zero configuration overhead — it runs as a single Docker container with
a clean Python client and no database tuning required. For V1, the priority is proving the
core RAG pipeline works, not optimizing infrastructure. ChromaDB lets us move fast without
getting distracted by Postgres configuration.

**Tradeoffs:**
- ChromaDB recall at scale is 91–95% vs pgvector's 99.6–99.8% at 250K+ vectors
- No SQL or relational query support, which limits complex metadata filtering
- Accepting a lower ceiling on retrieval quality in early versions in exchange for faster iteration

**Migration plan:**
V3 introduces user auth and per-user document collections, at which point Postgres is already
needed for session/user data. pgvector consolidates the stack onto a single Postgres instance
rather than running a separate vector DB alongside it.

**Alternatives considered:**
- Pinecone: managed cost ($70–300+/month) and vendor lock-in with no infrastructure story to tell
- Qdrant: stronger metadata filtering but heavier operational footprint than needed for V1

---

## ADR-002: text-embedding-3-small over text-embedding-3-large

**Date:** June 2026
**Status:** Active (revisit if retrieval quality is insufficient in V2)

**Decision:**
Use OpenAI's `text-embedding-3-small` for all document and query embeddings.

**Reasoning:**
At $0.02 per million tokens, 3-small is 6.5x cheaper than 3-large ($0.13/1M). For a
short-document RAG system at portfolio scale, the quality difference is marginal —
benchmarks show 75.8% vs 80.5% accuracy, a gap that rarely justifies the cost premium.
Embedding a 300-page document costs under $3 with 3-small. The wider ecosystem support
also means any LangChain or RAG tutorial will work out of the box.

**Tradeoffs:**
- Slightly lower semantic accuracy than 3-large, particularly on nuanced or complex queries
- If retrieval quality proves insufficient for longer or more technical documents in V2,
  will need to re-embed the entire corpus with 3-large (embeddings are not cross-compatible)

**Migration plan:**
Monitor retrieval quality during V2 multi-document testing. If precision is measurably
insufficient, upgrade to 3-large. The cost increase is acceptable at portfolio scale.

**Alternatives considered:**
- text-embedding-3-large: stronger accuracy but 6.5x cost premium not justified for V1
- nomic-embed-text via Ollama: free and competitive with 3-small, but adds local GPU
  dependency and complicates Docker setup. Revisit in V3 as an offline/privacy demo.

---

## ADR-003: FastAPI over Flask and Django for the backend

**Date:** June 2026
**Status:** Active

**Decision:**
Use FastAPI as the backend API framework.

**Reasoning:**
The backend makes concurrent calls to three external systems: the OpenAI embeddings API,
ChromaDB, and the OpenAI chat completions API. FastAPI's async-native design handles these
concurrently without blocking, where Flask would process them sequentially. FastAPI also
provides automatic OpenAPI/Swagger documentation at `/docs` out of the box, and Pydantic
models enforce schema contracts between services — both valuable for a portfolio project
that needs to be readable by interviewers.

**Tradeoffs:**
- No built-in auth, ORM, or admin panel — these need to be added manually in V3
- Smaller ecosystem than Django, though sufficient for this project's scope

**Alternatives considered:**
- Flask: would require manually adding async support, request validation, and API docs —
  exactly what FastAPI provides out of the box
- Django: overkill for an API-first service; synchronous ORM hurts AI workload performance;
  shines for full SaaS products with billing and admin dashboards, not this project shape

---

## ADR-004: RecursiveCharacterTextSplitter with 500-char chunks and 150-char overlap

**Date:** June 2026
**Status:** Active (revisit chunking strategy in V2)

**Decision:**
Use LangChain's `RecursiveCharacterTextSplitter` with `chunk_size=500` and
`chunk_overlap=150` as the baseline chunking strategy.

**Reasoning:**
RecursiveCharacterTextSplitter respects natural text boundaries (paragraphs, sentences)
before falling back to character splits, producing more semantically coherent chunks than
a naive fixed-size splitter. The 150-character overlap was increased from an initial 50
after observing a known failure mode: section headings (e.g. "Hindquarters:") were being
split from their description content, causing retrieval to return chunks without enough
context for the LLM to answer correctly.

**Known limitations:**
- Character-based chunk size is an approximation — actual token count varies by content.
  A future improvement is token-aware chunking using `tiktoken` to guarantee chunks stay
  within embedding model context limits.
- Overlap reduces but does not eliminate boundary splits for long sections. Retrieval
  quality still degrades when an answer spans more than two consecutive chunks.

**Planned improvements:**
- V2: Switch to token-aware chunking with `tiktoken` for precise context window control
- V2: Experiment with larger chunk sizes (1000 tokens) for documents with long sections
- V2: Store chunk metadata (page number, section heading) to enable source citations

---

## ADR-005: Dockerized microservices architecture

**Date:** June 2026
**Status:** Planned for end of V1

**Decision:**
Separate the system into four Docker containers: FastAPI backend, embedding service,
ChromaDB, and React frontend, orchestrated with Docker Compose.

**Reasoning:**
Separating the embedding service from the main backend API reflects production reality —
in a scaled system, embedding workloads are compute-intensive and benefit from independent
scaling. It also creates a clean separation of concerns: the backend handles orchestration
and business logic, the embedding service handles all OpenAI API calls. This architecture
is a stronger portfolio signal than a monolithic Flask app.

**Tradeoffs:**
- Additional Docker networking complexity compared to a monolith
- Overkill for the scale of this project, but the architecture demonstrates production
  systems thinking rather than tutorial-level design

**Decision to defer Dockerization:**
Dockerization is being done after the core pipeline, FastAPI wrapper, and React frontend
are working locally. Debugging broken logic inside containers is significantly harder than
debugging it first in a known-good local environment, then containerizing what works.

---