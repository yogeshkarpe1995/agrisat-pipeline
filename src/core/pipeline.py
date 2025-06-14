"""
Main pipeline orchestrator for satellite agriculture monitoring.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from src.core.config import Config
from src.services.auth import CopernicusAuth
from src.services.api_client import APIClient
from src.processors.satellite_processor import SatelliteProcessor
from src.processors.indices_calculator import IndicesCalculator
from src.processors.parallel_processor import ParallelPlotProcessor
from src.processors.metadata_generator import MetadataGenerator
from src.data.database_manager import DatabaseManager
from src.services.satellite_search import SatelliteAvailabilitySearch
from src.utils.helpers import (
    validate_plot_data, 
    create_output_directory,
    rate_limit_request,
    log_processing_stats,
    save_processing_metadata
)

logger = logging.getLogger(__name__)

class SatelliteMonitoringPipeline:
    """Main pipeline for satellite agriculture monitoring."""
    
    def __init__(self, config: Config):
        self.config = config
        self.auth = CopernicusAuth(config)
        self.api_client = APIClient(config, self.auth)
        self.satellite_processor = SatelliteProcessor(config)
        self.indices_calculator = IndicesCalculator(config)
        self.parallel_processor = ParallelPlotProcessor(config)
        self.metadata_generator = MetadataGenerator(config)
        self.db_manager = DatabaseManager()
        self.satellite_search = SatelliteAvailabilitySearch(self.auth)
        
    def run(self):
        """Execute the complete monitoring pipeline."""
        logger.info("Starting satellite agriculture monitoring pipeline")
        
        try:
            # Step 1: Fetch plot boundaries
            plots_data = self.api_client.fetch_plots()
            
            if not plots_data:
                logger.warning("No plots data received")
                return
            
            logger.info(f"Processing {len(plots_data)} plots")
            
            # Process plots in batches to optimize CPU usage
            batch_size = self.config.BATCH_SIZE
            for batch_start in range(0, len(plots_data), batch_size):
                batch_end = min(batch_start + batch_size, len(plots_data))
                batch = plots_data[batch_start:batch_end]
                
                logger.info(f"Processing batch {batch_start//batch_size + 1}: plots {batch_start+1}-{batch_end}")
                
                for i, plot_data in enumerate(batch):
                    try:
                        global_index = batch_start + i
                        plot_id = plot_data["properties"]["plot_id"]
                        logger.info(f"Processing plot {global_index+1}/{len(plots_data)}: {plot_id}")
                        self._process_single_plot(plot_data)
                        
                        # Rate limiting between plots
                        if global_index < len(plots_data) - 1:
                            rate_limit_request(self.config.REQUEST_DELAY)
                            
                    except Exception as e:
                        plot_id = plot_data.get("properties", {}).get("plot_id", "unknown")
                        logger.error(f"Failed to process plot {plot_id}: {str(e)}")
                        continue
                
                # Longer pause between batches to prevent CPU overload
                if batch_end < len(plots_data):
                    logger.info(f"Batch completed. Pausing before next batch...")
                    time.sleep(self.config.REQUEST_DELAY * 2)
            
            logger.info("Pipeline execution completed")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise
    
    def _process_single_plot(self, plot_data: Dict[str, Any]):
        """Process a single plot through the complete pipeline."""
        start_time = time.time()
        
        # Validate plot data
        if not validate_plot_data(plot_data):
            raise ValueError("Invalid plot data")
        
        plot_code = plot_data["properties"]["plot_id"]
        planting_date = plot_data["properties"]["planting_date"]
        
        logger.info(f"Processing plot {plot_code} with planting date {planting_date}")
        
        # Save plot metadata to database
        self.db_manager.save_plot_metadata(plot_data)
        
        # Search for actual available satellite data dates on Copernicus
        search_dates = self.satellite_search.get_dates_for_plot_season(plot_data)
        
        if not search_dates:
            logger.warning(f"No satellite data found on Copernicus for plot {plot_code}, skipping")
            return
            
        logger.info(f"Found {len(search_dates)} available satellite dates on Copernicus for plot {plot_code}")
        
        successful_dates = []
        
        # Process each date with database optimization
        for date_str in search_dates:
            try:
                # Check if already processed to avoid redundant downloads
                if self.db_manager.is_already_processed(plot_code, date_str):
                    logger.info(f"Skipping {date_str} for plot {plot_code} - already processed")
                    successful_dates.append(date_str)
                    continue
                
                logger.info(f"Processing date {date_str} for plot {plot_code}")
                processing_start = time.time()
                
                # Step 2: Download satellite image as TIFF file
                tiff_file_path = self.api_client.download_satellite_image(plot_data, date_str)
                
                # Step 3: Process satellite data to extract bands from TIFF
                bands_data = self.satellite_processor.process_satellite_data(
                    tiff_file_path, plot_code, date_str
                )
                
                # Step 4: Calculate vegetation indices
                indices_data = self.indices_calculator.calculate_all_indices(
                    bands_data, plot_code, date_str
                )
                
                # Step 5: Save results
                output_path = self._save_results(plot_data, date_str, bands_data, indices_data)
                
                # Get file size for database record
                import os
                file_size = os.path.getsize(tiff_file_path) if os.path.exists(tiff_file_path) else 0
                
                # Save processing record to database
                processing_time = time.time() - processing_start
                self.db_manager.save_processing_record(
                    plot_code, date_str, date_str, file_size,
                    processing_time, list(indices_data.keys()), str(output_path)
                )
                
                # Clean up temporary TIFF file
                try:
                    import shutil
                    import tempfile
                    if tiff_file_path.startswith(tempfile.gettempdir()):
                        shutil.rmtree(os.path.dirname(tiff_file_path), ignore_errors=True)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary file: {cleanup_error}")
                
                successful_dates.append(date_str)
                
                # Rate limiting between date requests
                rate_limit_request(self.config.REQUEST_DELAY)
                
            except Exception as e:
                logger.warning(f"Failed to process date {date_str} for plot {plot_code}: {str(e)}")
                continue
        
        # Update plot processing statistics in database
        self.db_manager.update_plot_processing_stats(plot_code, len(successful_dates))
        
        # Log processing statistics
        processing_time = time.time() - start_time
        log_processing_stats(
            plot_code, 
            f"{len(successful_dates)} dates", 
            self.config.INDICES,
            processing_time
        )
        
        if not successful_dates:
            logger.warning(f"No successful processing for plot {plot_code}")
    
    def _save_results(self, plot_data: Dict[str, Any], date_str: str, 
                     bands_data: Dict[str, Any], indices_data: Dict[str, Any]) -> Path:
        """Save processed results to disk and return output directory path."""
        plot_code = plot_data["properties"]["plot_id"]
        
        # Create output directory structure: {plotcode}/{date}/
        output_dir = create_output_directory(
            self.config.OUTPUT_DIR, 
            plot_code, 
            date_str
        )
        
        logger.info(f"Saving results to {output_dir}")
        
        # Get profile for GeoTIFF creation
        profile = bands_data.get('profile', {})
        
        # Save each vegetation index
        for index_name, index_data in indices_data.items():
            try:
                output_path = output_dir / f"{index_name}.tif"
                
                self.indices_calculator.save_index(
                    index_data, 
                    output_path, 
                    profile, 
                    index_name
                )
                
            except Exception as e:
                logger.error(f"Failed to save {index_name} for plot {plot_code}: {str(e)}")
                continue
        
        # Save processing metadata
        processing_info = {
            "date_processed": datetime.now().isoformat(),
            "indices_calculated": list(indices_data.keys()),
            "satellite_data_date": date_str,
            "image_dimensions": f"{self.config.IMAGE_WIDTH}x{self.config.IMAGE_HEIGHT}",
            "max_cloud_coverage": self.config.MAX_CLOUD_COVERAGE
        }
        
        save_processing_metadata(output_dir, plot_data, processing_info)
        
        logger.info(f"Successfully saved {len(indices_data)} indices for plot {plot_code} on {date_str}")
        return output_dir
