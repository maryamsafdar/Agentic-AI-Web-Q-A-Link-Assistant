import os
import json
import time
import traceback
from dataclasses import asdict  # ✅ for dict-ifying dataclasses
import streamlit as st
from dotenv import load_dotenv
from orchestrator import OrchestratorAgent

# ---------- Boot ----------
load_dotenv()
st.set_page_config(page_title="Day 5 — Agentic Q&A Dashboard", page_icon="🧪", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
:root {
  --grad: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 40%, #ec4899 100%);
  --panel: rgba(255,255,255,0.03);
  --border: rgba(255,255,255,0.08);
  --muted: #9aa4af;
}
html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1100px 760px at 8% -10%, rgba(14,165,233,0.12), transparent 60%),
              radial-gradient(1200px 900px at 100% 0%, rgba(236,72,153,0.10), transparent 60%);
}
.hero {
  padding: 20px 22px; border-radius: 16px; background: var(--grad); color: #fff !important;
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}
.hero h1, .hero p { color: #fff !important; margin: 0 !important; }
.card { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 16px; }
.badge {
  display:inline-flex; gap:8px; align-items:center; padding:6px 10px; border-radius:10px;
  border:1px solid var(--border); background:rgba(255,255,255,0.04); font-size:0.92rem;
}
.snip {
  border-left: 3px solid #0ea5e9; background: rgba(255,255,255,0.03);
  padding: 10px 12px; border-radius: 8px; margin-bottom: 8px;
}
.small { color: var(--muted); font-size: 0.92rem; }
textarea[placeholder*="Enter one question per line"] { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <h1>Day 5 — Agentic Web Link Q&A</h1>
  <p>Scrape → Clean → Highlight → Answer (LLM with fallback) • Multi-question • Summary • Caching</p>
</div>
""", unsafe_allow_html=True)
st.write("")

# ---------- Sidebar ----------
api_key_status = "✅ Found" if os.getenv("OPENAI_API_KEY") else "⚠️ Missing (using fallback)"
st.sidebar.header("⚙️ Settings")
st.sidebar.write(f"LLM: {api_key_status}  |  Model: `{os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}`")
top_k = st.sidebar.slider("Top-K chunks", 1, 8, 3)
max_chars = st.sidebar.slider("Chunk size (chars)", 600, 2400, 1200, step=100)
overlap = st.sidebar.slider("Chunk overlap (chars)", 50, 300, 150, step=25)
show_debug = st.sidebar.toggle("Show Debug tab", value=False)
st.sidebar.markdown("---")
if st.sidebar.button("🧹 Clear History", use_container_width=True):
    st.session_state.pop("history", None)
    st.toast("History cleared.", icon="🧽")

# ---------- Cache layer (return dicts for pickling) ----------
@st.cache_data(show_spinner=False, ttl=60*15)
def cached_orchestrator_run(url: str, question: str, _top_k: int, _max_chars: int, _overlap: int):
    from dataclasses import asdict
    orch = OrchestratorAgent(top_k=_top_k, max_chars=_max_chars, overlap=_overlap)
    res = orch.run(url, question)          # dataclass
    plain = asdict(res)                    # dict
    # ✅ force JSON-serializable only
    return json.loads(json.dumps(plain))


@st.cache_data(show_spinner=False, ttl=60*15)
def cached_summarize(url: str, _top_k: int, _max_chars: int, _overlap: int):
    orch = OrchestratorAgent(top_k=_top_k, max_chars=_max_chars, overlap=_overlap)
    summary = orch.summarize(url)          # dict (but make it extra-safe)
    return json.loads(json.dumps(summary))  # ✅ JSON round-trip


@st.cache_data(show_spinner=False, ttl=60*15)
def cached_answer_many(url: str, questions: tuple, _top_k: int, _max_chars: int, _overlap: int):
    from dataclasses import asdict
    orch = OrchestratorAgent(top_k=_top_k, max_chars=_max_chars, overlap=_overlap)
    results = orch.answer_many(url, list(questions))   # list[dataclass]
    plain_list = [asdict(r) for r in results]          # list[dict]
    return json.loads(json.dumps(plain_list))          # ✅ JSON round-trip


# ---------- Session ----------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- Inputs ----------
st.markdown("#### 🔍 Ask about a web page")
c1, c2 = st.columns([1.6, 1.4], gap="large")
with c1:
    url = st.text_input("Web page URL", placeholder="https://example.com/article")
with c2:
    mode = st.radio("Mode", ["Single question", "Multiple questions", "Summarize page"], horizontal=True)

if mode == "Single question":
    question = st.text_area("Your question", placeholder="Ask something specific about the page...", height=120)
elif mode == "Multiple questions":
    questions_raw = st.text_area("Questions (one per line)", placeholder="Enter one question per line", height=140)
else:
    summary_style = st.selectbox("Summary style", ["bullet-5", "short-paragraph"], index=0)

go = st.button("▶️ Run", type="primary")

# ---------- Tabs ----------
tabs = ["📋 Overview", "✅ Answers", "🔎 Highlights", "🧩 Context"]
if show_debug:
    tabs.append("🧪 Debug")
t_over, t_ans, t_high, t_ctx, *rest = st.tabs(tabs)

def log_history(entry):
    st.session_state.history.insert(0, entry)

def export_buttons(payload_dict, col1, col2):
    with col1:
        st.download_button("⬇️ Download (.txt)", data=payload_dict.get("text_export", ""),
                           file_name="result.txt", mime="text/plain", use_container_width=True)
    with col2:
        st.download_button("⬇️ Download (.json)", data=json.dumps(payload_dict, ensure_ascii=False, indent=2),
                           file_name="result.json", mime="application/json", use_container_width=True)

# ---------- Run ----------
if go:
    if not url:
        st.error("Please provide a URL.")
    else:
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            if mode == "Summarize page":
                summary = cached_summarize(url, top_k, max_chars, overlap)
                with t_over:
                    if summary.get("title"):
                        st.subheader(summary["title"])
                    st.markdown(f"<div class='badge'>🔗 URL <span class='small'>({summary['url'][:48]}…)</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='badge'>🤖 Provider <code>{summary['provider']}</code></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='badge'>🕒 {timestamp}</div>", unsafe_allow_html=True)
                    st.markdown("### 🧾 Summary")
                    st.write(summary["summary"])
                    ce1, ce2 = st.columns(2)
                    export_buttons(
                        {
                            "url": summary["url"], "title": summary["title"],
                            "summary": summary["summary"], "provider": summary["provider"],
                            "top_chunk_indices": summary["top_chunk_indices"],
                            "highlights": summary["highlights"], "total_chunks": summary["total_chunks"],
                            "text_export": summary["summary"]
                        },
                        ce1, ce2
                    )
                with t_high:
                    st.markdown("##### Top snippets")
                    for i, h in enumerate(summary.get("highlights", []), 1):
                        st.markdown(f"<div class='snip'><b>{i}.</b> {h}</div>", unsafe_allow_html=True)
                with t_ctx:
                    st.write(f"Top chunk indices: {summary['top_chunk_indices']} / total {summary['total_chunks']}")

                log_history({
                    "time": timestamp, "mode": "summary", "url": summary["url"], "title": summary["title"],
                    "provider": summary["provider"]
                })

            elif mode == "Multiple questions":
                qs = [q.strip() for q in (questions_raw or "").splitlines() if q.strip()]
                if not qs:
                    st.error("Please enter at least one question.")
                else:
                    results = cached_answer_many(url, tuple(qs), top_k, max_chars, overlap)  # list[dict]
                    first = results[0]
                    with t_over:
                        if first.get("title"):
                            st.subheader(first["title"])
                        st.markdown(f"<div class='badge'>🔗 URL <span class='small'>({first['url'][:48]}…)</span></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='badge'>🤖 Provider <code>{first['provider']}</code></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='badge'>🧩 Context {first['top_chunk_indices']} / {first['total_chunks']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='badge'>🕒 {timestamp}</div>", unsafe_allow_html=True)

                    with t_ans:
                        st.markdown("### Answers")
                        for i, r in enumerate(results, 1):
                            with st.expander(f"{i}. {qs[i-1]}", expanded=(i==1)):
                                st.write(r["answer"])

                        ce1, ce2 = st.columns(2)
                        export_buttons(
                            {
                                "mode": "multi",
                                "url": first["url"],
                                "title": first["title"],
                                "provider": first["provider"],
                                "questions": qs,
                                "answers": [r["answer"] for r in results],
                                "top_chunk_indices": first["top_chunk_indices"],
                                "total_chunks": first["total_chunks"],
                                "text_export": "\n\n".join([f"Q{i+1}: {q}\nA{i+1}: {results[i]['answer']}" for i, q in enumerate(qs)])
                            },
                            ce1, ce2
                        )

                    with t_high:
                        for i, h in enumerate(first.get("highlights", []), 1):
                            st.markdown(f"<div class='snip'><b>{i}.</b> {h}</div>", unsafe_allow_html=True)
                    with t_ctx:
                        st.write(f"Top chunk indices: {first['top_chunk_indices']} / total {first['total_chunks']}")

                    log_history({
                        "time": timestamp, "mode": "multi", "url": first["url"], "title": first["title"], "provider": first["provider"],
                        "num_questions": len(qs)
                    })

            else:  # Single question
                res = cached_orchestrator_run(url, question, top_k, max_chars, overlap)  # dict

                with t_over:
                    if res.get("title"):
                        st.subheader(res["title"])
                    st.markdown(f"<div class='badge'>🔗 URL <span class='small'>({res['url'][:48]}…)</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='badge'>🤖 Provider <code>{res['provider']}</code></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='badge'>🧩 Context {res['top_chunk_indices']} / {res['total_chunks']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='badge'>🕒 {timestamp}</div>", unsafe_allow_html=True)

                with t_ans:
                    st.markdown("### ✅ Answer")
                    st.write(res["answer"])
                    ce1, ce2 = st.columns(2)
                    export_buttons(
                        {
                            "mode": "single",
                            "url": res["url"], "title": res["title"], "provider": res["provider"],
                            "top_chunk_indices": res["top_chunk_indices"], "total_chunks": res["total_chunks"],
                            "highlights": res["highlights"],
                            "answer": res["answer"],
                            "text_export": res["answer"]
                        },
                        ce1, ce2
                    )

                with t_high:
                    st.markdown("##### Top snippets")
                    if res.get("highlights"):
                        for i, h in enumerate(res["highlights"], 1):
                            st.markdown(f"<div class='snip'><b>{i}.</b> {h}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("No highlight snippets produced.")

                with t_ctx:
                    st.write(f"Top chunk indices: {res['top_chunk_indices']} / total {res['total_chunks']}")

                log_history({
                    "time": timestamp, "mode": "single", "url": res["url"], "title": res["title"], "provider": res["provider"]
                })

            st.success("Completed.")

        except Exception as e:
            st.error(f"Pipeline failed: {e}")
            st.code(traceback.format_exc(), language="python")

# ---------- History ----------
st.markdown("---")
st.markdown("### 🕘 Recent Runs")
if st.session_state.history:
    for i, h in enumerate(st.session_state.history[:6], 1):
        with st.expander(f"{i}. {h['mode']} — {h.get('title') or '(untitled)'}", expanded=False):
            st.caption(h["time"])
            st.write(f"**URL:** {h['url']}")
            st.write(f"**Provider:** {h['provider']}")
else:
    st.caption("No history yet. Run a query to see it here.")
