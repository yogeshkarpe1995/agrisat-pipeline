"""
Configuration settings for the satellite monitoring pipeline.
"""

import os
from pathlib import Path

class Config:
    """Configuration class for pipeline settings."""
    
    def __init__(self):
        # API Endpoints
        self.PLOTS_API_URL = "https://agintel10x-test.onfarmerp.com:8002/api/MA_SubPlot/GetSubPlotDetailsForIntegration?subPlotCode=SP631"
        self.COPERNICUS_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        self.COPERNICUS_SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        self.COPERNICUS_DOWNLOAD_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
        
        # Authentication
        self.COPERNICUS_CLIENT_ID = os.getenv("COPERNICUS_CLIENT_ID", "cdse-public")
        self.COPERNICUS_CLIENT_SECRET = os.getenv("COPERNICUS_CLIENT_SECRET", "")
        self.COPERNICUS_USERNAME = os.getenv("COPERNICUS_USERNAME", "")
        self.COPERNICUS_PASSWORD = os.getenv("COPERNICUS_PASSWORD", "")
        
        # Processing settings
        self.MAX_CLOUD_COVERAGE = 90  # Maximum cloud coverage percentage
        self.IMAGE_WIDTH = 256
        self.IMAGE_HEIGHT = 256
        self.OUTPUT_FORMAT = "image/tiff"
        
        # Output directory
        self.OUTPUT_DIR = Path("output")
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Vegetation indices to calculate (optimized for minimal processing units)
        self.INDICES = ["NDVI", "NDRE", "MSAVI", "NDMI", "TrueColor"]
        
        # Rate limiting and CPU optimization
        self.REQUEST_DELAY = 1.0  # Seconds between requests
        self.MAX_RETRIES = 3
        self.BATCH_SIZE = 2  # Process plots in smaller batches to reduce CPU load
        self.MEMORY_EFFICIENT_MODE = True  # Enable memory-efficient processing
        
        # Parallel processing configuration
        self.MAX_PARALLEL_WORKERS = 4  # Maximum parallel worker threads
        self.PARALLEL_MODE = 'thread'  # 'thread' or 'process'
        self.MEMORY_LIMIT_GB = 4  # Memory limit for parallel processing
        
        # Cloud masking and quality filtering
        self.MIN_DATA_COVERAGE = 100  # Minimum % of valid pixels required
        self.ENABLE_CLOUD_MASKING = True  # Enable automatic cloud masking
        self.QUALITY_THRESHOLD = 'acceptable'  # 'poor', 'acceptable', 'good', 'excellent'
        
        # Date format
        self.DATE_FORMAT = "%Y-%m-%d"
