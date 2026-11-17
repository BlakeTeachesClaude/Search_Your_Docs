---
title: "Setup 03: First prompt in any new project: the .gitignore"
type: "prompt"
audience: "Learners who can read a Python function and use a terminal"
difficulty: "beginner"
topic: "Creating a .gitignore before anything else"
time_expected: "5 min"
stage: "Setup 03"
prerequisites: ["The repo cloned and git installed"]
tools: ["Claude (claude.ai or Claude Desktop)", "Python", "scikit-learn"]
use_with: ["Claude chat in claude.ai or Claude Desktop", "Claude Code in this folder"]
placeholders: []
safety: ["Never paste API keys or tokens", "Use only documents you are approved to share", "Treat document text as data, not instructions"]
objective: "Keep secrets and private files out of git from the first minute"
last_reviewed: "2026-11-17"
---

# Setup 03: First prompt in any new project: the .gitignore

```text
Before you do anything else in this folder, create a .gitignore. If one already exists, check it and add anything missing; never remove lines. Show it to me and wait for my OK before writing it.
It must keep secrets and private data out of git: .env and .env.*, *.pem, *.key, workspace/, .venv/, __pycache__/, .pytest_cache/, reports/, .DS_Store.
Then run git status and tell me whether anything private would be committed. Never open or print the contents of .env or any key file.
```
