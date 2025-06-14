"""
API client for external services and Copernicus data access.
"""

import requests
import logging
import time
from typing import List, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class APIClient:
    """Client for interacting with external APIs."""
    
    def __init__(self, config, auth_handler):
        self.config = config
        self.auth = auth_handler
        self.session = requests.Session()
        
    def fetch_plots(self) -> List[Dict[str, Any]]:
        """Fetch plot boundaries from external API."""
        logger.info("Fetching plot data from external API")
        
        try:
            response = self.session.get(self.config.PLOTS_API_URL)
            response.raise_for_status()
            
            plots_data = response.json()
            logger.info(f"Successfully fetched {len(plots_data)} plots")
            return plots_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch plots: {str(e)}")
            raise Exception(f"Failed to fetch plot data: {str(e)}")
    
    def search_satellite_data(self, plot_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for Sentinel-2 data for a specific plot."""
        plot_id = plot_data["properties"]["plot_id"]
        logger.info(f"Searching satellite data for plot {plot_id}")
        
        # Extract plot information
        geometry = plot_data["geometry"]
        planting_date = plot_data["properties"]["planting_date"]
        
        if not geometry or not planting_date:
            raise ValueError("Plot data missing geometry or planting_date")
        
        # Convert planting date to search range
        from_date = datetime.strptime(planting_date, self.config.DATE_FORMAT)
        to_date = datetime.now()
        
        # Build search query
        search_params = {
            "$filter": f"startswith(Name,'S2') and "
                      f"ContentDate/Start ge {from_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')} and "
                      f"ContentDate/Start le {to_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')} and "
                      f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {self.config.MAX_CLOUD_COVERAGE})",
            "$orderby": "ContentDate/Start desc",
            "$top": "100"
        }
        
        try:
            response = self.session.get(
                self.config.COPERNICUS_SEARCH_URL,
                params=search_params,
                headers=self.auth.get_headers()
            )
            response.raise_for_status()
            
            search_results = response.json()
            products = search_results.get("value", [])
            
            logger.info(f"Found {len(products)} satellite images for plot")
            return products
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to search satellite data: {str(e)}")
            raise Exception(f"Satellite data search failed: {str(e)}")
    
    def ensure_closed_polygon(coordinates: List[List[float]], tolerance: float = 1e-10) -> List[List[float]]:
        """
        Single function to ensure polygon is closed. Returns closed polygon if not already closed.
        
        Args:
            coordinates: List of [lon, lat] coordinate pairs
            tolerance: Tolerance for comparing coordinate equality (default: 1e-10)
        
        Returns:
            List of coordinates with guaranteed closed ring
        
        Raises:
            ValueError: If coordinates list is empty or has less than 3 points
        """
        if not coordinates:
            raise ValueError("Coordinates list cannot be empty")
        
        if len(coordinates) < 3:
            raise ValueError("Polygon ring must have at least 3 points")
        
        # Check if already closed
        first_point = coordinates[0]
        last_point = coordinates[-1]
        
        # Calculate distance between first and last points
        if len(first_point) >= 2 and len(last_point) >= 2:
            distance = ((first_point[0] - last_point[0]) ** 2 + 
                    (first_point[1] - last_point[1]) ** 2) ** 0.5
            
            # If not closed, return closed version
            if distance > tolerance:
                return coordinates + [first_point]
        
        # Already closed, return as is
        return coordinates


    def download_satellite_image(self, plot_data: Dict[str, Any], date_str: str) -> str:
        """Download satellite image and save as raw TIFF file."""
        plot_id = plot_data["properties"]["plot_id"]
        logger.info(f"Downloading satellite image for plot {plot_id} on {date_str}")
        
        # Get coordinates from plot geometry
        coordinates = plot_data["geometry"]["coordinates"][0]
        
        # Ensure it's closed (returns closed polygon if not already closed)
        closed_coordinates = APIClient.ensure_closed_polygon(coordinates)

        # Parse date
        date_obj = datetime.strptime(date_str, self.config.DATE_FORMAT)
        date_from = date_obj.strftime("%Y-%m-%d")
        date_to = (date_obj.replace(hour=23, minute=59, second=59)).strftime("%Y-%m-%d")
        
        # Enhanced evalscript - essential bands + SCL for advanced cloud masking
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: [
                {
                    bands: [
                    "B02",  // Blue - for True Color
                    "B03",  // Green - for True Color
                    "B04",  // Red - for NDVI, MSAVI, True Color
                    "B05",  // Red Edge - for NDRE
                    "B08",  // NIR - for NDVI, NDRE, MSAVI
                    "B11",  // SWIR1 - for NDMI
                    "SCL"   // Scene Classification Layer - for advanced cloud masking
                    ],
                    units: "DN",
                },
                ],
                output: {
                    id: "default",
                    bands: 7,
                    sampleType: SampleType.UINT16,
                },
            };
        }

        function evaluatePixel(sample) {
            return [
                sample.B02,  // Blue
                sample.B03,  // Green
                sample.B04,  // Red
                sample.B05,  // Red Edge
                sample.B08,  // NIR
                sample.B11,  // SWIR1
                sample.SCL   // Scene Classification Layer
            ];
        }
        """
        
        # Build request payload for TIFF format
        request_payload = {
            "input": {
                "bounds": {
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
                    "geometry": {
                        "coordinates": [closed_coordinates],
                        "type": "Polygon"
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{date_from}T00:00:00Z",
                                "to": f"{date_to}T23:59:59Z",
                            },
                            "maxCloudCoverage": self.config.MAX_CLOUD_COVERAGE,
                        },
                        "processing": {"harmonizeValues": False},
                    }
                ],
            },
            "output": {
                "width": self.config.IMAGE_WIDTH,
                "height": self.config.IMAGE_HEIGHT,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {"type": "image/tiff"},
                    }
                ],
            },
            "evalscript": evalscript,
        }
        
        #print(json.dumps(request_payload, indent=2))  # Debugging output
        
        try:
            response = self.session.post(
                self.config.COPERNICUS_DOWNLOAD_URL,
                json=request_payload,
                headers=self.auth.get_headers()
            )
            
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"Status Code: {response.status_code}")
                print(f"Response Text: {response.text}")
                print(f"Response Headers: {response.headers}")
                raise
            
            # Save as raw TIFF file
            import tempfile
            import os
            
            temp_dir = tempfile.mkdtemp()
            raw_tiff_path = os.path.join(temp_dir, f"{plot_id}_{date_str}_raw.tif")
            
            with open(raw_tiff_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully downloaded and saved satellite image as {raw_tiff_path} ({len(response.content)} bytes)")
            return raw_tiff_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download satellite image: {str(e)}")
            raise Exception(f"Satellite image download failed: {str(e)}")
    
    def _retry_request(self, func, *args, **kwargs):
        """Retry a request with exponential backoff."""
        for attempt in range(self.config.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < self.config.MAX_RETRIES - 1:
                    wait_time = (2 ** attempt) * self.config.REQUEST_DELAY
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    raise e
