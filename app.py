import streamlit as st
from dotenv import load_dotenv
from agents.web_scrapper import WebScraperAgent

load_dotenv()

st.set_page_config(page_title="Agentic Web Link Q&A", page_icon="🕸️", layout="wide")

st.title("🕸️ Agentic AI Web Link Q&A Assistant")
st.caption("Day 1: Skeleton app — inputs only, no pipeline yet")

url = st.text_input("Web page URL", placeholder="https://example.com/article")
question = st.text_area("Your question", placeholder="Ask something about the page...")

if st.button("Fetch"):
    if not url:
        st.error("Please provide a URL.")
    else:
        try:
            scraper = WebScraperAgent()
            result = scraper.fetch(url)
            st.success("Fetched successfully")
            st.write(f"**Title:** {result.title or '(none)'}")
            st.write(f"**URL:** {result.url}")
            st.write(f"**HTML length:** {len(result.html):,} chars")
            st.write(f"**Text length:** {len(result.text):,} chars")
            st.markdown("### Preview (first 1200 chars)")
            st.code(result.text[:1200] + ('...' if len(result.text) > 1200 else ''), language="markdown")
        except Exception as e:
            st.error(f"Failed to fetch: {e}")