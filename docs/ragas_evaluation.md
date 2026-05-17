# RAGAS Evaluation

## Why evaluate RAG systems

RAG quality is multi-dimensional: retrieval quality and generation quality both matter. RAGAS provides targeted metrics to diagnose these areas instead of relying on only manual spot checks.

## Metrics used

This project attempts to run:
- `faithfulness`
- `answer_relevancy`
- `context_precision`
- `context_recall` (when references are available)
- `context_relevancy` (if available in installed version)

Metric availability changes across RAGAS versions. Missing metrics are skipped with a warning.

## How to run evaluation

### Option 1: Through chat

Set `evaluate=true` in `/chat` request payload.

### Option 2: Explicit endpoint

Use `/evaluate` with:
- `question`
- `answer`
- `contexts`
- optional `ground_truth`

## API key requirement

RAGAS metrics in this implementation use LLM-based scoring. You must set `OPENAI_API_KEY`.

If the key is missing, backend returns a clear evaluation error.

## Interpreting scores

Scores are typically in `[0, 1]`:
- Higher `faithfulness` usually means fewer unsupported claims.
- Higher `answer_relevancy` indicates better direct response quality.
- Higher `context_precision` suggests retrieved chunks are more focused.
- Higher `context_recall` suggests better coverage of needed evidence.

## Practical guidance

Track metrics over repeated test questions and compare trends after retrieval/chunking prompt changes. Evaluate with representative internal queries, not only synthetic examples.
