from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List
from .base_scraper import BaseScraper

class PapersWithCodeScraper(BaseScraper):
    def __init__(self):
        super().__init__(source_name="Papers with Code")
        self.base_url = "https://paperswithcode.com/latest"

    async def fetch_articles(self) -> List[Dict]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                print(f"Fetching from {self.base_url}")
                response = await client.get(self.base_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = []

                # Find all paper items
                paper_items = soup.find_all('div', class_='paper-card')
                print(f"Found {len(paper_items)} paper items")
                
                for item in paper_items:
                    try:
                        article_data = {}
                        
                        # Get title and link
                        title_elem = item.find('h1')
                        if not title_elem:
                            title_elem = item.find('h4')
                            
                        if title_elem:
                            link_elem = title_elem.find('a')
                            if link_elem:
                                article_data['title'] = self.clean_text(link_elem.text)
                                article_data['link'] = f"https://paperswithcode.com{link_elem['href']}"
                        
                        # Get abstract/description
                        abstract_elem = item.find('p', class_='paper-abstract')
                        if not abstract_elem:
                            abstract_elem = item.find('p', class_='item-strip-abstract')
                        if abstract_elem:
                            article_data['abstract'] = self.clean_text(abstract_elem.text)
                        
                        # Get date - try multiple possible date elements and formats
                        date_elem = item.find(['span', 'div'], class_=['date-published', 'item-date', 'date'])
                        if date_elem:
                            date_text = date_elem.text.strip()
                            try:
                                # Handle various date formats and relative dates
                                if "days ago" in date_text:
                                    days = int(date_text.split()[0])
                                    article_data['date'] = datetime.utcnow() - timedelta(days=days)
                                elif "hours ago" in date_text:
                                    hours = int(date_text.split()[0])
                                    article_data['date'] = datetime.utcnow() - timedelta(hours=hours)
                                elif "minutes ago" in date_text:
                                    minutes = int(date_text.split()[0])
                                    article_data['date'] = datetime.utcnow() - timedelta(minutes=minutes)
                                elif "just now" in date_text.lower():
                                    article_data['date'] = datetime.utcnow()
                                else:
                                    # Try different date formats
                                    try:
                                        article_data['date'] = datetime.strptime(date_text, '%d %b %Y')
                                    except ValueError:
                                        try:
                                            article_data['date'] = datetime.strptime(date_text, '%Y-%m-%d')
                                        except ValueError:
                                            try:
                                                article_data['date'] = datetime.strptime(date_text, '%B %d, %Y')
                                            except ValueError:
                                                print(f"Could not parse date format: {date_text}")
                                                article_data['date'] = datetime.utcnow()
                            except (ValueError, IndexError) as e:
                                print(f"Error parsing date '{date_text}': {e}")
                                article_data['date'] = datetime.utcnow()

                        # Get GitHub stars if available
                        stars_elem = item.find('span', class_='github-stars')
                        if stars_elem:
                            article_data['stars'] = self.clean_text(stars_elem.text)

                        # Get paper publication date from metadata if available
                        meta_date = item.find('meta', {'name': 'citation_publication_date'})
                        if meta_date and meta_date.get('content'):
                            try:
                                article_data['date'] = datetime.strptime(meta_date['content'], '%Y-%m-%d')
                            except ValueError:
                                print(f"Could not parse meta date: {meta_date['content']}")

                        if article_data.get('title'):  # Only process if we have at least a title
                            articles.append(await self.parse_article(article_data))
                            print(f"Added article: {article_data['title']} with date: {article_data.get('date')}")
                            
                    except Exception as e:
                        print(f"Error parsing paper item: {e}")
                        continue

                print(f"Successfully parsed {len(articles)} articles")
                return articles

        except httpx.HTTPError as e:
            print(f"HTTP error occurred while fetching Papers with Code: {e}")
            return []
        except Exception as e:
            print(f"Error occurred while fetching Papers with Code: {e}")
            return []

    async def parse_article(self, article_data: Dict) -> Dict:
        # Create summary combining abstract, stars, and date if available
        summary_parts = []
        if article_data.get('stars'):
            summary_parts.append(f"⭐ {article_data['stars']}")
        if article_data.get('abstract'):
            summary_parts.append(article_data['abstract'])
        
        summary = " | ".join(summary_parts) if summary_parts else "No summary available"

        # Format the date nicely for display
        if article_data.get('date'):
            formatted_date = article_data['date'].strftime('%Y-%m-%d %H:%M:%S')
            summary = f"Published: {formatted_date}\n{summary}"

        return {
            "title": article_data.get('title', ''),
            "summary": summary,
            "link": article_data.get('link', ''),
            "source": self.source_name,
            "publication_date": article_data.get('date', datetime.utcnow())
        }