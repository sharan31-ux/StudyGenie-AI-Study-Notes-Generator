"""
Generate MCQ quizzes and flashcards from a study summary using Gemini,
with defensive JSON extraction since LLMs occasionally wrap output in
markdown fences or add stray commentary.
"""

import json
import re
from typing import List, Dict, Any

from .gemini_client import GeminiClient


def _extract_json(raw: str):
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1)

    return json.loads(cleaned)


def generate_mcq_quiz(client: GeminiClient, summary_text: str, num_questions: int = 8) -> List[Dict[str, Any]]:
    prompt = f"""Create {num_questions} multiple-choice questions (MCQs) to test understanding
of the study material below. Each question must have exactly 4 options, exactly one correct
answer, and a short (1-2 sentence) explanation of why that answer is correct.

Return ONLY valid JSON — a list of objects with this EXACT schema, no markdown fences,
no extra text before or after:
[
  {{
    "question": "string",
    "options": ["string", "string", "string", "string"],
    "answer_index": 0,
    "explanation": "string"
  }}
]

STUDY MATERIAL:
\"\"\"
{summary_text}
\"\"\"
"""
    raw = client.generate(prompt, temperature=0.5)
    try:
        data = _extract_json(raw)
        if isinstance(data, list):
            # Basic validation / cleanup so malformed items don't break the UI.
            cleaned = []
            for item in data:
                if (
                    isinstance(item, dict)
                    and isinstance(item.get("options"), list)
                    and len(item["options"]) >= 2
                    and "question" in item
                ):
                    item["answer_index"] = int(item.get("answer_index", 0)) if str(
                        item.get("answer_index", 0)
                    ).isdigit() else 0
                    cleaned.append(item)
            return cleaned
    except Exception:
        pass
    return []


def generate_flashcards(client: GeminiClient, summary_text: str, num_cards: int = 10) -> List[Dict[str, str]]:
    prompt = f"""Create {num_cards} flashcards from the study material below.
Each flashcard has a short "front" (a term/question, under 12 words) and a concise
"back" (the answer/definition, 1-3 sentences).

Return ONLY valid JSON — a list of objects with this EXACT schema, no markdown fences,
no extra text before or after:
[
  {{"front": "string", "back": "string"}}
]

STUDY MATERIAL:
\"\"\"
{summary_text}
\"\"\"
"""
    raw = client.generate(prompt, temperature=0.5)
    try:
        data = _extract_json(raw)
        if isinstance(data, list):
            cleaned = [
                item for item in data
                if isinstance(item, dict) and item.get("front") and item.get("back")
            ]
            return cleaned
    except Exception:
        pass
    return []
