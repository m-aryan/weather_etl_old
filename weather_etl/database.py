from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from .config import settings

# PG-SQL setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.from_url(settings.REDIS_URL)

class WeatherData(Base):
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    temperature_c = Column(Float)
    precip_mm = Column(Float)
    data_source = Column(String)
    processed_at = Column(DateTime)

class DataLineage(Base):
    __tablename__ = "data_lineage"
    
    id = Column(Integer, primary_key=True)
    source_table = Column(String)
    target_table = Column(String)
    transformation = Column(Text)
    processed_at = Column(DateTime)

Base.metadata.create_all(bind=engine)