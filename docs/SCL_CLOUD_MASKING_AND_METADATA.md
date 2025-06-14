# SCL-Based Cloud Masking and Comprehensive Metadata Generation

## Overview
This document details the enhanced cloud masking system using Sentinel-2 Scene Classification Layer (SCL) and the comprehensive metadata generation capabilities implemented in the satellite agriculture monitoring pipeline.

## 1. SCL-Enhanced Cloud Masking

### Sentinel-2 Scene Classification Layer (SCL)
The SCL band provides pixel-level classification of the Earth's surface, enabling more accurate cloud detection than traditional spectral analysis methods.

### SCL Classification Values
```
0 = No Data (black)
1 = Saturated or defective pixels
2 = Dark Area Pixels
3 = Cloud Shadows
4 = Vegetation
5 = Not Vegetated
6 = Water
7 = Unclassified
8 = Cloud Medium Probability
9 = Cloud High Probability
10 = Thin Cirrus
11 = Snow
```

### Enhanced Band Selection
The optimized system now downloads 7 bands instead of 12:
- **6 Spectral Bands**: B02, B03, B04, B05, B08, B11 (essential for indices)
- **1 Classification Band**: SCL (for advanced cloud masking)
- **Processing Unit Reduction**: 58% (7 of 12 bands)

### Cloud Detection Algorithm
```python
def detect_clouds_with_scl(scl_band):
    # Primary cloud classes
    cloud_classes = [3, 8, 9, 10]  # Shadows, medium/high clouds, cirrus
    
    # Invalid data classes
    invalid_classes = [0, 1]  # No data, saturated/defective
    
    # Combined mask
    cloud_mask = np.isin(scl_band, cloud_classes + invalid_classes)
    
    # Morphological cleaning
    cloud_mask = binary_opening(cloud_mask)
    cloud_mask = binary_closing(cloud_mask)
    
    return cloud_mask
```

### Fallback Mechanism
When SCL is unavailable, the system automatically falls back to spectral analysis:
- High reflectance detection in visible bands
- Low NDVI threshold analysis
- Blue band dominance assessment
- Morphological noise reduction

## 2. Comprehensive Metadata Generation

### Metadata Files Generated
For each processed plot, the system generates three metadata files:

1. **processing_metadata.json** - Complete processing information
2. **quality_report.json** - Quality assessment and recommendations
3. **processing_summary.json** - Concise processing summary

### Processing Metadata Structure
```json
{
  "processing_info": {
    "timestamp": "2025-06-12T14:09:48.749Z",
    "processing_version": "2.0.0",
    "pipeline_mode": "optimized_with_scl",
    "optimization_features": {
      "band_reduction": "58% (7 of 12 bands including SCL)",
      "processing_units_saved": "50%+",
      "cloud_masking": "SCL-enhanced",
      "parallel_processing": true,
      "quality_filtering": true
    }
  },
  "plot_information": {
    "plot_id": "SP189",
    "area_hectares": 2.5,
    "crop_type": "corn",
    "planting_date": "2024-11-13",
    "geometry": {
      "type": "Polygon",
      "bounds": {...}
    }
  },
  "satellite_data": {
    "acquisition_date": "2024-12-01",
    "satellite_mission": "Sentinel-2",
    "processing_level": "L2A",
    "bands_downloaded": ["B02", "B03", "B04", "B05", "B08", "B11", "SCL"],
    "optimization_applied": {
      "band_selection": "Essential bands only (6 spectral + SCL)",
      "processing_units_used": "7 instead of 12",
      "reduction_percentage": 58.3
    }
  },
  "vegetation_indices": {
    "NDVI": {
      "formula": "(NIR - RED) / (NIR + RED)",
      "purpose": "Vegetation health and biomass assessment",
      "bands_used": ["B08 (NIR)", "B04 (RED)"],
      "statistics": {
        "mean": 0.65,
        "std": 0.12,
        "min": 0.1,
        "max": 0.9,
        "data_coverage_percent": 95.2
      }
    }
  },
  "quality_assessment": {
    "overall_quality": "good",
    "cloud_coverage_percent": 15.2,
    "data_coverage_percent": 95.2,
    "assessment_method": "SCL-enhanced"
  },
  "cloud_analysis": {
    "detection_method": "SCL-enhanced",
    "scl_classification": {
      "4_Vegetation": {"percentage": 65.3},
      "5_Not_Vegetated": {"percentage": 18.5},
      "8_Cloud_Medium_Probability": {"percentage": 12.1},
      "3_Cloud_Shadows": {"percentage": 4.1}
    },
    "detailed_cloud_coverage": 16.2
  }
}
```

