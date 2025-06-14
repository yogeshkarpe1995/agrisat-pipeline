"""
Satellite data availability search for Copernicus Dataspace.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SatelliteAvailabilitySearch:
    """Search for available Sentinel-2 data on Copernicus Dataspace."""
    
    def __init__(self, auth_handler=None):
        self.auth_handler = auth_handler
        self.search_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    
    def get_available_dates(self, plot_data: Dict[str, Any], 
                           start_date: str, end_date: str,
                           max_cloud_coverage: int = 100) -> List[str]:
        """
        Search for available Sentinel-2 dates for a specific plot.
        
        Args:
            plot_data: Plot geometry and metadata
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_cloud_coverage: Maximum cloud coverage percentage
            
        Returns:
            List of available dates in YYYY-MM-DD format
        """
        try:
            # Get coordinates from plot geometry
            coordinates = plot_data["geometry"]["coordinates"][0]
            
            # Create bounding box
            lons = [coord[0] for coord in coordinates]
            lats = [coord[1] for coord in coordinates]
            bbox = [min(lons), min(lats), max(lons), max(lats)]
            
            # Build search filter
            polygon_wkt = f"POLYGON(({bbox[0]} {bbox[1]},{bbox[2]} {bbox[1]},{bbox[2]} {bbox[3]},{bbox[0]} {bbox[3]},{bbox[0]} {bbox[1]}))"
            
            search_filter = (
                f"Collection/Name eq 'SENTINEL-2' and "
                f"ContentDate/Start ge {start_date}T00:00:00.000Z and "
                f"ContentDate/Start le {end_date}T23:59:59.999Z and "
                f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {max_cloud_coverage}) and "
                f"OData.CSC.Intersects(area=geography'SRID=4326;{polygon_wkt}')"
            )
            
            search_params = {
                "$filter": search_filter,
                "$orderby": "ContentDate/Start asc",
                "$top": "200"  # Increased limit for comprehensive search
            }
            
            headers = {}
            if self.auth_handler and hasattr(self.auth_handler, 'get_headers'):
                headers = self.auth_handler.get_headers()
            
            logger.info(f"Searching Copernicus for Sentinel-2 data from {start_date} to {end_date}")
            
            response = requests.get(
                self.search_url,
                params=search_params,
                headers=headers,
                timeout=30
            )
            
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"Status Code: {response.status_code}")
                print(f"Response Text: {response.text}")
                print(f"Response Headers: {response.headers}")
                raise
            
            search_results = response.json()
            products = search_results.get("value", [])
            
            # Extract unique dates from products
            available_dates = set()
            for product in products:
                if "ContentDate" in product and "Start" in product["ContentDate"]:
                    date_str = product["ContentDate"]["Start"][:10]  # Extract YYYY-MM-DD
                    available_dates.add(date_str)
            
            sorted_dates = sorted(list(available_dates))
            logger.info(f"Found {len(sorted_dates)} available dates on Copernicus")
            
            return sorted_dates
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Copernicus API request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Failed to search satellite availability: {str(e)}")
            return []
    
    def get_dates_for_plot_season(self, plot_data: Dict[str, Any]) -> List[str]:
        """
        Get available satellite dates for the entire growing season of a plot.
        
        Args:
            plot_data: Plot data with planting and harvest dates
            
        Returns:
            List of available dates covering the growing season
        """
        planting_date = plot_data["properties"].get("planting_date")
        harvest_date = plot_data["properties"].get("harvest_date")
        
        if not planting_date:
            logger.error("No planting date provided for plot")
            return []
        
        # Parse planting date
        planting_dt = datetime.strptime(planting_date, "%Y-%m-%d")
        
        # Determine end date
        if harvest_date:
            end_dt = datetime.strptime(harvest_date, "%Y-%m-%d")
        else:
            # Default to 4 months after planting if no harvest date
            end_dt = planting_dt + timedelta(days=120)
        
        # Extend search period slightly before and after
        start_search = planting_dt - timedelta(days=7)
        end_search = end_dt + timedelta(days=7)
        
        return self.get_available_dates(
            plot_data,
            start_search.strftime("%Y-%m-%d"),
            end_search.strftime("%Y-%m-%d")
        )