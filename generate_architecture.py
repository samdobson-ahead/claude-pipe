#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv

# Optional PDF extraction
try:
    from pypdf import PdfReader  # lightweight and pure-python
except Exception:
    PdfReader = None

# Anthropic SDK
try:
    from anthropic import Anthropic
except Exception:
    Anthropic = None


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")


def read_pdf_file(path: Path) -> str:
    if PdfReader is None:
        return f"[PDF parsing unavailable. Install pypdf to extract text for {path.name}.]\n"
    try:
        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages):
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        return "\n\n".join(pages)
    except Exception as e:
        return f"[Failed to read PDF {path.name}: {e}]\n"


def load_docs(docs_dir: Path) -> List[Tuple[str, str]]:
    exts = {".md", ".txt", ".pdf"}
    docs: List[Tuple[str, str]] = []
    if not docs_dir.exists():
        return docs
    for p in sorted(docs_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in exts:
            if p.suffix.lower() == ".pdf":
                content = read_pdf_file(p)
            else:
                content = read_text_file(p)
            docs.append((str(p.relative_to(docs_dir)), content.strip()))
    return docs


def build_prompt(docs: List[Tuple[str, str]]) -> str:
    # Instruction modeled after the example the user provided.
    header = (
        "You are an expert solution architect.\n"
        "You will be provided with discovery materials (e.g., SOWs, Q&A transcripts, PoCs, architecture notes).\n"
        "Infer the client's objectives, constraints, platforms, and preferences strictly from the documents provided.\n"
        "Your task is to:\n"
        "1. Generate a validated reference architecture tailored to the environment and goals implied by the discovery docs.\n"
        "2. Provide BOTH a Mermaid diagram (in a fenced ```mermaid code block) and a written explanation.\n"
        "3. Highlight assumptions and constraints you needed to make when designing the architecture, citing the missing info.\n"
        "4. Ensure the output is practical and buildable, and align with best practices appropriate to the identified stack (e.g., AWS/Azure/GCP/on‑prem; Kubernetes/OpenShift/AKS/GKE; data/ML/app).\n\n"
        "Output format:\n"
        "- Start with a single fenced ```mermaid block for the diagram, nothing else interleaved.\n"
        "- Follow with sections: Explanation, Assumptions, Constraints.\n"
    )

    parts = [header, "\n---\n", "Discovery Documents (verbatim excerpts):\n"]
    for name, content in docs:
        parts.append(f"\n### {name}\n\n{content}\n")
    return "".join(parts)


def parse_mermaid_blocks(text: str) -> Tuple[str, str]:
    """Return (mermaid_code, remainder_markdown)."""
    import re

    fence_re = re.compile(r"```\s*mermaid\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
    m = fence_re.search(text)
    if not m:
        return "", text
    mermaid = m.group(1).strip()
    remainder = text[: m.start()] + text[m.end() :]
    return mermaid, remainder.strip()


def call_claude(prompt: str, model: str, max_tokens: int) -> dict:
    if Anthropic is None:
        raise RuntimeError(
            "anthropic package not installed. Install dependencies from requirements.txt."
        )

    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Create a .env with ANTHROPIC_API_KEY=..."
        )

    client = Anthropic(api_key=api_key)

    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0.2,
        system=(
            "Be precise, practical, and production-oriented. Infer platforms, services, and patterns strictly from the provided discovery materials. "
            "Apply industry best practices appropriate to whatever stack the documents imply (cloud/on‑prem, any provider, any workload). "
            "When information is missing, state reasonable assumptions explicitly. "
            "Return a single Mermaid diagram first (in a fenced triple-backtick block), then concise sections: Explanation, Assumptions, Constraints."
        ),
        messages=[{"role": "user", "content": prompt}],
    )

    # Convert to plain text for ease of parsing
    def to_text(message) -> str:
        parts = []
        for c in message.content:
            if c["type"] == "text":
                parts.append(c["text"])
        return "".join(parts)

    full_text = to_text(msg)
    return {"raw": msg.model_dump(), "text": full_text}


def write_outputs(out_dir: Path, response: dict) -> Tuple[Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    text = response.get("text", "")
    mermaid, remainder = parse_mermaid_blocks(text)

    diagram_path = out_dir / "diagram.mmd"
    explanation_path = out_dir / "explanation.md"
    json_path = out_dir / "full_response.json"

    diagram_path.write_text(mermaid or "// No mermaid block found\n", encoding="utf-8")
    explanation_path.write_text(remainder or text, encoding="utf-8")
    json_path.write_text(json.dumps(response["raw"], indent=2), encoding="utf-8")

    return diagram_path, explanation_path, json_path


def main():
    parser = argparse.ArgumentParser(description="Generate architecture from discovery docs via Claude.")
    parser.add_argument("--docs-dir", default="discovery-docs", type=str)
    parser.add_argument("--out-dir", default="outputs", type=str)
    parser.add_argument("--model", default="claude-3-5-sonnet-20240620", type=str)
    parser.add_argument("--max-tokens", default=4000, type=int)
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    out_dir = Path(args.out_dir)

    docs = load_docs(docs_dir)
    if not docs:
        print(f"No discovery docs found in {docs_dir}. Add .md/.txt/.pdf files and re-run.")

    prompt = build_prompt(docs)

    print("Calling Claude... (this may take ~10-20s)")
    response = call_claude(prompt, args.model, args.max_tokens)

    diagram_path, explanation_path, json_path = write_outputs(out_dir, response)
    print("Saved:")
    print(f"- diagram: {diagram_path}")
    print(f"- explanation: {explanation_path}")
    print(f"- full response JSON: {json_path}")


if __name__ == "__main__":
    main()
