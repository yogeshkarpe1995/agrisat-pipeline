"""
Calculate vegetation indices from satellite band data.
"""

import logging
import numpy as np
import rasterio
from pathlib import Path
from typing import Dict, Any
from src.processors.satellite_processor import SatelliteProcessor

logger = logging.getLogger(__name__)

class IndicesCalculator:
    """Calculate various vegetation indices from satellite bands."""
    
    def __init__(self, config):
        self.config = config
        
    def calculate_all_indices(self, bands_data: Dict[str, np.ndarray], 
                            plot_code: str, date_str: str) -> Dict[str, np.ndarray]:
        """Calculate all configured vegetation indices."""
        logger.info(f"Calculating vegetation indices for plot {plot_code} on {date_str}")
        
        indices = {}
        
        try:
            # Calculate each index
            if "NDVI" in self.config.INDICES:
                indices["NDVI"] = self._calculate_ndvi(bands_data)
                
            if "NDRE" in self.config.INDICES:
                indices["NDRE"] = self._calculate_ndre(bands_data)
                
            if "NDWI" in self.config.INDICES:
                indices["NDWI"] = self._calculate_ndwi(bands_data)
                
            if "MSAVI" in self.config.INDICES:
                indices["MSAVI"] = self._calculate_msavi(bands_data)
                
            if "NDMI" in self.config.INDICES:
                indices["NDMI"] = self._calculate_ndmi(bands_data)
                
            if "TrueColor" in self.config.INDICES:
                indices["TrueColor"] = self._calculate_true_color(bands_data)
            
            logger.info(f"Calculated {len(indices)} vegetation indices")
            return indices
            
        except Exception as e:
            logger.error(f"Failed to calculate indices: {str(e)}")
            raise Exception(f"Vegetation indices calculation failed: {str(e)}")
    
    def _calculate_ndvi(self, bands_data: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate Normalized Difference Vegetation Index (NDVI).
        
        NDVI = (NIR - RED) / (NIR + RED)
        Uses B08 (NIR) and B04 (RED)
        """
        logger.debug("Calculating NDVI")
        
        nir = bands_data["B08"].astype(np.float32)
        red = bands_data["B04"].astype(np.float32)
        
        # Avoid division by zero
        denominator = nir + red
        ndvi = np.where(denominator != 0, (nir - red) / denominator, 0)
        
        # Scale to 0-10000 range for UINT16 storage
        # ndvi_scaled = ((ndvi + 1) * 5000).astype(np.uint16)
        
        return ndvi
    
    def _calculate_ndre(self, bands_data: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate Normalized Difference Red Edge Index (NDRE).
        
        NDRE = (NIR - RedEdge) / (NIR + RedEdge)
        Uses B08 (NIR) and B05 (Red Edge)
        """
        logger.debug("Calculating NDRE")
        
        nir = bands_data["B08"].astype(np.float32)
        red_edge = bands_data["B05"].astype(np.float32)
        
        # Avoid division by zero
        denominator = nir + red_edge
        ndre = np.where(denominator != 0, (nir - red_edge) / denominator, 0)
        
        # Scale to 0-10000 range for UINT16 storage
        #ndre_scaled = ((ndre + 1) * 5000).astype(np.uint16)
        
        return ndre
    
    def _calculate_ndwi(self, bands_data: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate Normalized Difference Water Index (NDWI).
        
        NDWI = (GREEN - NIR) / (GREEN + NIR)
        Uses B03 (GREEN) and B08 (NIR)
        """
        logger.debug("Calculating NDWI")
        
        green = bands_data["B03"].astype(np.float32)
        nir = bands_data["B08"].astype(np.float32)
        
        # Avoid division by zero
        denominator = green + nir
        ndwi = np.where(denominator != 0, (green - nir) / denominator, 0)
        
        # Scale to 0-10000 range for UINT16 storage
        # ndwi_scaled = ((ndwi + 1) * 5000).astype(np.uint16)
        
        return ndwi
    
    def _calculate_msavi(self, bands_data: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate Modified Soil Adjusted Vegetation Index (MSAVI).
        
        MSAVI = (2 * NIR + 1 - sqrt((2 * NIR + 1)^2 - 8 * (NIR - RED))) / 2
        Uses B08 (NIR) and B04 (RED)
        """
        logger.debug("Calculating MSAVI")
        
        nir = bands_data["B08"].astype(np.float32)
        red = bands_data["B04"].astype(np.float32)
        
        # Normalize to 0-1 range for calculation
        nir_norm = nir / 10000.0
        red_norm = red / 10000.0
        
        # Calculate MSAVI
        term1 = 2 * nir_norm + 1
        term2 = np.sqrt(term1**2 - 8 * (nir_norm - red_norm))
        msavi = (term1 - term2) / 2
        
        # Handle potential negative values under square root
        msavi = np.where(np.isfinite(msavi), msavi, 0)
        msavi = np.clip(msavi, 0, 1)
        
        # Scale to 0-10000 range for UINT16 storage
        # msavi_scaled = (msavi * 10000).astype(np.uint16)
        
        return msavi
    
    def _calculate_ndmi(self, bands_data: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate Normalized Difference Moisture Index (NDMI).
        
        NDMI = (NIR - SWIR1) / (NIR + SWIR1)
        Uses B08 (NIR) and B11 (SWIR1)
        """
        logger.debug("Calculating NDMI")
        
        nir = bands_data["B08"].astype(np.float32)
        swir1 = bands_data["B11"].astype(np.float32)
        
        # Avoid division by zero
        denominator = nir + swir1
        ndmi = np.where(denominator != 0, (nir - swir1) / denominator, 0)
        
        # Clip to valid range [-1, 1]
        ndmi = np.clip(ndmi, -1, 1)
        
        return ndmi
    
    def _calculate_true_color(self, bands_data: Dict[str, np.ndarray]) -> np.ndarray:
        """Create True Color composite.
        
        Uses B04 (RED), B03 (GREEN), B02 (BLUE)
        Returns 3-band RGB composite
        """
        logger.debug("Calculating True Color composite")
        
        red = bands_data["B04"]
        green = bands_data["B03"]
        blue = bands_data["B02"]
        
        # Stack bands to create RGB composite
        rgb_composite = np.stack([red, green, blue], axis=0)
        
        return rgb_composite
    
    def save_index(self, index_data: np.ndarray, output_path: Path, 
                   profile: Dict[str, Any], index_name: str):
        """Save calculated index as GeoTIFF."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update profile for the specific index
        index_profile = profile.copy()
        
        if index_name == "TrueColor":
            # RGB composite has 3 bands
            index_profile.update({
                'count': 3,
                'dtype': rasterio.uint16,
                'compress': 'lzw'
            })
        else:
            # Single band indices
            index_profile.update({
                'count': 1,
                'dtype': rasterio.float32,
                'compress': 'lzw'
            })
        
        try:
            with rasterio.open(output_path, 'w', **index_profile) as dst:
                if index_name == "TrueColor":
                    # Write all 3 bands for RGB composite
                    for i in range(3):
                        dst.write(index_data[i], i + 1)
                else:
                    # Write single band
                    dst.write(index_data, 1)
                    
            logger.info(f"Saved {index_name} index to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save {index_name} index: {str(e)}")
            raise
