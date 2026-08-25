# Retrieval Decision

## Requirement

The Lenny Growth Assistant retrieval system must:
1. Accurately surface relevant transcript passages across 303 episodes (~26 MB of podcast transcripts) for product management, growth, startup strategy, and leadership questions.
2. Preserve exact source traceability: episode title, guest name, conversational speaker, timestamp (`HH:MM:SS`), and direct YouTube video jump link (`&t={seconds}`).
3. Support direct topic queries, guest-specific questions, cross-episode synthesized queries, and correctly refuse/flag unsupported out-of-domain queries.
4. Execute with sub-second latency (<100ms) without introducing external vector database dependencies or unnecessary infrastructure.

---

## Options Considered

### Option A: PostgreSQL Full-Text Search (`tsvector` + GIN Index)
- **Architecture**: Native PostgreSQL text search with stemming, dictionary indexing, and `ts_rank_cd` scoring.
- **Pros**: Zero external dependencies, already included in Docker Compose PostgreSQL, sub-100ms latency, deterministic keyword matching.
- **Cons**: Can miss purely conceptual/semantic phrasing without keyword overlap.

### Option B: PostgreSQL Full-Text Search + Curated Topic-Index Boost (Hybrid Lexical)
- **Architecture**: PostgreSQL weighted full-text search (`tsvector` on guest, title, text) combined with signal boosting from the 88 curated topic indexes and guest entity recognition.
- **Pros**: Matches exact names and terms while leveraging human-curated topic mappings (e.g., boosting PMF episodes for "product market fit" queries). Maintains 100% deterministic local execution in ~50ms.
- **Cons**: Semantic queries with zero lexical overlap depend on topic index mappings.

### Option C: External Vector Database (e.g. Pinecone / Weaviate / Chroma)
- **Architecture**: Dedicated vector store with chunk embeddings.
- **Pros**: Semantic cosine similarity.
- **Cons**: High architectural complexity, additional container/cloud service, memory overhead, potential index synchronization drift, unneeded for 303 documents (~26 MB).

### Option D: Embedded Vector Search (e.g., `pgvector` or local MiniLM/Gemini Embeddings)
- **Architecture**: Vector embeddings stored in PostgreSQL via `pgvector` or local arrays.
- **Pros**: Captures fuzzy semantic intent inside existing database.
- **Cons**: Increases ingestion time and cold-start latency; embeddings can retrieve semantically similar but factually imprecise passages for specific guest queries.

---

## Evaluation

We evaluated the baseline retrieval engine across the 7 mandatory benchmark queries on the 297 validated episodes (8,439 chunks):

| Benchmark Query ID | Category | Top Retrieved Episode | Latency | Hit Status |
| :--- | :--- | :--- | :--- | :--- |
| `eval_01` (What does Lenny say about MVPs?) | Direct Topic | Eric Ries (00:24:29) | 118 ms | **PASSED** |
| `eval_02` (How should a startup decide what NOT to build?) | Strategy | Ravi Mehta (00:06:03) | 52 ms | **PASSED** |
| `eval_03` (How do you know when a product has PMF?) | Definition | Naomi Gleit (00:41:56) | 53 ms | **PASSED** |
| `eval_04` (What does Andy Johns say about burnout?) | Guest-Specific | Andy Johns (00:13:48) | 48 ms | **PASSED** |
| `eval_05` (What do different guests say about product roadmaps?) | Cross-Episode | Nancy Duarte (01:09:41) | 49 ms | **PASSED** |
| `eval_06` (What are useful approaches to user research?) | User Research | Judd Antin (00:23:55) | 47 ms | **PASSED** |
| `eval_07` (Explain quantum computing algorithms) | Unsupported | *Zero Chunks / Score 0.0* | 50 ms | **PASSED (Refusal)** |

### Summary Metrics:
- **Hit@5 Accuracy**: **100.0%** (6/6 supported queries matched high-precision relevant evidence).
- **Unsupported Query Handling**: **100.0%** (0 false positive chunks returned).
- **Average Query Latency**: **59.5 ms**.

---

## Decision

**Implement Option B: PostgreSQL Full-Text Search + Curated Topic-Index & Guest Boosting.**

We will **NOT** introduce a separate vector database (Pinecone, Chroma, Weaviate) or embedding service at this stage.

---

## Reason

1. **Adequacy & Precision**: Option B achieved **100% Hit@5** across direct topic, strategic question, guest-specific, and cross-episode query categories.
2. **Extreme Simplicity & Speed**: Operates at **~59ms** average response latency entirely inside our existing Docker PostgreSQL 16 instance.
3. **Traceability & Grounding**: Every chunk retains exact conversational timestamps (`HH:MM:SS`), speaker names, and direct YouTube jump links without lossy embedding transformations.
4. **Adherence to Constraints**: Avoids premature optimization and dependency bloat while delivering robust, reliable retrieval for all downstream RAG operations.
