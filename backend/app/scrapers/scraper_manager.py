from typing import List, Dict
from .arxiv_scraper import ArxivScraper
from .papers_with_code_scraper import PapersWithCodeScraper
from .jair_scraper import JAIRScraper
from .techcrunch_scraper import TechCrunchScraper
from .nature_scraper import NatureAIScraper
from .huggingface_scraper import HuggingFaceScraper
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ScraperManager:
    def __init__(self):
        self.scrapers = [
            ArxivScraper(),
            PapersWithCodeScraper(),
            JAIRScraper(),
            TechCrunchScraper(),
            NatureAIScraper(),
            HuggingFaceScraper(),
        ]

    async def fetch_all_articles(self) -> List[Dict]:
        """
        Fetch articles from all configured scrapers
        """
        all_articles = []
        for scraper in self.scrapers:
            try:
                logger.info(f"Starting to fetch articles from {scraper.source_name}")
                articles = await scraper.fetch_articles()
                logger.info(f"Successfully fetched {len(articles)} articles from {scraper.source_name}")
                
                # Log the first article from each source for debugging
                if articles:
                    logger.info(f"Sample article from {scraper.source_name}:")
                    logger.info(f"Title: {articles[0].get('title')}")
                    logger.info(f"Link: {articles[0].get('link')}")
                
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error fetching articles from {scraper.source_name}: {e}")
        
        logger.info(f"Total articles fetched from all sources: {len(all_articles)}")
        return all_articles