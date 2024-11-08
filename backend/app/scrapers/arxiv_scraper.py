import re
from datetime import datetime
from typing import Dict, List
import httpx
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

class ArxivScraper(BaseScraper):
    def __init__(self):
        super().__init__(source_name="arXiv CS.AI")
        self.base_url = "https://arxiv.org/list/cs.AI/new"

    async def fetch_articles(self) -> List[Dict]:
        """
        Fetch new AI-related articles from arXiv
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = []

                # Find the "New submissions" section
                new_submissions = soup.find('h3', string=re.compile(r'New submissions'))
                if new_submissions:
                    # Get all articles in the new submissions section
                    dl_elements = new_submissions.find_next('dl')
                    if dl_elements:
                        current_article = {}
                        for element in dl_elements.children:
                            if element.name == 'dt':
                                # Start of new article
                                if current_article:
                                    articles.append(await self.parse_article(current_article))
                                current_article = {'id': element.get('id', '')}
                            elif element.name == 'dd':
                                # Article content
                                if current_article is not None:
                                    title_div = element.find('div', class_='list-title')
                                    authors_div = element.find('div', class_='list-authors')
                                    abstract_div = element.find('p', class_='mathjax')
                                    
                                    if title_div:
                                        current_article['title'] = self.clean_text(title_div.text.replace('Title:', ''))
                                    if authors_div:
                                        current_article['authors'] = self.clean_text(authors_div.text.replace('Authors:', ''))
                                    if abstract_div:
                                        current_article['abstract'] = self.clean_text(abstract_div.text)
                                    
                                    # Extract arXiv ID and create link
                                    if 'id' in current_article:
                                        arxiv_id = current_article['id'].split(':')[-1]
                                        current_article['link'] = f"https://arxiv.org/abs/{arxiv_id}"

                        # Don't forget to append the last article
                        if current_article:
                            articles.append(await self.parse_article(current_article))

                return articles

        except httpx.HTTPError as e:
            print(f"HTTP error occurred while fetching arXiv articles: {e}")
            return []
        except Exception as e:
            print(f"Error occurred while fetching arXiv articles: {e}")
            return []

    async def parse_article(self, article_data: Dict) -> Dict:
        """
        Parse article data into standardized format
        """
        # Combine abstract and authors into summary
        summary_parts = []
        if article_data.get('authors'):
            summary_parts.append(f"Authors: {article_data['authors']}")
        if article_data.get('abstract'):
            summary_parts.append(article_data['abstract'])
        
        summary = " | ".join(summary_parts)

        return {
            "title": article_data.get('title', ''),
            "summary": summary,
            "link": article_data.get('link', ''),
            "source": self.source_name,
            "publication_date": datetime.utcnow()  # arXiv shows current date for new submissions
        }

    def clean_text(self, text: str) -> str:
        """
        Clean and format text data, removing extra whitespace and newlines
        """
        if text:
            # Remove extra whitespace and newlines
            cleaned = ' '.join(text.strip().split())
            return cleaned
        return "" 