### Quality Report Features
- **Assessment Summary**: Overall quality metrics
- **Cloud Analysis**: Detailed SCL-based cloud statistics
- **Recommendations**: Data-driven usage recommendations
- **Usability Score**: Quantitative assessment (0-100)

### Processing Summary
Provides concise overview for quick assessment:
- Plot identification and dates
- Optimization savings achieved
- Quality score and cloud coverage
- Generated files and processing duration

## 3. Implementation Benefits

### Accuracy Improvements
- **SCL-based detection**: More accurate than spectral analysis alone
- **Pixel-level classification**: Precise identification of clouds, shadows, and invalid data
- **Reduced false positives**: Better discrimination between clouds and bright surfaces

### Processing Efficiency
- **58% band reduction**: Significant processing unit savings
- **Enhanced quality filtering**: Skip poor-quality images automatically
- **Intelligent masking**: Apply masks only to spectral bands, preserve SCL for analysis

### Comprehensive Documentation
- **Full traceability**: Complete processing history and parameters
- **Quality metrics**: Quantitative assessment for decision-making
- **Optimization tracking**: Clear visibility of efficiency gains

## 4. Usage and Integration

### Automatic Operation
The SCL-enhanced cloud masking operates automatically:
1. System checks for SCL band availability
2. Applies SCL-based detection when available
3. Falls back to spectral analysis if SCL missing
4. Generates comprehensive metadata for all processing

### Metadata Access
Metadata files are saved in the same directory as vegetation indices:
```
output/
├── plot_SP189_2024-12-01/
│   ├── NDVI.tif
│   ├── NDRE.tif
│   ├── MSAVI.tif
│   ├── NDMI.tif
│   ├── TrueColor.tif
│   ├── processing_metadata.json
│   ├── quality_report.json
│   └── processing_summary.json
```

### API Access
Enhanced API endpoints provide metadata access:
- `/api/plots/{id}/metadata` - Processing metadata
- `/api/plots/{id}/quality` - Quality reports
- `/api/processing-records` - Historical processing data

## 5. Configuration Options

### SCL Processing Settings
```python
# Cloud masking configuration
ENABLE_CLOUD_MASKING = True
MAX_CLOUD_COVERAGE = 20
MIN_DATA_COVERAGE = 80
QUALITY_THRESHOLD = 'acceptable'

# SCL-specific settings
SCL_CLOUD_CLASSES = [3, 8, 9, 10]  # Shadows, clouds, cirrus
SCL_INVALID_CLASSES = [0, 1]       # No data, defective
```

### Metadata Generation Settings
```python
# Metadata options
GENERATE_COMPREHENSIVE_METADATA = True
GENERATE_QUALITY_REPORTS = True
GENERATE_PROCESSING_SUMMARIES = True
INCLUDE_SCL_ANALYSIS = True
```

## 6. Quality Assurance

### Validation Checks
- SCL band presence verification
- Cloud mask quality assessment
- Metadata completeness validation
- Processing integrity checks

### Error Handling
- Graceful fallback to spectral analysis
- Robust metadata generation with partial data
- Clear error reporting and logging
- Recovery mechanisms for processing failures

This enhanced system provides superior cloud detection accuracy while maintaining the 50%+ processing unit savings, delivering comprehensive metadata for complete traceability and quality assessment.