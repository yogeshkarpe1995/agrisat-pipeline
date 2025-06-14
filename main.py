#!/usr/bin/env python3
"""
Satellite Agriculture Monitoring Pipeline
Main entry point for the satellite agriculture monitoring system.
"""

import sys
import logging
from pathlib import Path
from src.core.pipeline import SatelliteMonitoringPipeline
from src.core.config import Config

def setup_logging():
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pipeline.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function to run the satellite monitoring pipeline."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize configuration
        config = Config()
        
        # Create pipeline instance
        pipeline = SatelliteMonitoringPipeline(config)
        
        # Run the complete pipeline
        logger.info("Starting satellite agriculture monitoring pipeline")
        pipeline.run()
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
