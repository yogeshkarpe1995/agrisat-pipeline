"""
Cloud masking and image quality filtering for satellite imagery.
"""

import logging
import numpy as np
import rasterio
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ImageQualityFilter:
    """Filter satellite images based on cloud coverage and quality metrics."""
    
    def __init__(self, config):
        self.config = config
        self.max_cloud_coverage = getattr(config, 'MAX_CLOUD_COVERAGE', 20)
        self.min_data_coverage = getattr(config, 'MIN_DATA_COVERAGE', 80)  # Minimum % of valid pixels
        
    def apply_cloud_mask(self, bands_data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Apply cloud masking using SCL band and spectral analysis."""
        logger.info("Applying enhanced cloud masking to satellite imagery")
        
        try:
            # Check if SCL band is available for enhanced cloud masking
            if "SCL" in bands_data:
                cloud_mask = self._detect_clouds_with_scl(bands_data["SCL"])
                logger.info("Using SCL band for enhanced cloud detection")
            else:
                # Fallback to spectral analysis
                blue = bands_data.get("B02", np.zeros((256, 256)))
                green = bands_data.get("B03", np.zeros((256, 256)))
                red = bands_data.get("B04", np.zeros((256, 256)))
                nir = bands_data.get("B08", np.zeros((256, 256)))
                cloud_mask = self._detect_clouds_spectral(blue, green, red, nir)
                logger.info("Using spectral analysis for cloud detection")
            
            # Apply mask to all spectral bands (exclude SCL and metadata)
            masked_bands = {}
            excluded_keys = {'profile', 'cloud_coverage', 'cloud_mask', 'quality_metrics', 'quality_warning', 'SCL'}
            
            for band_name, band_data in bands_data.items():
                if band_name not in excluded_keys and isinstance(band_data, np.ndarray):
                    # Set cloudy pixels to NaN
                    masked_data = band_data.copy().astype(np.float32)
                    masked_data[cloud_mask] = np.nan
                    masked_bands[band_name] = masked_data
                else:
                    masked_bands[band_name] = band_data
            
            # Calculate cloud coverage percentage
            cloud_percentage = (np.sum(cloud_mask) / cloud_mask.size) * 100
            logger.info(f"Cloud coverage: {cloud_percentage:.1f}%")
            
            # Store cloud statistics
            masked_bands['cloud_coverage'] = cloud_percentage
            masked_bands['cloud_mask'] = cloud_mask
            
            return masked_bands
            
        except Exception as e:
            logger.error(f"Failed to apply cloud mask: {str(e)}")
            return bands_data
    
    def _detect_clouds_with_scl(self, scl_band: np.ndarray) -> np.ndarray:
        """Detect clouds using Sentinel-2 Scene Classification Layer (SCL).
        
        SCL Classification values:
        0 = No Data (black), 1 = Saturated or defective, 2 = Dark Area Pixels,
        3 = Cloud Shadows, 4 = Vegetation, 5 = Not Vegetated, 6 = Water,
        7 = Unclassified, 8 = Cloud Medium Probability, 9 = Cloud High Probability,
        10 = Thin Cirrus, 11 = Snow
        """
        logger.debug("Detecting clouds using SCL band")
        
        # Create cloud mask from SCL classifications
        cloud_classes = [3, 8, 9, 10]  # Cloud shadows, medium/high probability clouds, thin cirrus
        
        cloud_mask = np.isin(scl_band, cloud_classes)
        
        # Also include saturated/defective pixels and no data
        invalid_classes = [0, 1]  # No data, saturated/defective
        invalid_mask = np.isin(scl_band, invalid_classes)
        
        # Combine cloud and invalid pixel masks
        combined_mask = cloud_mask | invalid_mask
        
        # Apply morphological operations to clean up the mask
        from scipy import ndimage
        combined_mask = ndimage.binary_opening(combined_mask, structure=np.ones((2, 2)))
        combined_mask = ndimage.binary_closing(combined_mask, structure=np.ones((3, 3)))
        
        return combined_mask
    
    def _detect_clouds_spectral(self, blue: np.ndarray, green: np.ndarray, 
                               red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Detect clouds using spectral analysis (fallback method)."""
        
        # Convert to float to avoid overflow
        blue = blue.astype(np.float32)
        green = green.astype(np.float32)
        red = red.astype(np.float32)
        nir = nir.astype(np.float32)
        
        # Cloud detection criteria
        # 1. High reflectance in visible bands
        visible_threshold = 3000  # Adjust based on typical values
        high_visible = (blue > visible_threshold) & (green > visible_threshold) & (red > visible_threshold)
        
        # 2. Low NDVI (clouds have low vegetation index)
        ndvi = np.where((nir + red) != 0, (nir - red) / (nir + red), 0)
        low_ndvi = ndvi < 0.2
        
        # 3. Blue band dominance (clouds are often blue-white)
        blue_dominance = blue > (red * 1.1)
        
        # Combine criteria
        cloud_mask = high_visible & low_ndvi & blue_dominance
        
        # Morphological operations to clean up the mask
        from scipy import ndimage
        cloud_mask = ndimage.binary_opening(cloud_mask, structure=np.ones((3, 3)))
        cloud_mask = ndimage.binary_closing(cloud_mask, structure=np.ones((5, 5)))
        
        return cloud_mask
    
    def assess_image_quality(self, bands_data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Assess overall image quality metrics."""
        logger.debug("Assessing image quality")
        
        quality_metrics = {
            'overall_quality': 'good',
            'cloud_coverage': 0.0,
            'data_coverage': 100.0,
            'noise_level': 'low',
            'usable': True
        }
        
        try:
            # Get cloud coverage if available
            if 'cloud_coverage' in bands_data:
                quality_metrics['cloud_coverage'] = bands_data['cloud_coverage']
            
            # Calculate data coverage (non-NaN pixels)
            valid_data_percentages = []
            for band_name, band_data in bands_data.items():
                if band_name not in ['profile', 'cloud_coverage', 'cloud_mask'] and isinstance(band_data, np.ndarray):
                    valid_pixels = np.sum(~np.isnan(band_data))
                    total_pixels = band_data.size
                    valid_percentage = (valid_pixels / total_pixels) * 100
                    valid_data_percentages.append(valid_percentage)
            
            if valid_data_percentages:
                quality_metrics['data_coverage'] = np.mean(valid_data_percentages)
            
            # Determine if image is usable
            quality_metrics['usable'] = (
                quality_metrics['cloud_coverage'] <= self.max_cloud_coverage and
                quality_metrics['data_coverage'] >= self.min_data_coverage
            )
            
            # Overall quality assessment
            if quality_metrics['cloud_coverage'] <= 10 and quality_metrics['data_coverage'] >= 95:
                quality_metrics['overall_quality'] = 'excellent'
            elif quality_metrics['cloud_coverage'] <= 20 and quality_metrics['data_coverage'] >= 85:
                quality_metrics['overall_quality'] = 'good'
            elif quality_metrics['usable']:
                quality_metrics['overall_quality'] = 'acceptable'
            else:
                quality_metrics['overall_quality'] = 'poor'
            
            logger.info(f"Image quality: {quality_metrics['overall_quality']} "
                       f"(cloud: {quality_metrics['cloud_coverage']:.1f}%, "
                       f"data: {quality_metrics['data_coverage']:.1f}%)")
            
        except Exception as e:
            logger.error(f"Failed to assess image quality: {str(e)}")
            quality_metrics['usable'] = False
            quality_metrics['overall_quality'] = 'unknown'
        
        return quality_metrics
    
    def filter_by_quality(self, bands_data: Dict[str, np.ndarray], 
                         quality_threshold: str = 'acceptable') -> bool:
        """Filter image based on quality threshold."""
        
        quality_metrics = self.assess_image_quality(bands_data)
        
        quality_levels = ['poor', 'acceptable', 'good', 'excellent']
        threshold_index = quality_levels.index(quality_threshold)
        current_index = quality_levels.index(quality_metrics['overall_quality'])
        
        return current_index >= threshold_index and quality_metrics['usable']
    
    def enhance_image_quality(self, bands_data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Apply basic image enhancement techniques."""
        logger.debug("Applying image quality enhancement")
        
        enhanced_bands = {}
        
        try:
            for band_name, band_data in bands_data.items():
                if band_name not in ['profile', 'cloud_coverage', 'cloud_mask'] and isinstance(band_data, np.ndarray):
                    # Apply noise reduction and contrast enhancement
                    enhanced_data = self._enhance_band(band_data)
                    enhanced_bands[band_name] = enhanced_data
                else:
                    enhanced_bands[band_name] = band_data
            
            logger.info("Applied image quality enhancement")
            return enhanced_bands
            
        except Exception as e:
            logger.error(f"Failed to enhance image quality: {str(e)}")
            return bands_data
    
    def _enhance_band(self, band_data: np.ndarray) -> np.ndarray:
        """Apply enhancement to a single band."""
        
        # Skip enhancement if data contains NaN values
        if np.any(np.isnan(band_data)):
            return band_data
        
        # Apply Gaussian filter for noise reduction
        from scipy import ndimage
        smoothed = ndimage.gaussian_filter(band_data.astype(np.float32), sigma=0.5)
        
        # Histogram stretching for contrast enhancement
        valid_mask = ~np.isnan(smoothed)
        if np.any(valid_mask):
            p2, p98 = np.percentile(smoothed[valid_mask], [2, 98])
            if p98 > p2:
                stretched = np.clip((smoothed - p2) / (p98 - p2) * (p98 - p2) + p2, 
                                  np.min(smoothed), np.max(smoothed))
                return stretched.astype(band_data.dtype)
        
        return band_data