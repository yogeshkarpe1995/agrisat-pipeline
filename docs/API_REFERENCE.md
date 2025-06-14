
# API Reference Guide

This document provides detailed information about the Satellite Agriculture Monitoring API endpoints.

## Base Information

- **Base URL**: `http://0.0.0.0:5000/api`
- **Content Type**: `application/json`
- **Port**: 5000 (forwarded to 80/443 in production)

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Error Handling

All API responses follow a consistent format:

### Success Response
```json
{
  "status": "success",
  "data": {},
  "count": 0
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description"
}
```

### HTTP Status Codes
- `200 OK`: Request successful
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Endpoints Reference

### 1. Health Check

**Endpoint**: `GET /api/health`

**Description**: Check API service health status.

**Parameters**: None

**Response**:
```json
{
  "status": "healthy",
  "service": "Satellite Agriculture Monitoring API",
  "version": "1.0.0"
}
```

**Example**:
```bash
curl http://0.0.0.0:5000/api/health
```

---

### 2. Get All Plots

**Endpoint**: `GET /api/plots`

**Description**: Retrieve metadata for all agricultural plots in the system.

**Parameters**: None

**Response**:
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
      "harvest_date": "2024-04-10",
      "irrigation_type": "drip",
      "soil_type": "clay_loam",
      "elevation_m": 260,
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[75, 31.25], [75.01, 31.25], [75.01, 31.255], [75, 31.255], [75, 31.25]]]
      },
      "last_processed": "2025-06-10T07:45:58.552484",
      "total_images_processed": 11,
      "created_at": "2025-06-10T07:45:58.552484",
      "updated_at": "2025-06-10T07:45:58.552484"
    }
  ],
  "count": 1
}
```

**Example**:
```bash
curl http://0.0.0.0:5000/api/plots
```

---

### 3. Get Specific Plot

**Endpoint**: `GET /api/plots/{plot_id}`

**Description**: Retrieve metadata for a specific agricultural plot.

**Parameters**:
- `plot_id` (string): Unique plot identifier

**Response**:
```json
{
  "status": "success",
  "data": {
    "plot_id": "IND001",
    "area_hectares": 12.5,
    "crop_type": "wheat",
    "owner": "Bharat Agro Pvt Ltd",
    "region": "Punjab, India",
    "planting_date": "2023-11-15",
    "harvest_date": "2024-04-10",
    "irrigation_type": "drip",
    "soil_type": "clay_loam",
    "elevation_m": 260,
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[75, 31.25], [75.01, 31.25], [75.01, 31.255], [75, 31.255], [75, 31.25]]]
    },
    "last_processed": "2025-06-10T07:45:58.552484",
    "total_images_processed": 11,
    "created_at": "2025-06-10T07:45:58.552484",
    "updated_at": "2025-06-10T07:45:58.552484"
  }
}
```

**Error Responses**:
- `404`: Plot not found

**Example**:
```bash
curl http://0.0.0.0:5000/api/plots/IND001
```

---

### 4. Get Plot Processing Records

**Endpoint**: `GET /api/plots/{plot_id}/processing`

**Description**: Retrieve processing history for a specific plot.

**Parameters**:
- `plot_id` (string): Unique plot identifier

**Response**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "IND001_2023-11-15",
      "plot_id": "IND001",
      "processing_date": "2023-11-15",
      "satellite_date": "2023-11-15",
      "file_size_bytes": 15728640,
      "processing_time_seconds": 2.5,
      "indices_calculated": ["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"],
      "output_path": "output/IND001/2023-11-15",
      "created_at": "2025-06-10T07:45:58.552484",
      "updated_at": "2025-06-10T07:45:58.552484"
    }
  ],
  "count": 1
}
```

**Example**:
```bash
curl http://0.0.0.0:5000/api/plots/IND001/processing
```

---

### 5. Get All Processing Records

**Endpoint**: `GET /api/processing`

**Description**: Retrieve all processing records from the system.

**Parameters**: None

**Response**: Same as plot-specific processing records but for all plots.

**Example**:
```bash
curl http://0.0.0.0:5000/api/processing
```

---

### 6. Get Available Dates for Plot

**Endpoint**: `GET /api/plots/{plot_id}/dates`

**Description**: Retrieve available processing dates and indices for a specific plot.

**Parameters**:
- `plot_id` (string): Unique plot identifier

**Response**:
```json
{
  "status": "success",
  "data": [
    {
      "date": "2023-11-15",
      "indices": ["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"],
      "metadata": {
        "plot_data": {
          "type": "Feature",
          "properties": {
            "plot_id": "IND001",
            "area_hectares": 12.5,
            "crop_type": "wheat"
          }
        },
        "processing_info": {
          "date_processed": "2025-06-10T07:45:58.552484",
          "indices_calculated": ["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"],
          "satellite_data_date": "2023-11-15",
          "image_dimensions": "1280x1280",
          "max_cloud_coverage": 20
        }
      }
    }
  ],
  "count": 1
}
```

**Error Responses**:
- `404`: Plot not found

**Example**:
```bash
curl http://0.0.0.0:5000/api/plots/IND001/dates
```

---

