from dataclass import ScrapeResult
from typing import Optional
import requests #ignore
from bs4 import BeautifulSoup


class WebScraperAgent:
    def __init__(self, timeout:int = 20, user_agent:Optional[str]= None) -> None:
        self.timeout = timeout
        self.user_agent = user_agent or (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        )
    def fetch(self, url: str)-> ScrapeResult:
        headers = {"User-Agent": self.user_agent}
        resp= response = requests.get(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        title = soup.title.string if soup.title else None
        text = soup.get_text(separator='\n', strip=True)
        text = "".join(text.split())
        return ScrapeResult(url=url, html=html, text=text, title=title)