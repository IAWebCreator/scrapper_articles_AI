from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from . import models, schemas, database
from .database import engine, SessionLocal
from .scrapers.scraper_manager import ScraperManager
import logging
from .config import settings
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI News Aggregator")

# Update CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper_manager = ScraperManager()

# In production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["your-domain.com", "*.your-domain.com"]
    )

@app.get("/articles/", response_model=List[schemas.Article])
async def get_articles(
    timeframe: int = Query(24, description="Timeframe in hours"),
    source: str = Query(None, description="Filter by source"),
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Article)
    
    if timeframe:
        time_threshold = datetime.utcnow() - timedelta(hours=timeframe)
        query = query.filter(models.Article.publication_date >= time_threshold)
    
    if source:
        query = query.filter(models.Article.source == source)
    
    return query.order_by(models.Article.publication_date.desc()).all()

@app.get("/sources/")
async def get_sources(db: Session = Depends(database.get_db)):
    sources = db.query(models.Article.source).distinct().all()
    return [source[0] for source in sources]

@app.post("/refresh-articles/")
async def refresh_articles(db: Session = Depends(database.get_db)):
    """Trigger a fresh scrape of all articles"""
    try:
        # Fetch new articles
        articles = await scraper_manager.fetch_all_articles()
        new_articles_count = 0
        
        # Store in database
        for article_data in articles:
            try:
                # Check if article already exists
                existing = db.query(models.Article).filter(
                    models.Article.title == article_data["title"],
                    models.Article.source == article_data["source"]
                ).first()
                
                if not existing:
                    new_article = models.Article(**article_data)
                    db.add(new_article)
                    new_articles_count += 1
                    
            except Exception as article_error:
                logger.error(f"Error processing article: {article_error}")
                continue
        
        try:
            db.commit()
            return {"message": "Articles refreshed successfully", "count": new_articles_count}
        except Exception as commit_error:
            db.rollback()
            logger.error(f"Error committing to database: {commit_error}")
            raise HTTPException(status_code=500, detail="Error saving articles to database")
            
    except Exception as e:
        logger.error(f"Error in refresh_articles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing articles: {str(e)}"
        )