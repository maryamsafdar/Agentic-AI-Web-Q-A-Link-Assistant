from dataclasses import dataclass
from typing import Dict,Optional, List,Any
from agents.web_scrapper import WebScraperAgent
from agents.contentProcessor import ContentProcessorAgent
from agents.qna_agent import QnAAgent
from dataclass import OrchestratorResult

class OrchestratorAgent:
    def __init__(self, *, top_k: int = 3, max_chars: int = 1200, overlap: int = 150, model: Optional[str] = None):
        self.scraper = WebScraperAgent()
        self.processor = ContentProcessorAgent(top_k=top_k, max_chars=max_chars, overlap=overlap)
        self.qna = QnAAgent(model=model)

    def run(self, url: str, question: str) -> OrchestratorResult:
        sres = self.scraper.fetch(url)
        pres = self.processor.process(sres.text, question)
        context = [pres.chunks[i] for i in pres.top_chunk_indices]
        qres = self.qna.answer(question, context)
        return OrchestratorResult(
            url=sres.url,
            title=sres.title,
            highlights=pres.highlights,
            answer=qres.answer,
            provider=qres.provider,
            top_chunk_indices=pres.top_chunk_indices,
            total_chunks=len(pres.chunks),
        )

    # NEW: summarize current page using top chunks as context
    def summarize(self, url: str, style: str = "bullet-5") -> Dict[str, Any]:
        prompt = "Summarize the page in 5 concise bullet points." if style == "bullet-5" else "Summarize this page briefly."
        sres = self.scraper.fetch(url)
        pres = self.processor.process(sres.text, prompt)
        context = [pres.chunks[i] for i in pres.top_chunk_indices]
        qres = self.qna.answer(prompt, context)
        return {
            "url": sres.url,
            "title": sres.title,
            "summary": qres.answer,
            "provider": qres.provider,
            "top_chunk_indices": pres.top_chunk_indices,
            "highlights": pres.highlights,
            "total_chunks": len(pres.chunks),
        }

    # NEW: answer multiple questions against the same URL
    def answer_many(self, url: str, questions: List[str]) -> List[OrchestratorResult]:
        results: List[OrchestratorResult] = []
        # Process once using the first question (for ranking); reuse for others for speed.
        first_q = questions[0] if questions else ""
        sres = self.scraper.fetch(url)
        pres = self.processor.process(sres.text, first_q or "extract key facts")
        base_context = [pres.chunks[i] for i in pres.top_chunk_indices]
        for q in questions:
            # Optionally, you could re-rank per question. Here we use base_context for speed.
            qres = self.qna.answer(q, base_context)
            results.append(OrchestratorResult(
                url=sres.url,
                title=sres.title,
                highlights=pres.highlights,
                answer=qres.answer,
                provider=qres.provider,
                top_chunk_indices=pres.top_chunk_indices,
                total_chunks=len(pres.chunks),
            ))
        return results