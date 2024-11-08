from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List
from urllib.parse import urljoin
from .base_scraper import BaseScraper

class TechCrunchScraper(BaseScraper):
    def __init__(self):
        super().__init__(source_name="TechCrunch AI")
        self.base_url = "https://techcrunch.com/category/artificial-intelligence/"

    async def fetch_articles(self) -> List[Dict]:
        try:
            headers = {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
            }
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                print(f"Fetching from TechCrunch AI: {self.base_url}")
                response = await client.get(self.base_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = []

                # Find all article entries in the main content area
                article_entries = soup.find_all('div', class_='post-block')
                print(f"Found {len(article_entries)} article entries")
                
                for entry in article_entries:
                    try:
                        article_data = {}
                        
                        # Get title and link from the header
                        header_elem = entry.find('h2', class_='post-block__title')
                        if header_elem:
                            link_elem = header_elem.find('a', href=True)
                            if link_elem:
                                article_data['title'] = self.clean_text(link_elem.text)
                                article_data['link'] = link_elem['href']
                                print(f"Found article: {article_data['title']}")
                        
                        # Get author
                        author_elem = entry.find('span', class_='river-byline__authors')
                        if author_elem:
                            author_link = author_elem.find('a')
                            if author_link:
                                article_data['author'] = self.clean_text(author_link.text)

                        # Get excerpt/summary
                        excerpt_elem = entry.find('div', class_='post-block__content')
                        if excerpt_elem:
                            article_data['excerpt'] = self.clean_text(excerpt_elem.text)
                        
                        # Get date
                        time_elem = entry.find('time', class_='river-byline__time')
                        if time_elem:
                            try:
                                # First try to get the datetime attribute
                                if time_elem.get('datetime'):
                                    article_data['date'] = datetime.fromisoformat(
                                        time_elem['datetime'].replace('Z', '+00:00')
                                    )
                                else:
                                    # If no datetime attribute, try to parse the text
                                    date_text = self.clean_text(time_elem.text)
                                    if 'ago' in date_text:
                                        # Handle relative dates
                                        article_data['date'] = datetime.utcnow()
                                    else:
                                        article_data['date'] = datetime.strptime(date_text, '%B %d, %Y')
                            except (ValueError, AttributeError) as e:
                                print(f"Error parsing date: {e}")
                                article_data['date'] = datetime.utcnow()

                        # Get category tags
                        category_elem = entry.find('span', class_='river-byline__categories')
                        if category_elem:
                            categories = [self.clean_text(tag.text) for tag in category_elem.find_all('a')]
                            article_data['categories'] = ', '.join(categories)

                        if article_data.get('title'):  # Only add if we have at least a title
                            articles.append(await self.parse_article(article_data))
                            print(f"Added TechCrunch article: {article_data['title']}")
                        else:
                            print("Article missing title, skipping.")
                            
                    except Exception as e:
                        print(f"Error parsing TechCrunch article: {e}")
                        continue

                print(f"Successfully parsed {len(articles)} TechCrunch articles")
                return articles

        except httpx.HTTPError as e:
            print(f"HTTP error occurred while fetching TechCrunch articles: {e}")
            return []
        except Exception as e:
            print(f"Error occurred while fetching TechCrunch articles: {e}")
            return []

    async def parse_article(self, article_data: Dict) -> Dict:
        # Build a comprehensive summary
        summary_parts = []
        
        if article_data.get('author'):
            summary_parts.append(f"By {article_data['author']}")
            
        if article_data.get('categories'):
            summary_parts.append(f"Categories: {article_data['categories']}")
            
        if article_data.get('excerpt'):
            summary_parts.append(article_data['excerpt'])

        summary = " | ".join(summary_parts) if summary_parts else "No details available"

        return {
            "title": article_data.get('title', ''),
            "summary": summary,
            "link": article_data.get('link', ''),
            "source": self.source_name,
            "publication_date": article_data.get('date', datetime.utcnow())
        }