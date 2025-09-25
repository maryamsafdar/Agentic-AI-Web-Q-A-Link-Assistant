# import re
# from typing import List

# def clean_text(text: str) -> str:
#     text = re.sub(r"\s+", " ", text or "").strip()
#     return text

# def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150, max_total_chars: int = 600_000, max_chunks: int = 200) -> List[str]:
#     """Chunk text into overlapping windows with strict caps to prevent MemoryError.

#     - max_total_chars: hard limit on how many characters we consider from the start of the document
#     - max_chunks: hard limit on number of chunks produced
#     """
#     text = clean_text(text or "")
#     if not text:
#         return []
#     # Limit the total size we process to avoid huge memory usage
#     if len(text) > max_total_chars:
#         text = text[:max_total_chars]

#     if len(text) <= max_chars:
#         return [text]

#     # Ensure overlap is smaller than max_chars
#     overlap = min(overlap, max(0, max_chars // 3))

#     chunks = []
#     start = 0
#     # stride ensures we don't create too many chunks
#     stride = max(1, max_chars - overlap)

#     # Compute an upper bound on iterations
#     safety_iters = 0
#     while start < len(text) and len(chunks) < max_chunks:
#         end = min(len(text), start + max_chars)
#         chunks.append(text[start:end])
#         start += stride
#         safety_iters += 1
#         if safety_iters > max_chunks + 5:
#             break

#     # De-duplicate near-identical trailing bits
#     deduped = []
#     for c in chunks:
#         c2 = c.strip()
#         if not deduped or c2 != deduped[-1]:
#             deduped.append(c2)
#     return deduped

# def top_k_indices(scores, k=3):
#     scores = list(scores)
#     pairs = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
#     return [i for i,_ in pairs[:k]]

# def extract_snippets(text: str, question: str, k: int = 3):
#     """Return k relevant 240-char snippets using a simple word-overlap proxy, for highlighting."""
#     text = clean_text(text)
#     sentences = re.split(r'(?<=[.!?])\s+', text)
#     q_words = set(re.findall(r"\w+", question.lower()))
#     scored = []
#     for s in sentences:
#         s_words = set(re.findall(r"\w+", s.lower()))
#         jacc = len(q_words & s_words) / (len(q_words | s_words) or 1)
#         scored.append((jacc, s))
#     best = [s for _,s in sorted(scored, key=lambda x: x[0], reverse=True)[:k]]
#     return [s[:240] for s in best]

import re
from typing import List

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def chunk_text(
    text: str,
    max_chars: int = 1200,
    overlap: int = 150,
    max_total_chars: int = 600_000,
    max_chunks: int = 200
) -> List[str]:
    text = clean_text(text or "")
    if not text:
        return []
    if len(text) > max_total_chars:
        text = text[:max_total_chars]
    if len(text) <= max_chars:
        return [text]

    overlap = min(overlap, max(0, max_chars // 3))
    stride = max(1, max_chars - overlap)

    chunks, start = [], 0
    while start < len(text) and len(chunks) < max_chunks:
        end = min(len(text), start + max_chars)
        chunks.append(text[start:end])
        start += stride

    # De-dupe trailing near-identicals
    deduped = []
    for c in chunks:
        c2 = c.strip()
        if not deduped or c2 != deduped[-1]:
            deduped.append(c2)
    return deduped

def extract_snippets(text: str, question: str, k: int = 3):
    text = clean_text(text)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    q_words = set(re.findall(r"\w+", (question or "").lower()))
    scored = []
    for s in sentences:
        s_words = set(re.findall(r"\w+", s.lower()))
        denom = len(q_words | s_words) or 1
        scored.append((len(q_words & s_words) / denom, s))
    best = [s for _, s in sorted(scored, key=lambda x: x[0], reverse=True)[:k]]
    return [s[:240] for s in best]

def simple_rank_chunks(chunks: List[str], question: str) -> List[int]:
    q_words = set(re.findall(r"\w+", (question or "").lower()))
    scored = []
    for i, ch in enumerate(chunks):
        w = set(re.findall(r"\w+", ch.lower()))
        denom = len(q_words | w) or 1
        scored.append((len(q_words & w) / denom, i))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [i for _, i in scored]
