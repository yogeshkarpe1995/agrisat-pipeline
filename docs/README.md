
# Satellite Agriculture Monitoring Pipeline

A comprehensive system for monitoring agricultural plots using satellite imagery from Copernicus/Sentinel-2 data. The pipeline processes satellite data to calculate vegetation indices and provides a REST API for accessing the results.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Pipeline Components](#pipeline-components)
- [Vegetation Indices](#vegetation-indices)
- [Output Structure](#output-structure)
- [Troubleshooting](#troubleshooting)

## Overview

This system automates the process of:
1. Fetching agricultural plot boundaries from external APIs
2. Downloading satellite imagery from Copernicus Dataspace
3. Processing satellite data to extract spectral bands
4. Calculating vegetation indices (NDVI, NDRE, NDWI, MSAVI, TrueColor)
5. Storing results as GeoTIFF files with metadata
6. Providing REST API access to processed data

## Features

- **Automated satellite data processing** for multiple agricultural plots
- **Vegetation index calculation** including NDVI, NDRE, NDWI, MSAVI, and TrueColor composites
- **Database tracking** to avoid redundant processing
- **REST API** for accessing processed data and metadata
- **Batch processing** with rate limiting for efficient resource usage
- **Error handling** and comprehensive logging
- **GeoTIFF output** with proper geospatial metadata

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   External API  │    │  Copernicus     │    │   Database      │
│   (Plot Data)   │    │   Dataspace     │    │   (SQLite)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
┌─────────▼──────────────────────▼──────────────────────▼───────┐
│                    Main Pipeline                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ API Client  │  │ Satellite   │  │ Indices     │           │
│  │             │  │ Processor   │  │ Calculator  │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Output Files   │
                    │  (GeoTIFF +     │
                    │   Metadata)     │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   REST API      │
                    │   Server        │
                    └─────────────────┘
```

## Installation

1. **Clone the repository** (if applicable) or ensure all files are present
2. **Install dependencies** - The system will automatically install required packages:
   - requests
   - rasterio
   - numpy
   - scipy
   - sqlalchemy
   - flask
   - flask-cors

3. **Set up environment variables** in Replit Secrets:
   ```
   COPERNICUS_USERNAME=your_username
   COPERNICUS_PASSWORD=your_password
   DATABASE_URL=sqlite:///satellite_monitoring.db
   ```

## Configuration

The system is configured through the `config.py` file:

### Key Configuration Options

- **API Endpoints**: Copernicus and external plot data APIs
- **Processing Settings**: Image dimensions (1280x1280), cloud coverage threshold (20%)
- **Vegetation Indices**: NDVI, NDRE, NDWI, MSAVI, TrueColor
- **Rate Limiting**: Request delays and batch sizes
- **Output Directory**: `output/` folder structure

### Authentication

Configure Copernicus Dataspace credentials:
```python
COPERNICUS_USERNAME = "your_username"
COPERNICUS_PASSWORD = "your_password"
COPERNICUS_CLIENT_ID = "cdse-public"
```

## Usage

### Running the Pipeline

1. **Start the main pipeline**:
   ```bash
   python main.py
   ```

2. **Start the API server** (in parallel):
   ```bash
   python api_server.py
   ```

3. **Use the Run button** in Replit to start both processes

### Pipeline Process

1. Pipeline fetches plot data from external API
2. For each plot, it generates date ranges from planting to harvest
3. Downloads satellite imagery for each date
4. Processes imagery to extract spectral bands
5. Calculates vegetation indices
6. Saves results as GeoTIFF files with metadata
7. Updates database with processing records

## API Documentation

The REST API provides access to processed satellite data and metadata.

### Base URL
```
http://0.0.0.0:5000/api
```

### Endpoints

#### Get All Plots
```http
GET /api/plots
```
Returns metadata for all agricultural plots.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "plot_id": "IND001",
      "area_hectares": 12.5,
      "crop_type": "wheat",
      "owner": "Bharat Agro Pvt Ltd",
      "region": "Punjab, India",
      "planting_date": "2023-11-15",
      "harvest_date": "2024-04-10"
    }
  ],
  "count": 1
}
```

#### Get Specific Plot
```http
GET /api/plots/{plot_id}
```
Returns metadata for a specific plot.

#### Get Plot Processing Records
```http
GET /api/plots/{plot_id}/processing
```
Returns processing history for a specific plot.

#### Get Available Dates for Plot
```http
GET /api/plots/{plot_id}/dates
```
Returns available processing dates and indices for a plot.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "date": "2023-11-15",
      "indices": ["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"],
      "metadata": {
        "processing_info": {
          "date_processed": "2025-06-10T07:45:58.552484",
          "satellite_data_date": "2023-11-15",
          "image_dimensions": "1280x1280"
        }
      }
    }
  ]
}
```

#### Get Indices for Specific Date
```http
GET /api/plots/{plot_id}/dates/{date}/indices
```
Returns available vegetation indices for a specific plot and date.

#### Download Index File
```http
GET /api/plots/{plot_id}/dates/{date}/indices/{index_name}/download
```
Downloads the GeoTIFF file for a specific vegetation index.

#### Get Processing Metadata
```http
GET /api/plots/{plot_id}/dates/{date}/metadata
```
Returns processing metadata for a specific plot and date.

#### Get System Statistics
```http
GET /api/stats
```
Returns system-wide processing statistics.

#### Health Check
```http
GET /api/health
```
Returns API health status.

## Database Schema

The system uses SQLite database with two main tables:

### PlotMetadata Table
Stores information about agricultural plots:
- `plot_id` (Primary Key): Unique plot identifier
- `area_hectares`: Plot area in hectares
- `crop_type`: Type of crop grown
- `owner`: Plot owner name
- `region`: Geographic region
- `planting_date`: Crop planting date
- `harvest_date`: Expected harvest date
- `irrigation_type`: Irrigation method
- `soil_type`: Soil classification
- `elevation_m`: Elevation in meters
- `geometry`: GeoJSON geometry data
- `last_processed`: Last processing timestamp
- `total_images_processed`: Number of processed images
- `created_at`, `updated_at`: Timestamps

### ProcessingRecord Table
Tracks processed satellite data to avoid redundancy:
- `id` (Primary Key): Composite of plot_id + date
- `plot_id`: Reference to plot
- `processing_date`: Date when processing occurred
- `satellite_date`: Actual satellite acquisition date
- `file_size_bytes`: Size of processed files
- `processing_time_seconds`: Processing duration
- `indices_calculated`: JSON list of calculated indices
- `output_path`: Path to output files
- `created_at`, `updated_at`: Timestamps

## Pipeline Components

### 1. API Client (`api_client.py`)
Handles external API communications:
- Fetches plot data from external sources
- Authenticates with Copernicus Dataspace
- Downloads satellite imagery using Sentinel Hub API
- Implements retry logic and error handling

### 2. Authentication (`auth.py`)
Manages Copernicus Dataspace authentication:
- OAuth2 token management
- Automatic token refresh
- Bearer token headers for API requests

### 3. Satellite Processor (`satellite_processor.py`)
Processes raw satellite data:
- Extracts spectral bands from downloaded imagery
- Handles TIFF and ZIP file formats
- Creates synthetic data for testing when needed
- Saves band data as GeoTIFF files

### 4. Indices Calculator (`indices_calculator.py`)
Calculates vegetation indices:
- NDVI: Normalized Difference Vegetation Index
- NDRE: Normalized Difference Red Edge Index
- NDWI: Normalized Difference Water Index
- MSAVI: Modified Soil Adjusted Vegetation Index
- TrueColor: RGB composite imagery

### 5. Database Manager (`database_manager.py`)
Handles database operations:
- Tracks processed data to avoid redundancy
- Stores plot metadata and processing records
- Provides query methods for API endpoints

### 6. Pipeline Orchestrator (`pipeline.py`)
Coordinates the entire processing workflow:
- Batch processing with rate limiting
- Error handling and logging
- Progress tracking and statistics
- Output directory management

## Vegetation Indices

### NDVI (Normalized Difference Vegetation Index)
**Formula:** `(NIR - RED) / (NIR + RED)`
**Uses:** B08 (NIR) and B04 (RED)
**Purpose:** Indicates vegetation health and biomass

### NDRE (Normalized Difference Red Edge Index)
**Formula:** `(NIR - RedEdge) / (NIR + RedEdge)`
**Uses:** B08 (NIR) and B05 (Red Edge)
**Purpose:** More sensitive to chlorophyll content than NDVI

### NDWI (Normalized Difference Water Index)
**Formula:** `(GREEN - NIR) / (GREEN + NIR)`
**Uses:** B03 (GREEN) and B08 (NIR)
**Purpose:** Indicates water content and stress

### MSAVI (Modified Soil Adjusted Vegetation Index)
**Formula:** `(2 * NIR + 1 - sqrt((2 * NIR + 1)^2 - 8 * (NIR - RED))) / 2`
**Uses:** B08 (NIR) and B04 (RED)
**Purpose:** Reduces soil background influence

### TrueColor
**Composition:** RGB composite using B04 (RED), B03 (GREEN), B02 (BLUE)
**Purpose:** Visual representation of the area

## Output Structure

The system creates a hierarchical output structure:

```
output/
├── {plot_id}/
│   ├── {date}/
│   │   ├── NDVI.tif
│   │   ├── NDRE.tif
│   │   ├── NDWI.tif
│   │   ├── MSAVI.tif
│   │   ├── TrueColor.tif
│   │   └── metadata.json
│   └── {date}/
│       └── ...
└── {plot_id}/
    └── ...
```

### Metadata Structure
Each processing session generates a `metadata.json` file:

```json
{
  "plot_data": {
    "type": "Feature",
    "properties": {
      "plot_id": "IND001",
      "area_hectares": 12.5,
      "crop_type": "wheat",
      "owner": "Bharat Agro Pvt Ltd",
      "region": "Punjab, India",
      "planting_date": "2023-11-15",
      "harvest_date": "2024-04-10",
      "irrigation_type": "drip",
      "soil_type": "clay_loam",
      "elevation_m": 260
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [...]
    }
  },
  "processing_info": {
    "date_processed": "2025-06-10T07:45:58.552484",
    "indices_calculated": ["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"],
    "satellite_data_date": "2023-11-15",
    "image_dimensions": "1280x1280",
    "max_cloud_coverage": 20
  },
  "timestamp": "2025-06-10T07:45:58.552508"
}
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify Copernicus credentials in Replit Secrets
   - Check if credentials have proper permissions

2. **No Satellite Data Found**
   - Check cloud coverage threshold (default: 20%)
   - Verify date ranges align with satellite data availability
   - Ensure plot coordinates are valid

3. **Processing Failures**
   - Check logs in `pipeline.log`
   - Verify sufficient disk space for output files
   - Review network connectivity for API requests

4. **API Server Port Conflicts**
   - Default port is 5000
   - Check if port is already in use
   - Restart the API server if needed

5. **Database Issues**
   - SQLite database is created automatically
   - Check write permissions in project directory
   - Database file: `satellite_monitoring.db`

### Logging

The system provides comprehensive logging:
- **File logging**: `pipeline.log`
- **Console logging**: Real-time progress updates
- **Log levels**: INFO, WARNING, ERROR, DEBUG

### Performance Optimization

- **Batch processing**: Configurable batch sizes (default: 2 plots)
- **Rate limiting**: Delays between API requests (default: 1 second)
- **Memory management**: Efficient processing of large raster files
- **Database optimization**: Tracking prevents redundant processing

### Data Quality

- **Cloud coverage filtering**: Maximum 20% cloud coverage
- **Synthetic data fallback**: For testing when real data unavailable
- **Data validation**: Input validation for plot geometries and dates
- **Error handling**: Graceful handling of processing failures

## Support

For issues or questions:
1. Check the logs in `pipeline.log`
2. Review the API health endpoint: `/api/health`
3. Verify configuration in `config.py`
4. Ensure all environment variables are set correctly

## License

This project is for educational and research purposes. Ensure compliance with Copernicus Dataspace terms of service for satellite data usage.
