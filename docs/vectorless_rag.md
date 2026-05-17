# Vectorless RAG

## What "vectorless RAG" means

Vectorless RAG retrieves context without embeddings and without vector databases. Instead of nearest-neighbor search in embedding space, retrieval is based on lexical overlap.

## Why BM25 is used

BM25 is a mature sparse retrieval method that ranks documents by term relevance and inverse document frequency. It is a strong baseline for structured internal corpora where terminology is relatively stable.

## How it differs from vector DB-based RAG

Vector DB-based RAG:
- Requires embedding model + vector index
- Captures semantic similarity better
- Adds infrastructure complexity and cost

Vectorless BM25 RAG:
- Uses token matching and IDF scoring only
- No embedding compute or vector storage
- Easier to inspect and debug

## Pros

- Minimal infrastructure
- Fast setup
- Transparent scoring
- Lower cost for small/medium internal datasets

## Cons

- Weaker semantic generalization
- Sensitive to wording mismatch
- Requires better chunk quality and keyword-rich content

## When to choose this approach

- Compliance-sensitive environments
- Early-stage prototypes
- Teams needing explainability and low operational overhead
- Internal documentation with predictable vocabulary
