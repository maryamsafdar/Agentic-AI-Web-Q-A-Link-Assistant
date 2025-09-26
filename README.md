# Agentic AI Web Link Q&A Assistant (Streamlit)

A Streamlit app demonstrating an *agentic* workflow that:
1) Fetches content from a given web URL
2) Cleans and segments the text
3) Highlights the most relevant sections to a user question
4) Generates contextual answers using an LLM (OpenAI) — with a TF‑IDF fallback if no API key is present
5) Supports follow‑up questions without re‑scraping (session memory)

---

## Quick Start

### 1) Create a virtual environment and install dependencies
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2) Set your API key (recommended)
Create a `.env` file in the project root with:
```
OPENAI_API_KEY=sk-...your key...
OPENAI_MODEL=gpt-4o-mini
```

> Alternatively, you can set the key in `~/.bashrc`, PowerShell profile, or via Streamlit Secrets.

### 3) Run the app
```bash
streamlit run app.py
```

Then open the local URL (typically http://localhost:8501).

---

## Project Structure

```
agentic-web-link-qa-assistant/
├─ app.py
├─ orchestrator.py
├─ requirements.txt
├─ .env.example
├─ README.md
├─ prompts/
│  └─ system_prompts.py
├─ agents/
│  ├─ __init__.py
│  ├─ web_scraper.py
│  ├─ content_processor.py
│  └─ qna_agent.py
└─ utils/
   └─ text_utils.py
```

---

## Notes

- If no `OPENAI_API_KEY` is found, the app will **still run** with a TF‑IDF heuristic to extract a likely answer from the page; LLM quality answers require a valid key.
- The app uses `requests + BeautifulSoup` for scraping; many sites block scraping or rely on heavy JS — in such cases, try a different page or provide a static article URL.
- For best results: copy a readable article/blog/documentation URL and ask precise questions.
