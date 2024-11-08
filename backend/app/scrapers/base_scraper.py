from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict

class BaseScraper(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    async def fetch_articles(self) -> List[Dict]:
        """
        Fetch articles from the source
        Returns a list of dictionaries containing article data
        """
        pass

    @abstractmethod
    async def parse_article(self, article_data) -> Dict:
        """
        Parse individual article data
        Returns a dictionary with article details
        """
        pass

    def clean_text(self, text: str) -> str:
        """
        Clean and format text data
        """
        if text:
            return " ".join(text.split())
        return "" 