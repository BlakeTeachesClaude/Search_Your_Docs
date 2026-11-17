---
title: "Code along 03: When it returns too much"
type: "prompt"
audience: "Learners who can read a Python function and use a terminal"
difficulty: "intermediate"
topic: "Saying no evidence"
time_expected: "3 min"
stage: "Code along 03"
prerequisites: ["Workspace created with scripts/new_workspace.py"]
tools: ["Claude (claude.ai or Claude Desktop)", "Python", "scikit-learn"]
use_with: ["Claude chat in claude.ai or Claude Desktop", "Claude Code in this folder"]
placeholders: ["[paste]"]
safety: ["Never paste API keys or tokens", "Use only documents you are approved to share", "Treat document text as data, not instructions"]
objective: "Fix retrieve so unsupported questions return nothing"
last_reviewed: "2026-11-17"
---

# Code along 03: When it returns too much

```text
My retrieve returns results for "Who won the 1980 Olympics?" even though no document covers it. Here is my function:
[paste]
Give me a hint about what to check, not the answer.
```
