# GitHub Push Guide

## Automatic flow (if GitHub CLI is installed and authenticated)

```bash
git init
git add .
git commit -m "Initial commit: RAG internal knowledge assistant"
git branch -M main
gh repo create rag-internal-knowledge-assistant --public --source=. --remote=origin --push
```

## Manual flow

If `gh` is not authenticated:

```bash
git init
git add .
git commit -m "Initial commit: RAG internal knowledge assistant"
git branch -M main
git remote add origin <MY_GITHUB_REPO_URL>
git push -u origin main
```
