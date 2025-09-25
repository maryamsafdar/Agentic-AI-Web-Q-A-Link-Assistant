from typing import List, Optional
from dataclasses import dataclass

@dataclass
class ScrapeResult:
    url: str
    html: str
    text: str
    title: Optional[str] = None

@dataclass
class ProcessResult:
    cleaned_text: str
    chunks: List[str]
    highlights: List[str]
    top_chunk_indices: List[int]
    method: str  # "tfidf" | "jaccard"
   

    

@dataclass
class QnAResult:
    answer: str
    reasoning: Optional[str]
    provider: str 

@dataclass
class OrchestratorResult:
    url: str
    title: Optional[str]
    highlights: List[str]
    answer: str
    provider: str
    top_chunk_indices: List[int]
    total_chunks: int
