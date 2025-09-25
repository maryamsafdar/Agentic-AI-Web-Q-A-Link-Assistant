from dataclasses import dataclass
from typing import List
from utils.text_utils import clean_text, chunk_text, extract_snippets, simple_rank_chunks
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# Try TF-IDF, else fallback to Jaccard
_TFIDF_OK = True
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:
    _TFIDF_OK = False

@dataclass
class ProcessResult:
    cleaned_text: str
    chunks: List[str]
    highlights: List[str]
    top_chunk_indices: List[int]
    method: str  # "tfidf" | "jaccard"

class ContentProcessorAgent:
    def __init__(self, max_chars: int = 1200, overlap: int = 150, top_k: int = 3):
        self.max_chars = max_chars
        self.overlap = overlap
        self.top_k = top_k

    def process(self, text: str, question: str) -> ProcessResult:
        cleaned = clean_text(text)
        chunks = chunk_text(cleaned, max_chars=self.max_chars, overlap=self.overlap)

        if not chunks:
            return ProcessResult(cleaned, [], [], [], method="jaccard")

        method = "tfidf"
        if _TFIDF_OK:
            try:
                corpus = chunks + [question]
                vec = TfidfVectorizer(stop_words="english")
                X = vec.fit_transform(corpus)
                q_vec, doc_vecs = X[-1], X[:-1]
                scores = cosine_similarity(doc_vecs, q_vec).ravel()
                order = scores.argsort()[::-1].tolist()
            except Exception:
                method = "jaccard"
                order = simple_rank_chunks(chunks, question)
        else:
            method = "jaccard"
            order = simple_rank_chunks(chunks, question)

        top_ids = order[: self.top_k]
        highlights = extract_snippets(cleaned, question, k=self.top_k)
        return ProcessResult(cleaned, chunks, highlights, top_ids, method)
