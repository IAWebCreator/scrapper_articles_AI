from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List
from urllib.parse import urljoin
from .base_scraper import BaseScraper

class JAIRScraper(BaseScraper):
    def __init__(self):
        super().__init__(source_name="Journal of AI Research")
        self.base_url = "https://www.jair.org/index.php/jair/issue/view/1170"

    async def fetch_articles(self) -> List[Dict]:
        try:
            headers = {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
            }

            async with httpx.AsyncClient(follow_redirects=True) as client:
                print(f"Fetching from JAIR: {self.base_url}")
                response = await client.get(self.base_url, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                articles = []

                # Get issue publication date from the page
                issue_date = None
                published_text = soup.find(string="Published:")
                if published_text and published_text.parent:
                    try:
                        date_text = published_text.next_sibling.strip()
                        issue_date = datetime.strptime(date_text, '%Y-%m-%d')
                        print(f"Found issue date: {issue_date}")
                    except (ValueError, AttributeError) as e:
                        print(f"Error parsing date: {e}")
                        issue_date = datetime.utcnow()

                # Find all article entries in the section with class 'articles'
                articles_section = soup.find('section', class_='articles')
                if not articles_section:
                    print("Could not find articles section")
                    return []

                # Find all article entries
                article_entries = articles_section.find_all('div', class_='obj_article_summary')
                print(f"Found {len(article_entries)} article entries")

                for entry in article_entries:
                    try:
                        article_data = {}

                        # Get title and link
                        title_elem = entry.find('div', class_='title')
                        if title_elem:
                            link_elem = title_elem.find('a')
                            if link_elem:
                                article_data['title'] = self.clean_text(link_elem.text)
                                # Make sure we have a full URL
                                article_data['link'] = urljoin(self.base_url, link_elem['href'])
                                print(f"Found article: {article_data['title']}")

                        # Get authors
                        authors_elem = entry.find('div', class_='authors')
                        if authors_elem:
                            authors = []
                            for author_link in authors_elem.find_all('a'):
                                authors.append(self.clean_text(author_link.text))
                            article_data['authors'] = ', '.join(authors)

                        # Get pages
                        pages_elem = entry.find('div', class_='pages')
                        if pages_elem:
                            article_data['pages'] = self.clean_text(pages_elem.text.replace('Pages:', '').strip())

                        # Set publication date
                        article_data['date'] = issue_date

                        # Get PDF link if available
                        pdf_elem = entry.find('a', class_='pdf')
                        if pdf_elem and pdf_elem.get('href'):
                            article_data['pdf_link'] = urljoin(self.base_url, pdf_elem['href'])

                        if article_data.get('title'):  # Only add if we have at least a title
                            articles.append(await self.parse_article(article_data))
                            print(f"Added JAIR article: {article_data['title']}")
                        else:
                            print("Article missing title, skipping.")

                    except Exception as e:
                        print(f"Error parsing JAIR article: {e}")
                        continue

                print(f"Successfully parsed {len(articles)} JAIR articles")
                return articles

        except httpx.HTTPError as e:
            print(f"HTTP error occurred while fetching JAIR articles: {e}")
            return []
        except Exception as e:
            print(f"Error occurred while fetching JAIR articles: {e}")
            return []

    async def parse_article(self, article_data: Dict) -> Dict:
        # Build a comprehensive summary
        summary_parts = []

        if article_data.get('authors'):
            summary_parts.append(f"Authors: {article_data['authors']}")

        if article_data.get('pages'):
            summary_parts.append(f"Pages: {article_data['pages']}")

        if article_data.get('pdf_link'):
            summary_parts.append(f"[PDF Available]")

        summary = " | ".join(summary_parts) if summary_parts else "No details available"

        return {
            "title": article_data.get('title', ''),
            "summary": summary,
            "link": article_data.get('link', ''),
            "source": self.source_name,
            "publication_date": article_data.get('date', datetime.utcnow())
        }