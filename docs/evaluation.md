# Evaluation and quality gates

## Two evaluation layers

The repository separates deterministic online indicators from the offline retrieval regression gate.
Neither calls a second evaluator LLM, avoiding additional evaluation-data egress and cost.

### Online deterministic indicators

`POST /evaluate` is admin-only and rate-limited. It calculates bounded lexical indicators for:

- faithfulness: answer content overlap with supplied contexts
- answer relevance: question/answer overlap
- context relevance: question/context overlap
- citation validity: whether cited indexes refer to supplied contexts
- context coverage: reference-answer terms covered by context, when a reference is supplied

These metrics are useful for repeatable diagnostics, not claims of human correctness. High lexical
overlap can still be wrong; low overlap can still be a valid paraphrase.

### Golden retrieval regression

`backend/scripts/run_retrieval_eval.py` loads the checked-in golden dataset and measures:

- Recall@3: fraction of cases where the expected document is in the first three results
- MRR: average reciprocal rank of the expected document

CI requires Recall@3 `>= 0.95` and MRR `>= 0.85`. The current small sample is a code-regression
fixture, not a production benchmark.

## Run locally

```bash
cd backend
python -m scripts.run_retrieval_eval
pytest --cov=app --cov-report=term-missing
```

To call the API as an admin:

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "When are incidents escalated?",
    "answer": "Critical incidents are escalated immediately [1].",
    "contexts": ["Critical incidents must be escalated immediately."],
    "ground_truth": "Critical incidents are escalated immediately."
  }' \
  https://api.example.com/evaluate
```

## Production evaluation program

Create a versioned, access-controlled dataset containing representative terminology, paraphrases,
negative/no-answer cases, stale/conflicting sources, injection attempts, multilingual needs, long
documents, and tenant/role isolation cases. Do not place production secrets or unapproved personal
data in CI fixtures.

Track at least retrieval Recall@K/MRR, answer correctness, groundedness, citation correctness,
abstention quality, latency, cost, and safety. Segment results by tenant/corpus type and measure
confidence intervals. Require human review for material policy, legal, medical, security, or other
high-impact answers.

## Change policy

Re-evaluate after changes to chunking, thresholds, prompts, model/provider, parsing, ACL filters, or
the corpus. Treat a quality improvement that weakens abstention, tenant isolation, privacy, latency,
or cost as a tradeoff requiring explicit review. Never tune on the final acceptance set alone.
