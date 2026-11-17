# Build a local RAG with Claude

60-minute instructor-led lab. Use Python 3.10+ and the fictional documents in this folder. No external search service or database.

## Setup (about 10 minutes, together)
```sh
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python scripts/new_workspace.py    # creates workspace/ with documents, starter my_rag.py and check.py
cd workspace
python check.py 0                  # environment check: expect PASS for Python, scikit-learn, anthropic, documents
```
**Collect your documents.** The default is three fictional policy documents. To use your own, point the setup at one folder of approved `.md` or `.txt` files: `python scripts/new_workspace.py --docs ~/approved-folder`. Hidden files, symlinks, PDFs and files over 1 MB are skipped and listed.

You will write the code yourself in `workspace/my_rag.py`; the finished reference solution is `rag.py` at the repo root. To see the reference work first (optional):

```sh
python rag.py "What is the hotel reimbursement limit?"
```

Retrieval works offline after the packages are installed. `--answer` sends the selected passages and question to Claude over the network. Use only approved data. Set `ANTHROPIC_API_KEY` securely in your environment and `ANTHROPIC_MODEL` to a model available to your account (for example `claude-haiku-5-5` if available). Then:
```sh
python rag.py "What is the hotel reimbursement limit?" --answer
```

The answer should reference `travel.md#1` and $180 before taxes. Test `How many vacation days do employees receive?` and an unsupported question like `Who won the 1980 Olympics?`. The latter should find no evidence with the included fixture corpus. Lexical retrieval does not guarantee relevance, and generation can still be wrong. Verify cited evidence.

## Live code-along
Open `workspace/my_rag.py`. It already calls every function from `main()`, so each function you write runs as soon as you save it. Four steps, each ending with a run and a self-check:

1. **Load and chunk.** Write `load_chunks`, keep `STEP = 1`, run `python my_rag.py` (expect `3 chunks` for the sample documents), then `python check.py 1`.
2. **Build the index.** Write `build_index`, set `STEP = 2`, run, then `python check.py 2`. Expect `index shape: (3, ...)`.
3. **Retrieve.** Write `retrieve`, set `STEP = 3`, run, then `python check.py 3`. The hotel question should return `travel.md#1` first, and a question the documents cannot answer should return nothing.
4. **Ground the answer.** Write `answer`, run `python check.py 4` (works offline with a stand-in for Claude), then set `STEP = 4` and run `python my_rag.py` with `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` set.

The code for each step is on the matching slide in `deck/index.html`. `rag.py` is the finished reference that wires all four together behind a command line (`--folder PATH` points it at a selected folder of approved text and Markdown documents, not an indiscriminate scan of personal Documents; `--answer` adds the Claude call). Use only approved documents; retrieved passages are sent to Claude in step 4.

## Checkpoint
1. Run an in-domain question and show the source.
2. Explain why we retrieve before calling Claude.
3. Change the question and predict the source before running it.

## Extension lane (choose one)
- Add chunk overlap and compare retrieval on a passage split across boundaries.
- Replace TF-IDF with local dense embeddings. Compare synonym queries against the baseline.
- Add PDF text extraction and preserve page numbers.
- Add a five-question evaluation with expected sources and an unanswerable case. Measure recall@3 and answer groundedness separately.
- Add a simple interactive CLI, cache the index and update it when documents change.

Acceptance criteria: show a working improvement, explain why it matters, and test against the baseline including an unsupported question.

## Instructor support lane
Ask the learner to run each component separately; inspect file loading, chunk content, fitted vocabulary, query vector and scores. Use pair debugging or a short small-group mini-lesson, then have them rerun independently. Offer the reference solution as scaffold, not as the assessment. Rejoin both lanes for a share-out and a final evidence-backed question.

References: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html ; https://platform.claude.com/docs/en/api/python/messages/create

## Testing and go/no-go
```sh
python -m pip install -r requirements-dev.txt
make test          # offline regression suite (Claude API mocked)
make smoke         # smoke suite; writes reports/smoke-report.md with GO / CONDITIONAL GO / NO-GO
make smoke-live    # adds a real Claude API call (needs ANTHROPIC_API_KEY and ANTHROPIC_MODEL)
```
NO-GO means a required check failed. CONDITIONAL GO means required checks passed but something was skipped, failed optionally, or a manual sign-off in `compat/verified.json` (Claude API, Claude Code, Claude Desktop) is missing or older than 60 days.

## HTML deck
Open `deck/index.html` in any browser (no server or internet needed). Arrow keys navigate, F fullscreen, O slide overview; print to PDF for handouts. Edit the content in `scripts/build_deck.py`, then run `python scripts/build_deck.py`. A test fails if the deck is out of date.

## Using Claude with this repo
`CLAUDE.md` tells Claude to coach learners (hints and `check.py`, not the solution) and to keep documents and keys safe. `.claude/settings.json` pre-approves the lab and test commands, asks before installs, commits and live API runs, and blocks reading `.env`, network fetches and destructive commands. Claude Code reads both automatically; verify how Claude Desktop applies them before teaching and record it in `compat/verified.json`.
