import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Agentic Web Link Q&A", page_icon="🕸️", layout="wide")

st.title("🕸️ Agentic AI Web Link Q&A Assistant")
st.caption("Day 1: Skeleton app — inputs only, no pipeline yet")

url = st.text_input("Web page URL", placeholder="https://example.com/article")
question = st.text_area("Your question", placeholder="Ask something about the page...")

if st.button("Run Agent", type="primary"):
    if not url or not question:
        st.error("Please provide both a URL and a question.")
    else:
        st.info("🚧 Day 1 scaffold only — agents will be added later.")
