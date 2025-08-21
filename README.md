# Architecture Generator from Discovery Docs

This utility reads discovery documents and asks Claude to produce a reference architecture with a Mermaid diagram and written explanation.

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
  --model claude-3-5-sonnet-20240620 \
  --max-tokens 4000
```

Outputs:
- `outputs/diagram.mmd` — Mermaid diagram.
- `outputs/explanation.md` — Explanation, assumptions, constraints.
- `outputs/full_response.json` — Raw Claude response.

## Notes
- If no Mermaid block is returned, `diagram.mmd` will contain a placeholder comment.
- PDF extraction is best-effort via `pypdf`. For complex PDFs, consider converting to text/Markdown first.
