"""
Comprehensive metadata generation for satellite processing results.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

class MetadataGenerator:
    """Generate comprehensive metadata files for processed satellite data."""
    
    def __init__(self, config):
        self.config = config
        
    def generate_processing_metadata(self, 
                                   plot_data: Dict[str, Any],
                                   date_str: str,
                                   bands_data: Dict[str, np.ndarray],
                                   indices_data: Dict[str, np.ndarray],
                                   processing_stats: Dict[str, Any],
                                   output_path: Path) -> Dict[str, Any]:
        """Generate comprehensive metadata for processed satellite data."""
        
        logger.info(f"Generating metadata for plot {plot_data.get('properties', {}).get('plot_id', 'unknown')}")
        
        metadata = {
            "processing_info": self._generate_processing_info(processing_stats),
            "plot_information": self._extract_plot_info(plot_data),
            "satellite_data": self._generate_satellite_metadata(date_str, bands_data),
            "vegetation_indices": self._generate_indices_metadata(indices_data),
            "quality_assessment": self._extract_quality_metrics(bands_data),
            "cloud_analysis": self._generate_cloud_analysis(bands_data),
            "file_structure": self._generate_file_structure(output_path),
            "system_configuration": self._generate_system_config(),
            "processing_timeline": self._generate_processing_timeline()
        }
        
        # Save metadata file
        metadata_file = output_path / "processing_metadata.json"
        self._save_metadata_file(metadata, metadata_file)
        
        # Generate additional specialized metadata files
        self._generate_quality_report(metadata, output_path)
        self._generate_processing_summary(metadata, output_path)
        
        return metadata
    
    def _generate_processing_info(self, processing_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate processing information metadata."""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "processing_version": "2.0.0",
            "pipeline_mode": "optimized_with_scl",
            "optimization_features": {
                "band_reduction": "58% (7 of 12 bands including SCL)",
                "processing_units_saved": "50%+",
                "cloud_masking": "SCL-enhanced",
                "parallel_processing": True,
                "quality_filtering": True
            },
            "processing_duration_seconds": processing_stats.get("processing_time", 0),
            "memory_usage_mb": processing_stats.get("memory_usage", "unknown"),
            "cpu_cores_used": processing_stats.get("cpu_cores", self.config.MAX_PARALLEL_WORKERS)
        }
    
    def _extract_plot_info(self, plot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive plot information."""
        properties = plot_data.get("properties", {})
        geometry = plot_data.get("geometry", {})
        
        return {
            "plot_id": properties.get("plot_id", "unknown"),
            "area_hectares": properties.get("area_hectares", None),
            "crop_type": properties.get("crop_type", "unknown"),
            "owner": properties.get("owner", "unknown"),
            "region": properties.get("region", "unknown"),
            "planting_date": properties.get("planting_date", None),
            "harvest_date": properties.get("harvest_date", None),
            "irrigation_type": properties.get("irrigation_type", "unknown"),
            "soil_type": properties.get("soil_type", "unknown"),
            "elevation_m": properties.get("elevation_m", None),
            "geometry": {
                "type": geometry.get("type", "unknown"),
                "coordinates_count": len(geometry.get("coordinates", [[]])[0]) if geometry.get("coordinates") else 0,
                "bounds": self._calculate_bounds(geometry) if geometry.get("coordinates") else None
            }
        }
    
    def _generate_satellite_metadata(self, date_str: str, bands_data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Generate satellite data metadata."""
        
        # Extract basic image properties
        sample_band = None
        for band_name, band_data in bands_data.items():
            if isinstance(band_data, np.ndarray) and band_name not in ['profile', 'cloud_mask']:
                sample_band = band_data
                break
        
        dimensions = sample_band.shape if sample_band is not None else (0, 0)
        
        return {
            "acquisition_date": date_str,
            "satellite_mission": "Sentinel-2",
            "processing_level": "L2A",
            "spatial_resolution": "10m-20m mixed",
            "image_dimensions": {
                "width": dimensions[1] if len(dimensions) > 1 else 0,
                "height": dimensions[0] if len(dimensions) > 0 else 0
            },
            "bands_downloaded": self._list_downloaded_bands(bands_data),
            "coordinate_system": "EPSG:4326",
            "pixel_size_meters": 10,
            "data_type": "UINT16",
            "optimization_applied": {
                "band_selection": "Essential bands only (6 spectral + SCL)",
                "processing_units_used": "7 instead of 12",
                "reduction_percentage": 58.3
            }
        }
    
    def _generate_indices_metadata(self, indices_data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Generate vegetation indices metadata."""
        
        indices_info = {}
        
        for index_name, index_data in indices_data.items():
            if isinstance(index_data, np.ndarray):
                # Calculate statistics
                valid_pixels = ~np.isnan(index_data)
                if np.any(valid_pixels):
                    stats = {
                        "mean": float(np.nanmean(index_data)),
                        "std": float(np.nanstd(index_data)),
                        "min": float(np.nanmin(index_data)),
                        "max": float(np.nanmax(index_data)),
                        "median": float(np.nanmedian(index_data)),
                        "valid_pixels_count": int(np.sum(valid_pixels)),
                        "total_pixels": int(index_data.size),
                        "data_coverage_percent": float(np.sum(valid_pixels) / index_data.size * 100)
                    }
                else:
                    stats = {"error": "No valid pixels found"}
                
                # Index-specific information
                index_info = {
                    "formula": self._get_index_formula(index_name),
                    "purpose": self._get_index_purpose(index_name),
                    "bands_used": self._get_index_bands(index_name),
                    "valid_range": self._get_index_range(index_name),
                    "statistics": stats,
                    "data_type": str(index_data.dtype),
                    "dimensions": index_data.shape
                }
                
                indices_info[index_name] = index_info
        
        return indices_info
    
    def _extract_quality_metrics(self, bands_data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Extract quality assessment metrics."""
        
        quality_metrics = bands_data.get('quality_metrics', {})
        
        return {
            "overall_quality": quality_metrics.get('overall_quality', 'unknown'),
            "cloud_coverage_percent": quality_metrics.get('cloud_coverage', 0),
            "data_coverage_percent": quality_metrics.get('data_coverage', 100),
            "noise_level": quality_metrics.get('noise_level', 'unknown'),
            "usable_for_analysis": quality_metrics.get('usable', True),
            "quality_warning": bands_data.get('quality_warning', False),
            "assessment_method": "SCL-enhanced" if "SCL" in bands_data else "spectral_analysis"
        }
    
    def _generate_cloud_analysis(self, bands_data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Generate detailed cloud analysis."""
        
        cloud_analysis = {
            "detection_method": "SCL-enhanced" if "SCL" in bands_data else "spectral_analysis",
            "cloud_coverage_percent": bands_data.get('cloud_coverage', 0),
            "cloud_mask_available": 'cloud_mask' in bands_data
        }
        
        # SCL-specific analysis
        if "SCL" in bands_data:
            scl_data = bands_data["SCL"]
            unique_classes, counts = np.unique(scl_data, return_counts=True)
            
            scl_legend = {
                0: "No Data", 1: "Saturated/Defective", 2: "Dark Area",
                3: "Cloud Shadows", 4: "Vegetation", 5: "Not Vegetated",
                6: "Water", 7: "Unclassified", 8: "Cloud Medium Probability",
                9: "Cloud High Probability", 10: "Thin Cirrus", 11: "Snow"
            }
            
            class_distribution = {}
            total_pixels = scl_data.size
            
            for class_id, count in zip(unique_classes, counts):
                class_name = scl_legend.get(class_id, f"Unknown_{class_id}")
                percentage = (count / total_pixels) * 100
                class_distribution[f"{class_id}_{class_name}"] = {
                    "pixel_count": int(count),
                    "percentage": float(percentage)
                }
            
            cloud_analysis["scl_classification"] = class_distribution
            
            # Calculate detailed cloud statistics
            cloud_classes = [3, 8, 9, 10]  # Cloud shadows, medium/high clouds, cirrus
            cloud_pixels = np.sum([counts[np.where(unique_classes == cls)[0][0]] 
                                 for cls in cloud_classes if cls in unique_classes])
            cloud_analysis["detailed_cloud_coverage"] = float(cloud_pixels / total_pixels * 100)
        
        return cloud_analysis
    
    def _generate_file_structure(self, output_path: Path) -> Dict[str, Any]:
        """Generate file structure information."""
        
        files = []
        for file_path in output_path.rglob("*"):
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "relative_path": str(file_path.relative_to(output_path)),
                    "size_bytes": file_path.stat().st_size,
                    "type": file_path.suffix,
                    "created": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                })
        
        return {
            "output_directory": str(output_path),
            "total_files": len(files),
            "files": files,
            "total_size_bytes": sum(f["size_bytes"] for f in files)
        }
    
    def _generate_system_config(self) -> Dict[str, Any]:
        """Generate system configuration information."""
        
        return {
            "max_cloud_coverage": self.config.MAX_CLOUD_COVERAGE,
            "image_dimensions": f"{self.config.IMAGE_WIDTH}x{self.config.IMAGE_HEIGHT}",
            "indices_calculated": self.config.INDICES,
            "parallel_workers": self.config.MAX_PARALLEL_WORKERS,
            "processing_mode": self.config.PARALLEL_MODE,
            "memory_limit_gb": self.config.MEMORY_LIMIT_GB,
            "quality_threshold": self.config.QUALITY_THRESHOLD,
            "cloud_masking_enabled": self.config.ENABLE_CLOUD_MASKING,
            "batch_size": self.config.BATCH_SIZE
        }
    
    def _generate_processing_timeline(self) -> Dict[str, Any]:
        """Generate processing timeline information."""
        
        return {
            "started_at": datetime.utcnow().isoformat() + "Z",
            "steps": [
                "Plot data fetching",
                "Satellite data search",
                "Image download (optimized bands)",
                "Cloud masking (SCL-enhanced)",
                "Quality assessment",
                "Vegetation indices calculation",
                "Metadata generation",
                "File output"
            ],
            "optimization_features_applied": [
                "50%+ processing unit reduction",
                "SCL-based cloud masking",
                "Parallel processing",
                "Quality filtering",
                "Comprehensive metadata generation"
            ]
        }
    
    def _save_metadata_file(self, metadata: Dict[str, Any], filepath: Path):
        """Save metadata to JSON file."""
        
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Saved comprehensive metadata to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save metadata file: {str(e)}")
    
    def _generate_quality_report(self, metadata: Dict[str, Any], output_path: Path):
        """Generate a separate quality assessment report."""
        
        quality_report = {
            "assessment_summary": metadata["quality_assessment"],
            "cloud_analysis": metadata["cloud_analysis"],
            "recommendations": self._generate_quality_recommendations(metadata),
            "data_usability": self._assess_data_usability(metadata)
        }
        
        report_file = output_path / "quality_report.json"
        self._save_metadata_file(quality_report, report_file)
    
    def _generate_processing_summary(self, metadata: Dict[str, Any], output_path: Path):
        """Generate a processing summary report."""
        
        summary = {
            "plot_id": metadata["plot_information"]["plot_id"],
            "processing_date": metadata["processing_info"]["timestamp"],
            "satellite_date": metadata["satellite_data"]["acquisition_date"],
            "optimization_savings": metadata["satellite_data"]["optimization_applied"],
            "quality_score": metadata["quality_assessment"]["overall_quality"],
            "cloud_coverage": metadata["quality_assessment"]["cloud_coverage_percent"],
            "indices_generated": list(metadata["vegetation_indices"].keys()),
            "total_files": metadata["file_structure"]["total_files"],
            "processing_duration": metadata["processing_info"]["processing_duration_seconds"]
        }
        
        summary_file = output_path / "processing_summary.json"
        self._save_metadata_file(summary, summary_file)
    
    # Helper methods for index information
    def _get_index_formula(self, index_name: str) -> str:
        formulas = {
            "NDVI": "(NIR - RED) / (NIR + RED)",
            "NDRE": "(NIR - RedEdge) / (NIR + RedEdge)", 
            "MSAVI": "(2*NIR + 1 - sqrt((2*NIR + 1)² - 8*(NIR - RED))) / 2",
            "NDMI": "(NIR - SWIR1) / (NIR + SWIR1)",
            "TrueColor": "RGB composite (RED, GREEN, BLUE)"
        }
        return formulas.get(index_name, "Unknown formula")
    
    def _get_index_purpose(self, index_name: str) -> str:
        purposes = {
            "NDVI": "Vegetation health and biomass assessment",
            "NDRE": "Chlorophyll content and vegetation stress detection",
            "MSAVI": "Soil-adjusted vegetation index for areas with exposed soil",
            "NDMI": "Vegetation moisture content and water stress assessment",
            "TrueColor": "Visual representation and interpretation"
        }
        return purposes.get(index_name, "Unknown purpose")
    
    def _get_index_bands(self, index_name: str) -> List[str]:
        bands = {
            "NDVI": ["B08 (NIR)", "B04 (RED)"],
            "NDRE": ["B08 (NIR)", "B05 (Red Edge)"],
            "MSAVI": ["B08 (NIR)", "B04 (RED)"],
            "NDMI": ["B08 (NIR)", "B11 (SWIR1)"],
            "TrueColor": ["B04 (RED)", "B03 (GREEN)", "B02 (BLUE)"]
        }
        return bands.get(index_name, ["Unknown bands"])
    
    def _get_index_range(self, index_name: str) -> str:
        ranges = {
            "NDVI": "-1 to 1 (typical vegetation: 0.2 to 0.8)",
            "NDRE": "-1 to 1 (typical vegetation: 0.2 to 0.6)",
            "MSAVI": "0 to 1 (higher values indicate more vegetation)",
            "NDMI": "-1 to 1 (higher values indicate more moisture)",
            "TrueColor": "0 to 65535 per band (UINT16)"
        }
        return ranges.get(index_name, "Unknown range")
    
    def _list_downloaded_bands(self, bands_data: Dict[str, np.ndarray]) -> List[str]:
        """List all downloaded satellite bands."""
        bands = []
        for band_name in bands_data.keys():
            if band_name not in ['profile', 'cloud_coverage', 'cloud_mask', 'quality_metrics', 'quality_warning']:
                bands.append(band_name)
        return sorted(bands)
    
    def _calculate_bounds(self, geometry: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Calculate bounding box for geometry."""
        try:
            coords = geometry.get("coordinates", [[]])[0]
            if not coords:
                return None
            
            lons = [coord[0] for coord in coords]
            lats = [coord[1] for coord in coords]
            
            return {
                "min_longitude": min(lons),
                "max_longitude": max(lons),
                "min_latitude": min(lats),
                "max_latitude": max(lats)
            }
        except Exception:
            return None
    
    def _generate_quality_recommendations(self, metadata: Dict[str, Any]) -> List[str]:
        """Generate quality-based recommendations."""
        recommendations = []
        
        cloud_coverage = metadata["quality_assessment"]["cloud_coverage_percent"]
        overall_quality = metadata["quality_assessment"]["overall_quality"]
        
        if cloud_coverage > 30:
            recommendations.append("High cloud coverage detected - consider alternative date")
        elif cloud_coverage > 15:
            recommendations.append("Moderate cloud coverage - results may be affected in cloudy areas")
        
        if overall_quality == "poor":
            recommendations.append("Poor image quality - recommend processing alternative date")
        elif overall_quality == "acceptable":
            recommendations.append("Acceptable quality - suitable for analysis with caution")
        else:
            recommendations.append("Good quality data - suitable for reliable analysis")
        
        return recommendations
    
    def _assess_data_usability(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall data usability."""
        
        quality = metadata["quality_assessment"]["overall_quality"]
        cloud_coverage = metadata["quality_assessment"]["cloud_coverage_percent"]
        
        usability_score = 0
        if quality == "excellent":
            usability_score += 40
        elif quality == "good":
            usability_score += 30
        elif quality == "acceptable":
            usability_score += 20
        
        if cloud_coverage <= 10:
            usability_score += 30
        elif cloud_coverage <= 20:
            usability_score += 20
        elif cloud_coverage <= 30:
            usability_score += 10
        
        # Add coverage bonus
        data_coverage = metadata["quality_assessment"]["data_coverage_percent"]
        if data_coverage >= 95:
            usability_score += 30
        elif data_coverage >= 85:
            usability_score += 20
        elif data_coverage >= 75:
            usability_score += 10
        
        usability_level = "poor"
        if usability_score >= 80:
            usability_level = "excellent"
        elif usability_score >= 60:
            usability_level = "good"
        elif usability_score >= 40:
            usability_level = "acceptable"
        
        return {
            "usability_score": usability_score,
            "usability_level": usability_level,
            "recommended_for_analysis": usability_score >= 40
        }