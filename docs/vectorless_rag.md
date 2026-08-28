# Vectorless retrieval design

## Retrieval algorithm

The retriever combines two normalized sparse signals:

- BM25 rewards informative token overlap and term rarity.
- Character n-gram TF-IDF recovers partial words, identifiers, spelling variants, and some compound
  term variation.

Scores are combined, sorted, and filtered by both an absolute minimum and a threshold relative to
the best candidate. The API returns at most `DEFAULT_TOP_K` results. If no candidate survives, the
generation workflow abstains rather than asking the model to answer without evidence.

## Authorization ordering

Authorization happens before ranking. The store query filters by `tenant_id` and intersects the
caller's roles with each document's allowed roles. Unauthorized text is therefore not in the
retrieval corpus, scores, prompt, source list, or model-provider request.

This ordering is a mandatory security property. Do not optimize by loading a global corpus and
filtering the top results afterward; ranking can leak document existence and reduce recall for the
authorized corpus.

## Configuration

| Setting | Purpose | Default |
|---|---|---|
| `DEFAULT_TOP_K` | Maximum evidence chunks | `5` |
| `RETRIEVAL_MIN_SCORE` | Absolute confidence floor | `0.05` |
| `RETRIEVAL_MIN_RELATIVE_SCORE` | Fraction of the best score a result must meet | `0.20` |
| `CHUNK_SIZE_WORDS` | Target chunk size | `220` |
| `CHUNK_OVERLAP_WORDS` | Context overlap | `40` |

Tune these on a representative, tenant-safe golden dataset. A higher threshold improves precision
and abstention but may reduce recall. Larger overlaps can preserve context while increasing storage,
duplicate evidence, and prompt size.

## Appropriate use

Sparse retrieval is a good fit when terminology is stable, explainability matters, data egress must
be minimized, and corpus size is moderate. Consider a dense or hybrid index when questions contain
frequent paraphrases, multiple languages, noisy OCR, or semantic concepts with little lexical
overlap. Any replacement must preserve tenant and role filtering before retrieval and must be
evaluated for cross-tenant leakage.

## Regression gate

`backend/evaluation/golden_dataset.json` is evaluated in CI. The gate requires Recall@3 of at least
`0.95` and MRR of at least `0.85`. Expand the dataset with organization-specific terminology,
negative questions, ACL cases, and known failure modes before production approval.
