"""
Utility functions for the satellite monitoring pipeline.
"""

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)

def validate_plot_data(plot_data: Dict[str, Any]) -> bool:
    """Validate that plot data contains required fields."""
    # Check for GeoJSON structure
    if "type" not in plot_data or plot_data["type"] != "Feature":
        logger.error("Plot data is not a valid GeoJSON Feature")
        return False
    
    if "properties" not in plot_data or "geometry" not in plot_data:
        logger.error("Plot data missing required GeoJSON fields")
        return False
    
    properties = plot_data["properties"]
    geometry = plot_data["geometry"]
    
    # Check required properties
    if "plot_id" not in properties:
        logger.error("Plot data missing plot_id in properties")
        return False
    
    if "planting_date" not in properties:
        logger.error("Plot data missing planting_date in properties")
        return False
    
    # Validate geometry structure
    if not isinstance(geometry, dict) or "coordinates" not in geometry:
        logger.error("Plot geometry is invalid")
        return False
    
    # Validate planting date format
    try:
        datetime.strptime(properties["planting_date"], "%Y-%m-%d")
    except ValueError:
        logger.error("Planting date format is invalid, expected YYYY-MM-DD")
        return False
    
    return True

def get_date_range_from_planting(planting_date: str, 
                                harvest_date: str = None,
                                days_before: int = 0, 
                                days_after: int = 30,
                                plot_data = None,
                                api_client = None) -> List[str]:
    """Get actual available satellite data dates from Copernicus for the specified plot and date range."""
    planting_dt = datetime.strptime(planting_date, "%Y-%m-%d")
    
    if harvest_date:
        end_date = datetime.strptime(harvest_date, "%Y-%m-%d")
    else:
        # Default to 120 days after planting for crop monitoring
        end_date = planting_dt + timedelta(days=120)
    
    start_date = planting_dt - timedelta(days=days_before)
    
    # If no API client or plot data provided, fall back to regular interval dates
    if not api_client or not plot_data:
        logger.warning("No API client or plot data provided, using regular interval dates")
        return _generate_interval_dates(start_date, end_date)
    
    try:
        # Search for actual satellite data availability on Copernicus
        available_dates = _search_available_satellite_dates(
            plot_data, start_date, end_date, api_client
        )
        
        if not available_dates:
            logger.warning("No satellite data found on Copernicus, using regular interval dates")
            return _generate_interval_dates(start_date, end_date)
        
        logger.info(f"Found {len(available_dates)} available satellite dates on Copernicus")
        return available_dates
        
    except Exception as e:
        logger.error(f"Failed to search Copernicus for available dates: {str(e)}")
        logger.warning("Falling back to regular interval dates")
        return _generate_interval_dates(start_date, end_date)

def _generate_interval_dates(start_date: datetime, end_date: datetime) -> List[str]:
    """Generate dates at regular intervals as fallback."""
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=14)  # Bi-weekly intervals
    
    return dates

def _search_available_satellite_dates(plot_data: dict, start_date: datetime, 
                                    end_date: datetime, api_client) -> List[str]:
    """Search Copernicus for actual available satellite data dates."""
    from datetime import datetime
    
    # Get coordinates from plot geometry
    coordinates = plot_data["geometry"]["coordinates"][0]
    
    # Create bounding box from coordinates
    lons = [coord[0] for coord in coordinates]
    lats = [coord[1] for coord in coordinates]
    bbox = [min(lons), min(lats), max(lons), max(lats)]
    
    # Search parameters for Copernicus
    search_params = {
        "$filter": f"Collection/Name eq 'SENTINEL-2' and "
                  f"ContentDate/Start ge {start_date.strftime('%Y-%m-%d')}T00:00:00.000Z and "
                  f"ContentDate/Start le {end_date.strftime('%Y-%m-%d')}T23:59:59.999Z and "
                  f"OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(({bbox[0]} {bbox[1]},{bbox[2]} {bbox[1]},{bbox[2]} {bbox[3]},{bbox[0]} {bbox[3]},{bbox[0]} {bbox[1]}))')",
        "$orderby": "ContentDate/Start asc",
        "$top": "100"
    }
    
    try:
        import requests
        response = requests.get(
            "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
            params=search_params,
            headers=api_client.auth.get_headers() if hasattr(api_client, 'auth') else {},
            timeout=30
        )
        response.raise_for_status()
        
        search_results = response.json()
        products = search_results.get("value", [])
        
        # Extract unique dates from available products
        available_dates = set()
        for product in products:
            if "ContentDate" in product and "Start" in product["ContentDate"]:
                date_str = product["ContentDate"]["Start"][:10]  # Extract YYYY-MM-DD
                available_dates.add(date_str)
        
        # Sort dates and return as list
        return sorted(list(available_dates))
        
    except Exception as e:
        logger.error(f"Copernicus search failed: {str(e)}")
        raise

def create_output_directory(base_dir: Path, plot_code: str, date_str: str) -> Path:
    """Create output directory structure for plot data."""
    output_dir = base_dir / plot_code / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def safe_file_write(file_path: Path, content: bytes):
    """Safely write content to file with error handling."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(content)
            
        logger.debug(f"Successfully wrote {len(content)} bytes to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to write file {file_path}: {str(e)}")
        raise

def rate_limit_request(delay: float):
    """Apply rate limiting between requests."""
    time.sleep(delay)

def log_processing_stats(plot_code: str, date_str: str, 
                        indices_calculated: List[str], 
                        processing_time: float):
    """Log statistics about processing results."""
    logger.info(
        f"Processing completed for plot {plot_code} on {date_str}: "
        f"{len(indices_calculated)} indices calculated in {processing_time:.2f}s"
    )

def save_processing_metadata(output_dir: Path, plot_data: Dict[str, Any], 
                           processing_info: Dict[str, Any]):
    """Save metadata about the processing run."""
    metadata = {
        "plot_data": plot_data,
        "processing_info": processing_info,
        "timestamp": datetime.now().isoformat()
    }
    
    metadata_path = output_dir / "metadata.json"
    
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.debug(f"Saved processing metadata to {metadata_path}")
        
    except Exception as e:
        logger.warning(f"Failed to save metadata: {str(e)}")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def cleanup_temp_files(temp_dir: Path):
    """Clean up temporary files created during processing."""
    try:
        if temp_dir.exists():
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    file_path.unlink()
            temp_dir.rmdir()
            logger.debug(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp files: {str(e)}")
