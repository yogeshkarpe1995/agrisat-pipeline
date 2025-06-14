"""
Satellite image processing and data handling.
"""

import logging
import rasterio
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
import tempfile
import zipfile
import io
from .quality_filter import ImageQualityFilter

logger = logging.getLogger(__name__)

class SatelliteProcessor:
    """Process satellite imagery and extract band data."""
    
    def __init__(self, config):
        self.config = config
        self.quality_filter = ImageQualityFilter(config)
        
    def process_satellite_data(self, tiff_file_path: str, plot_code: str, date_str: str) -> Dict[str, np.ndarray]:
        """Process satellite image data from TIFF file and extract bands."""
        logger.info(f"Processing satellite data for plot {plot_code} on {date_str}")
        
        try:
            # Extract bands directly from TIFF file
            bands_data = self._extract_bands_from_tiff(tiff_file_path)
            
            # Apply cloud masking and quality filtering
            bands_data = self.quality_filter.apply_cloud_mask(bands_data)
            
            # Assess image quality
            quality_metrics = self.quality_filter.assess_image_quality(bands_data)
            
            # Check if image meets quality standards
            if not self.quality_filter.filter_by_quality(bands_data, 'acceptable'):
                logger.warning(f"Image quality below threshold for plot {plot_code} on {date_str}: "
                             f"{quality_metrics['overall_quality']}")
                # Return with quality warning but still process
                bands_data['quality_warning'] = True
                bands_data['quality_metrics'] = quality_metrics
            else:
                logger.info(f"Image quality: {quality_metrics['overall_quality']} "
                           f"(cloud: {quality_metrics['cloud_coverage']:.1f}%)")
                bands_data['quality_metrics'] = quality_metrics
            
            logger.info(f"Successfully extracted {len([k for k in bands_data.keys() if k not in ['profile', 'cloud_coverage', 'cloud_mask', 'quality_metrics', 'quality_warning']])} bands")
            return bands_data
            
        except Exception as e:
            logger.error(f"Failed to process satellite data: {str(e)}")
            raise Exception(f"Satellite data processing failed: {str(e)}")
    
    def _extract_bands_from_tiff(self, tiff_file_path: str) -> Dict[str, np.ndarray]:
        """Extract band data from TIFF file."""
        bands_data = {}
        
        try:
            with rasterio.open(tiff_file_path) as dataset:
                logger.info(f"TIFF file has {dataset.count} bands, dimensions: {dataset.width}x{dataset.height}")
                
                # Enhanced band mapping with SCL for advanced cloud masking
                band_mapping = {
                    1: "B02",   # Blue - for True Color
                    2: "B03",   # Green - for True Color  
                    3: "B04",   # Red - for NDVI, MSAVI, True Color
                    4: "B05",   # Red Edge - for NDRE
                    5: "B08",   # NIR - for NDVI, NDRE, MSAVI
                    6: "B11",   # SWIR1 - for NDMI
                    7: "SCL"    # Scene Classification Layer - for cloud masking
                }
                
                # Read enhanced bands (7 bands: 6 spectral + SCL)
                for i in range(1, min(dataset.count + 1, 8)):  # Max 7 bands with SCL
                    band_data = dataset.read(i)
                    band_name = band_mapping.get(i, f"B{i:02d}")
                    bands_data[band_name] = band_data
                    logger.debug(f"Extracted band {band_name}: shape {band_data.shape}")
                    
                # Store metadata
                bands_data['profile'] = dataset.profile
                logger.info(f"Successfully extracted {len(bands_data)-1} bands from TIFF")
                
        except Exception as e:
            logger.error(f"Failed to extract bands from TIFF: {str(e)}")
            raise
            
        return bands_data
    
    def _extract_from_zip(self, zip_data: bytes) -> Dict[str, np.ndarray]:
        """Extract bands from zip file response."""
        bands_data = {}
        
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
                for filename in zip_file.namelist():
                    if filename.endswith('.tif'):
                        with tempfile.NamedTemporaryFile(suffix='.tif') as temp_file:
                            temp_file.write(zip_file.read(filename))
                            temp_file.flush()
                            
                            with rasterio.open(temp_file.name) as dataset:
                                for i in range(1, dataset.count + 1):
                                    band_data = dataset.read(i)
                                    bands_data[f"B{i:02d}"] = band_data
                                    
                                bands_data['profile'] = dataset.profile
                                break
                                
        except Exception as e:
            logger.error(f"Failed to extract from zip: {str(e)}")
            raise
            
        return bands_data
    
    def _create_synthetic_bands(self) -> Dict[str, np.ndarray]:
        """Create synthetic band data for testing when real data is unavailable."""
        logger.warning("Creating synthetic band data for processing")
        
        # Create synthetic bands with realistic Sentinel-2 characteristics
        width, height = self.config.IMAGE_WIDTH, self.config.IMAGE_HEIGHT
        bands_data = {}
        
        # Enhanced bands with SCL for cloud masking (7 bands)
        band_configs = {
            'B02': (0, 4000),    # Blue - for True Color
            'B03': (0, 4000),    # Green - for True Color
            'B04': (0, 4000),    # Red - for NDVI, MSAVI, True Color
            'B05': (0, 4000),    # Red Edge - for NDRE
            'B08': (0, 4000),    # NIR - for NDVI, NDRE, MSAVI
            'B11': (0, 4000),    # SWIR1 - for NDMI
            'SCL': (0, 11),      # Scene Classification Layer - for cloud masking
        }
        
        np.random.seed(42)  # For reproducible synthetic data
        
        for band_name, (min_val, max_val) in band_configs.items():
            # Create synthetic band with some spatial structure
            base_data = np.random.rand(height, width)
            # Add some spatial correlation
            from scipy import ndimage
            base_data = ndimage.gaussian_filter(base_data, sigma=2)
            # Scale to appropriate range
            band_data = (base_data * (max_val - min_val) + min_val).astype(np.uint16)
            bands_data[band_name] = band_data
        
        # Add profile for GeoTIFF creation
        bands_data['profile'] = {
            'driver': 'GTiff',
            'interleave': 'band',
            'tiled': False,
            'nodata': None,
            'width': width,
            'height': height,
            'count': 1,
            'dtype': rasterio.uint16,
            'compress': 'lzw'
        }
        
        return bands_data
    
    def save_band_data(self, bands_data: Dict[str, np.ndarray], output_path: Path, band_name: str):
        """Save band data as GeoTIFF."""
        if band_name not in bands_data:
            raise ValueError(f"Band {band_name} not found in data")
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get the base profile and update for single band
        profile = bands_data.get('profile', {})
        profile.update({
            'count': 1,
            'dtype': rasterio.uint16,
            'compress': 'lzw'
        })
        
        try:
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(bands_data[band_name], 1)
                
            logger.info(f"Saved {band_name} data to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save band data: {str(e)}")
            raise
