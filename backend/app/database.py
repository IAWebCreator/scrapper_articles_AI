from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()

# Get database URL from environment and properly encode password
db_user = "postgres"
db_password = urllib.parse.quote_plus("1Nuevohigado")  # URL encode the password
db_host = "localhost"
db_port = "5432"
db_name = "IA_articles"

SQLALCHEMY_DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create engine with explicit encoding
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    client_encoding='utf8'
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 