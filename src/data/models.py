"""
Database models for satellite monitoring pipeline.
"""

import os
from sqlalchemy import create_engine, Column, String, DateTime, Float, Integer, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class ProcessingRecord(Base):
    """Track processed satellite data to avoid redundant downloads."""
    __tablename__ = 'processing_records'
    
    id = Column(String, primary_key=True)  # plot_id + date
    plot_id = Column(String, nullable=False)
    processing_date = Column(String, nullable=False)  # YYYY-MM-DD format
    satellite_date = Column(String, nullable=False)  # Actual satellite acquisition date
    file_size_bytes = Column(Integer)
    processing_time_seconds = Column(Float)
    indices_calculated = Column(Text)  # JSON string of calculated indices
    output_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
class PlotMetadata(Base):
    """Store plot information and processing status."""
    __tablename__ = 'plot_metadata'
    
    plot_id = Column(String, primary_key=True)
    area_hectares = Column(Float)
    crop_type = Column(String)
    owner = Column(String)
    region = Column(String)
    planting_date = Column(String)  # YYYY-MM-DD
    harvest_date = Column(String)   # YYYY-MM-DD
    irrigation_type = Column(String)
    soil_type = Column(String)
    elevation_m = Column(Float)
    geometry = Column(Text)  # GeoJSON geometry as text
    last_processed = Column(DateTime)
    total_images_processed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Database setup
def get_database_session():
    """Create database session."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///data/satellite_monitoring.db")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def create_tables():
    """Create all database tables."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///data/satellite_monitoring.db")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)