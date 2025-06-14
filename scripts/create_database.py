
#!/usr/bin/env python3
"""
Database creation script for Satellite Agriculture Monitoring Pipeline.
This script creates the database tables, indexes, and populates sample data.
"""

import os
import sys
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from src.data.models import Base, PlotMetadata, ProcessingRecord, get_database_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database():
    """Create database tables and indexes."""
    try:
        # Set default database URL if not provided
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite:///satellite_monitoring.db"
        
        database_url = os.getenv("DATABASE_URL")
        logger.info(f"Creating database: {database_url}")
        
        # Create engine and tables
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        
        # Create additional indexes for better performance
        with engine.connect() as conn:
            # Index on region for regional queries
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_plot_region ON plot_metadata(region)"))
                logger.info("Created index on plot_metadata.region")
            except Exception as e:
                logger.warning(f"Index on region may already exist: {e}")
            
            # Index on crop_type for crop-based filtering
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_plot_crop_type ON plot_metadata(crop_type)"))
                logger.info("Created index on plot_metadata.crop_type")
            except Exception as e:
                logger.warning(f"Index on crop_type may already exist: {e}")
            
            # Index on processing_date for date-based queries
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_processing_date ON processing_records(processing_date)"))
                logger.info("Created index on processing_records.processing_date")
            except Exception as e:
                logger.warning(f"Index on processing_date may already exist: {e}")
            
            # Composite index on (plot_id, processing_date)
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_plot_processing_date ON processing_records(plot_id, processing_date)"))
                logger.info("Created composite index on processing_records(plot_id, processing_date)")
            except Exception as e:
                logger.warning(f"Composite index may already exist: {e}")
            
            conn.commit()
        
        logger.info("Database tables and indexes created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database: {str(e)}")
        return False

def populate_sample_data():
    """Populate database with sample plot data."""
    try:
        session = get_database_session()
        
        # Sample plot data
        sample_plots = [
            {
                "plot_id": "IND001",
                "area_hectares": 12.5,
                "crop_type": "wheat",
                "owner": "Bharat Agro Pvt Ltd",
                "region": "Punjab, India",
                "planting_date": "2023-11-15",
                "harvest_date": "2024-04-10",
                "irrigation_type": "drip",
                "soil_type": "clay_loam",
                "elevation_m": 260,
                "geometry": json.dumps({
                    "type": "Polygon",
                    "coordinates": [[[75, 31.25], [75.01, 31.25], [75.01, 31.255], [75, 31.255], [75, 31.25]]]
                })
            },
            {
                "plot_id": "IND002",
                "area_hectares": 8.3,
                "crop_type": "rice",
                "owner": "Green Fields Agriculture",
                "region": "Tamil Nadu, India",
                "planting_date": "2024-06-01",
                "harvest_date": "2024-10-15",
                "irrigation_type": "flood",
                "soil_type": "clay",
                "elevation_m": 45,
                "geometry": json.dumps({
                    "type": "Polygon",
                    "coordinates": [[[78.5, 12.5], [78.51, 12.5], [78.51, 12.505], [78.5, 12.505], [78.5, 12.5]]]
                })
            },
            {
                "plot_id": "IND003",
                "area_hectares": 15.2,
                "crop_type": "cotton",
                "owner": "Maharashtra Cotton Co.",
                "region": "Maharashtra, India",
                "planting_date": "2023-12-05",
                "harvest_date": "2024-11-20",
                "irrigation_type": "sprinkler",
                "soil_type": "black_soil",
                "elevation_m": 450,
                "geometry": json.dumps({
                    "type": "Polygon",
                    "coordinates": [[[75.8, 19.2], [75.81, 19.2], [75.81, 19.205], [75.8, 19.205], [75.8, 19.2]]]
                })
            },
            {
                "plot_id": "IND004",
                "area_hectares": 6.7,
                "crop_type": "maize",
                "owner": "Karnataka Farmers Union",
                "region": "Karnataka, India",
                "planting_date": "2024-06-20",
                "harvest_date": "2024-12-10",
                "irrigation_type": "drip",
                "soil_type": "red_soil",
                "elevation_m": 800,
                "geometry": json.dumps({
                    "type": "Polygon",
                    "coordinates": [[[77.2, 15.3], [77.21, 15.3], [77.21, 15.305], [77.2, 15.305], [77.2, 15.3]]]
                })
            },
            {
                "plot_id": "IND005",
                "area_hectares": 20.1,
                "crop_type": "sugarcane",
                "owner": "Uttar Pradesh Sugar Mills",
                "region": "Uttar Pradesh, India",
                "planting_date": "2024-07-10",
                "harvest_date": "2024-11-05",
                "irrigation_type": "flood",
                "soil_type": "alluvial",
                "elevation_m": 180,
                "geometry": json.dumps({
                    "type": "Polygon",
                    "coordinates": [[[80.1, 26.8], [80.11, 26.8], [80.11, 26.805], [80.1, 26.805], [80.1, 26.8]]]
                })
            }
        ]
        
        # Insert sample plots
        for plot_data in sample_plots:
            existing_plot = session.query(PlotMetadata).filter_by(plot_id=plot_data["plot_id"]).first()
            
            if not existing_plot:
                plot = PlotMetadata(**plot_data)
                session.add(plot)
                logger.info(f"Added sample plot: {plot_data['plot_id']}")
            else:
                logger.info(f"Plot {plot_data['plot_id']} already exists, skipping")
        
        session.commit()
        logger.info("Sample plot data populated successfully")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to populate sample data: {str(e)}")
        raise
    finally:
        session.close()

def verify_database():
    """Verify database creation and data integrity."""
    try:
        session = get_database_session()
        
        # Check tables exist and have data
        plot_count = session.query(PlotMetadata).count()
        record_count = session.query(ProcessingRecord).count()
        
        logger.info(f"Database verification:")
        logger.info(f"  - Plot metadata records: {plot_count}")
        logger.info(f"  - Processing records: {record_count}")
        
        # Check indexes (SQLite specific)
        if "sqlite" in os.getenv("DATABASE_URL", ""):
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"))
            indexes = [row[0] for row in result.fetchall()]
            logger.info(f"  - Custom indexes created: {len(indexes)}")
            for idx in indexes:
                logger.info(f"    - {idx}")
        
        # Sample query to test functionality
        sample_plot = session.query(PlotMetadata).first()
        if sample_plot:
            logger.info(f"  - Sample plot query successful: {sample_plot.plot_id}")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        return False

def main():
    """Main function to create and initialize database."""
    logger.info("Starting database creation script")
    
    try:
        # Step 1: Create database tables and indexes
        if not create_database():
            logger.error("Database creation failed")
            sys.exit(1)
        
        # Step 2: Populate sample data
        populate_sample_data()
        
        # Step 3: Verify database
        if not verify_database():
            logger.error("Database verification failed")
            sys.exit(1)
        
        logger.info("Database creation and initialization completed successfully")
        logger.info("You can now run the satellite monitoring pipeline")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
