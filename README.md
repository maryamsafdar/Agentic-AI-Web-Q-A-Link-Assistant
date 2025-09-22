# Agentic AI Web Link Q&A Assistant (Streamlit)

A Streamlit app demonstrating an *agentic* workflow:
1. Fetch content from a given web URL
2. Clean and segment the text
3. Highlight relevant sections
4. Generate contextual answers using an LLM (OpenAI, fallback supported)

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