### 7. Get Indices for Specific Date

**Endpoint**: `GET /api/plots/{plot_id}/dates/{date}/indices`

**Description**: Retrieve available vegetation indices for a specific plot and date.

**Parameters**:
- `plot_id` (string): Unique plot identifier
- `date` (string): Date in YYYY-MM-DD format

**Response**:
```json
{
  "status": "success",
  "data": [
    {
      "name": "NDVI",
      "file_size": 3276800,
      "file_path": "IND001/2023-11-15/NDVI.tif"
    },
    {
      "name": "NDRE",
      "file_size": 3276800,
      "file_path": "IND001/2023-11-15/NDRE.tif"
    },
    {
      "name": "NDWI",
      "file_size": 3276800,
      "file_path": "IND001/2023-11-15/NDWI.tif"
    },
    {
      "name": "MSAVI",
      "file_size": 3276800,
      "file_path": "IND001/2023-11-15/MSAVI.tif"
    },
    {
      "name": "TrueColor",
      "file_size": 9830400,
      "file_path": "IND001/2023-11-15/TrueColor.tif"
    }
  ],
  "count": 5
}
```

**Error Responses**:
- `404`: Plot or date not found

**Example**:
```bash
curl http://0.0.0.0:5000/api/plots/IND001/dates/2023-11-15/indices
```

---

### 8. Download Index File

**Endpoint**: `GET /api/plots/{plot_id}/dates/{date}/indices/{index_name}/download`

**Description**: Download a specific vegetation index GeoTIFF file.

**Parameters**:
- `plot_id` (string): Unique plot identifier
- `date` (string): Date in YYYY-MM-DD format
- `index_name` (string): Index name (NDVI, NDRE, NDWI, MSAVI, TrueColor)

**Response**: Binary GeoTIFF file

**Headers**:
- `Content-Type`: `image/tiff`
- `Content-Disposition`: `attachment; filename="{plot_id}_{date}_{index_name}.tif"`

**Error Responses**:
- `404`: File not found

**Example**:
```bash
curl -O http://0.0.0.0:5000/api/plots/IND001/dates/2023-11-15/indices/NDVI/download
```

---

### 9. Get Processing Metadata

**Endpoint**: `GET /api/plots/{plot_id}/dates/{date}/metadata`

**Description**: Retrieve processing metadata for a specific plot and date.

**Parameters**:
- `plot_id` (string): Unique plot identifier
- `date` (string): Date in YYYY-MM-DD format

**Response**:
```json
{
  "status": "success",
  "data": {
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
        "coordinates": [[[75, 31.25], [75.01, 31.25], [75.01, 31.255], [75, 31.255], [75, 31.25]]]
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
}
```

**Error Responses**:
- `404`: Metadata not found

**Example**:
```bash
curl http://0.0.0.0:5000/api/plots/IND001/dates/2023-11-15/metadata
```

---

### 10. Get System Statistics

**Endpoint**: `GET /api/stats`

**Description**: Retrieve system-wide processing statistics.

**Parameters**: None

**Response**:
```json
{
  "status": "success",
  "data": {
    "total_plots": 5,
    "total_processing_records": 156,
    "total_output_files": 780,
    "total_output_size_bytes": 2560000000,
    "total_output_size_mb": 2441.41,
    "indices_available": ["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"]
  }
}
```

**Example**:
```bash
curl http://0.0.0.0:5000/api/stats
```

## Usage Examples

### Python Examples

```python
import requests

# Get all plots
response = requests.get('http://0.0.0.0:5000/api/plots')
plots = response.json()

# Get specific plot
response = requests.get('http://0.0.0.0:5000/api/plots/IND001')
plot = response.json()

# Download NDVI file
response = requests.get('http://0.0.0.0:5000/api/plots/IND001/dates/2023-11-15/indices/NDVI/download')
with open('NDVI.tif', 'wb') as f:
    f.write(response.content)
```

### JavaScript Examples

```javascript
// Get all plots
fetch('http://0.0.0.0:5000/api/plots')
  .then(response => response.json())
  .then(data => console.log(data));

// Get plot dates
fetch('http://0.0.0.0:5000/api/plots/IND001/dates')
  .then(response => response.json())
  .then(data => console.log(data));

// Download file
fetch('http://0.0.0.0:5000/api/plots/IND001/dates/2023-11-15/indices/NDVI/download')
  .then(response => response.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'NDVI.tif';
    a.click();
  });
```

## Rate Limiting

Currently, there are no rate limits implemented on the API. However, the underlying satellite data processing pipeline implements rate limiting for external API calls.

## CORS Support

The API includes CORS support, allowing cross-origin requests from web browsers.

## File Formats

- **GeoTIFF**: All vegetation index files are saved as GeoTIFF format
- **JSON**: Metadata is provided in JSON format
- **Compression**: GeoTIFF files use LZW compression

## Data Quality

- **Cloud Coverage**: Maximum 20% cloud coverage for satellite imagery
- **Image Dimensions**: 1280x1280 pixels
- **Data Type**: 16-bit unsigned integer for vegetation indices
- **Scaling**: Vegetation indices are scaled to 0-10000 range
