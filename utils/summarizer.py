"""
Map-reduce summarization for large PDFs.

MAP  : split the document into overlapping chunks and summarize each
       chunk independently (keeps every chunk within a safe context size
       and lets chunks be processed even if the doc is huge).
REDUCE: combine the chunk-level summaries into one cohesive final
       summary, then derive key points from that final summary.
"""

import json
import re
from typing import List

from .gemini_client import GeminiClient


def chunk_text(text: str, max_chars: int = 6000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks so each Gemini call stays small and fast."""
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        chunks.append(text[start:end])
        if end >= length:
            break
        start = end - overlap
    return [c for c in chunks if c.strip()]


def map_summarize_chunk(client: GeminiClient, chunk: str, idx: int, total: int) -> str:
    """MAP step: summarize a single chunk, preserving facts/definitions/formulas."""
    prompt = f"""You are an expert academic study assistant helping a student revise.
Summarize the following excerpt (part {idx + 1} of {total}) from a study document.
Preserve every important fact, definition, formula, name, and concept.
Be concise but complete. Return plain text only — no markdown headers, no bullet symbols.

EXCERPT:
\"\"\"
{chunk}
\"\"\"
"""
    return client.generate(prompt, temperature=0.3)


def reduce_summaries(client: GeminiClient, chunk_summaries: List[str], style: str = "detailed") -> str:
    """REDUCE step: merge chunk summaries into one cohesive final summary."""
    combined = "\n\n".join(f"[Part {i + 1}]\n{s}" for i, s in enumerate(chunk_summaries))

    length_hint = {
        "brief": "in about 150-200 words",
        "detailed": "in about 350-500 words",
        "comprehensive": "in about 600-900 words",
    }.get(style, "in about 350-500 words")

    prompt = f"""Combine the following partial summaries of ONE document into a single,
well-organized study summary, written {length_hint}.
Remove redundancy, keep a logical flow of ideas, and write it as if explaining
the topic directly to a student.
Do not mention "parts", "excerpts", or the summarization process itself.

FORMAT — follow this exactly:
- Plain flowing prose only, organized into short paragraphs (3-5 sentences each).
- Separate paragraphs with exactly ONE blank line. No blank line within a paragraph.
- Do NOT use markdown headers (no #, ##, ###).
- Do NOT use bullet points, numbered lists, or dashes to start a line.
- Do NOT use bold/italic markdown (no **text**, no *text*).
- If the source material includes figures, prices, or breakdowns, weave them into
  the sentences of a paragraph instead of listing them (e.g. "the base price was
  X, with Y in tax, bringing the total to Z") rather than as a list.
- Output nothing but the summary text itself — no title, no labels, no preamble.

PARTIAL SUMMARIES:
\"\"\"
{combined}
\"\"\"
"""
    return client.generate(prompt, temperature=0.4)


def generate_key_points(client: GeminiClient, full_summary: str, num_points: int = 10) -> List[str]:
    """Extract the most important, exam-ready bullet points from the final summary."""
    prompt = f"""From the study summary below, extract the {num_points} most important key points
a student must remember before an exam. Each point should be a single, self-contained sentence.

Return ONLY a JSON array of strings. No markdown code fences, no extra commentary.
Example format: ["Point one.", "Point two."]

SUMMARY:
\"\"\"
{full_summary}
\"\"\"
"""
    raw = client.generate(prompt, temperature=0.3)
    return _safe_json_list(raw)


def _safe_json_list(raw: str) -> List[str]:
    """Robustly parse a JSON list from a model response, with a plain-text fallback."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return [str(item).strip() for item in data if str(item).strip()]
    except Exception:
        pass

    # Fallback: treat each non-empty line as a point.
    lines = [l.strip("-•*\t ") for l in raw.split("\n") if l.strip()]
    return lines[:15]
