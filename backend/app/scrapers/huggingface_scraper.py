from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List
from urllib.parse import urljoin
from .base_scraper import BaseScraper

class HuggingFaceScraper(BaseScraper):
    def __init__(self):
        super().__init__(source_name="Hugging Face Blog")
        self.base_url = "https://huggingface.co/blog"

    async def fetch_articles(self) -> List[Dict]:
        try:
            headers = {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
            }
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                print(f"Fetching from Hugging Face Blog: {self.base_url}")
                response = await client.get(self.base_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                all_articles = []
                recent_articles = []

                # Find all community articles
                community_articles = soup.find_all('div', {'class': 'flex', 'role': 'article'})
                print(f"Found {len(community_articles)} community articles")

                # Process community articles
                for article in community_articles:
                    try:
                        article_data = {}
                        
                        # Get title and link
                        title_link = article.find('a', class_='text-lg')
                        if title_link:
                            article_data['title'] = self.clean_text(title_link.text)
                            article_data['link'] = urljoin(self.base_url, title_link['href'])

                        # Get author
                        author_elem = article.find('a', class_='hover:underline')
                        if author_elem:
                            article_data['author'] = self.clean_text(author_elem.text)

                        # Get date
                        date_text = None
                        for text in article.stripped_strings:
                            if any(time_indicator in text.lower() for time_indicator in ['days ago', 'hours ago', 'about']):
                                date_text = text
                                break

                        if date_text:
                            try:
                                if 'days ago' in date_text:
                                    days = int(date_text.split()[0])
                                    article_data['date'] = datetime.utcnow() - timedelta(days=days)
                                elif 'hours ago' in date_text:
                                    hours = int(date_text.split()[0])
                                    article_data['date'] = datetime.utcnow() - timedelta(hours=hours)
                                elif 'about' in date_text.lower() and 'hours ago' in date_text.lower():
                                    hours = int(date_text.split()[1])
                                    article_data['date'] = datetime.utcnow() - timedelta(hours=hours)
                            except (ValueError, IndexError) as e:
                                print(f"Error parsing date '{date_text}': {e}")
                                article_data['date'] = datetime.utcnow()
                        else:
                            article_data['date'] = datetime.utcnow()

                        # Get likes/interactions count if available
                        likes_elem = article.find('span', class_='ml-1')
                        if likes_elem:
                            article_data['likes'] = self.clean_text(likes_elem.text)

                        if article_data.get('title'):  # Only add if we have at least a title
                            parsed_article = await self.parse_article(article_data)
                            all_articles.append(parsed_article)
                            
                            # Check if article is from last 24 hours
                            if datetime.utcnow() - article_data['date'] <= timedelta(hours=24):
                                recent_articles.append(parsed_article)
                            
                            print(f"Added Hugging Face article: {article_data['title']}")
                        else:
                            print("Article missing title, skipping.")
                            
                    except Exception as e:
                        print(f"Error parsing Hugging Face article: {e}")
                        continue

                # Process featured articles similarly
                featured_articles = soup.find_all('article', class_='flex')
                print(f"Found {len(featured_articles)} featured articles")

                for article in featured_articles:
                    try:
                        article_data = {}
                        
                        # Get title and link
                        title_link = article.find('a', class_='text-2xl')
                        if title_link:
                            article_data['title'] = self.clean_text(title_link.text)
                            article_data['link'] = urljoin(self.base_url, title_link['href'])

                        # Get author and date
                        meta_text = article.find('div', class_='text-sm')
                        if meta_text:
                            meta_parts = [part.strip() for part in meta_text.text.split('•')]
                            if len(meta_parts) >= 2:
                                article_data['author'] = meta_parts[0].replace('By', '').strip()
                                try:
                                    article_data['date'] = datetime.strptime(meta_parts[1].strip(), '%B %d, %Y')
                                except ValueError:
                                    article_data['date'] = datetime.utcnow()

                        if article_data.get('title'):
                            parsed_article = await self.parse_article(article_data)
                            all_articles.append(parsed_article)
                            
                            # Check if article is from last 24 hours
                            if datetime.utcnow() - article_data['date'] <= timedelta(hours=24):
                                recent_articles.append(parsed_article)
                                
                            print(f"Added Hugging Face featured article: {article_data['title']}")
                        else:
                            print("Featured article missing title, skipping.")

                    except Exception as e:
                        print(f"Error parsing Hugging Face featured article: {e}")
                        continue

                # Return recent articles if available, otherwise return last 3 articles
                if recent_articles:
                    print(f"Returning {len(recent_articles)} articles from last 24 hours")
                    return recent_articles
                else:
                    print("No articles from last 24 hours, returning last 3 articles")
                    return sorted(all_articles, 
                                key=lambda x: datetime.fromisoformat(str(x['publication_date'])), 
                                reverse=True)[:3]

        except httpx.HTTPError as e:
            print(f"HTTP error occurred while fetching Hugging Face articles: {e}")
            return []
        except Exception as e:
            print(f"Error occurred while fetching Hugging Face articles: {e}")
            return []

    async def parse_article(self, article_data: Dict) -> Dict:
        # Build a comprehensive summary
        summary_parts = []
        
        if article_data.get('author'):
            summary_parts.append(f"By {article_data['author']}")
            
        if article_data.get('likes'):
            summary_parts.append(f"❤️ {article_data['likes']}")

        summary = " | ".join(summary_parts) if summary_parts else "No details available"

        return {
            "title": article_data.get('title', ''),
            "summary": summary,
            "link": article_data.get('link', ''),
            "source": self.source_name,
            "publication_date": article_data.get('date', datetime.utcnow())
        }