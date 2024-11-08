from sqlalchemy import Column, Integer, String, DateTime, Text
from .database import Base
from datetime import datetime

class Article(Base):
    __tablename__ = "articles"

    article_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text)
    link = Column(String(500), nullable=False)
    publication_date = Column(DateTime, nullable=False)
    source = Column(String(100), nullable=False)
  