import os
from dataclasses import dataclass
from typing import List, Optional
from dataclass import QnAResult

class LLMUnavailableError(RuntimeError):
    pass

class QnAAgent:
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _openai_client(self):
        try:
            from openai import OpenAI
        except Exception as e:
            raise LLMUnavailableError("OpenAI SDK not installed") from e
        key = os.getenv("OPENAI_API_KEY")
        # If no key, we treat it as unavailable so the caller can fall back.
        if not key:
            raise LLMUnavailableError("OPENAI_API_KEY not configured")
        # OpenAI() will pull key from env by default, but we pass explicitly for clarity.
        return OpenAI(api_key=key)

    def _build_prompt(self, question: str, context_chunks: List[str]) -> str:
        context = "\n\n".join([f"[Context {i+1}] {c}" for i, c in enumerate(context_chunks)])
        return (
            "You are a helpful assistant. Use the context to answer the user's question.\n"
            "- If the answer is not in the context, say you are unsure.\n"
            "- Quote short snippets when useful.\n"
            "- Provide a brief 'Why this answer' rationale.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )

    def ask_llm(self, question: str, context_chunks: List[str]) -> QnAResult:
        """Single attempt. If anything goes wrong, raise LLMUnavailableError so caller can fall back."""
        client = self._openai_client()
        prompt = self._build_prompt(question, context_chunks)
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Answer concisely and cite relevant quotes."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
        except Exception as e:
            # Treat any runtime failure as LLM unavailable to trigger fallback
            raise LLMUnavailableError(f"OpenAI call failed: {e}") from e

        content = resp.choices[0].message.content.strip()
        return QnAResult(answer=content, reasoning=None, provider=f"openai:{self.model}")

    def ask_fallback(self, question: str, context_chunks: List[str]) -> QnAResult:
        import re
        q_words = set(re.findall(r"\w+", question.lower()))
        def score(t):
            t_words = set(re.findall(r"\w+", t.lower()))
            return len(q_words & t_words)
        if not context_chunks:
            return QnAResult(answer="I couldn't find content to answer this.", reasoning=None, provider="fallback")
        best = max(context_chunks, key=score)
        extract = best[:800]
        return QnAResult(
            answer=(
                "(Heuristic extract — set OPENAI_API_KEY for LLM answers)\n\n"
                f"Likely relevant: {extract}"
            ),
            reasoning="Selected the most overlapping chunk.",
            provider="fallback"
        )

    def answer(self, question: str, context_chunks: List[str]) -> QnAResult:
        """Try LLM once; on *any* failure, gracefully fall back to heuristic."""
        try:
            return self.ask_llm(question, context_chunks)
        except Exception:
            return self.ask_fallback(question, context_chunks)
