from pydantic import BaseModel
from datetime import datetime

class ArticleBase(BaseModel):
    title: str
    summary: str
    link: str
    source: str
    publication_date: datetime

class ArticleCreate(ArticleBase):
    pass

class Article(ArticleBase):
    article_id: int

    class Config:
        from_attributes = True