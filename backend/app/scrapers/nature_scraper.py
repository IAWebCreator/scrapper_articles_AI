from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List
from .base_scraper import BaseScraper

class NatureAIScraper(BaseScraper):
    def __init__(self):
        super().__init__(source_name="Nature AI Special")
        # Updated URL to a more accessible Nature AI page
        self.base_url = "https://www.nature.com/search?q=artificial%20intelligence&journal=nature"

    async def fetch_articles(self) -> List[Dict]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(self.base_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = []

                # Find all article items in the search results
                article_items = soup.find_all('li', class_='app-article-list-row')
                
                for item in article_items:
                    try:
                        article_data = {}
                        
                        # Get title
                        title_elem = item.find('a', class_='c-card__link')
                        if title_elem:
                            article_data['title'] = self.clean_text(title_elem.text)
                            article_data['link'] = f"https://www.nature.com{title_elem['href']}"
                        
                        # Get description/summary
                        desc_elem = item.find('div', class_='c-card__summary')
                        if desc_elem:
                            article_data['description'] = self.clean_text(desc_elem.text)
                        
                        # Get date
                        date_elem = item.find('time')
                        if date_elem:
                            try:
                                article_data['date'] = datetime.strptime(date_elem['datetime'], '%Y-%m-%d')
                            except (ValueError, KeyError):
                                article_data['date'] = datetime.utcnow()

                        if article_data.get('title'):  # Only process if we have at least a title
                            articles.append(await self.parse_article(article_data))
                            
                    except Exception as e:
                        print(f"Error parsing Nature article: {e}")
                        continue

                return articles

        except httpx.HTTPError as e:
            print(f"HTTP error occurred while fetching Nature articles: {e}")
            return []
        except Exception as e:
            print(f"Error occurred while fetching Nature articles: {e}")
            return []

    async def parse_article(self, article_data: Dict) -> Dict:
        return {
            "title": article_data.get('title', ''),
            "summary": article_data.get('description', ''),
            "link": article_data.get('link', ''),
            "source": self.source_name,
            "publication_date": article_data.get('date', datetime.utcnow())
        } 