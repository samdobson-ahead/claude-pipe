# Architecture Generator from Discovery Docs

This utility reads discovery documents and asks Claude to produce a reference architecture with a Mermaid diagram and written explanation.
TLDR - the workflow is like this:
1. Add documents to discovery-docs directory
2. Run the generate_architecture.py script
3. Claude ingests the prompt in the script along with the docs in the discovery-docs folder.
4. Outputs a Mermaid arch diagram and written notes.

## Setup

1. Create and activate a Python 3.10+ environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure your API key:

   ```bash
   cp .env.example .env
   # Edit .env and set ANTHROPIC_API_KEY
   ```

4. Add discovery files to `discovery-docs/` (supported: .md, .txt, .pdf).

## Run

```bash
python generate_architecture.py \
  --docs-dir discovery-docs \
  --out-dir outputs \
  --model claude-3-7-sonnet-latest \
  --max-tokens 4000
```

Outputs:
- `outputs/diagram.mmd` — Mermaid diagram.
- `outputs/explanation.md` — Explanation, assumptions, constraints.

You can also set `CLAUDE_MODEL` in your `.env` to override the default model, for example:

```bash
CLAUDE_MODEL=claude-3-7-sonnet-latest
```
- `outputs/full_response.json` — Raw Claude response.

## Notes
- If no Mermaid block is returned, `diagram.mmd` will contain a placeholder comment.
- PDF extraction is best-effort via `pypdf`. For complex PDFs, consider converting to text/Markdown first.
