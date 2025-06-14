
# Pipeline Processes Documentation

This document provides detailed information about the satellite agriculture monitoring pipeline processes, workflows, and data flow.

## Pipeline Overview

The satellite agriculture monitoring pipeline is a multi-stage process that transforms raw plot data into processed vegetation indices. The pipeline is designed for scalability, reliability, and efficiency.

## Architecture Flow

```
External API → Authentication → Data Download → Processing → Index Calculation → Storage → API Access
     ↓              ↓              ↓             ↓              ↓             ↓           ↓
Plot Metadata → Token Mgmt → Satellite Data → Band Extraction → NDVI/NDRE → GeoTIFF → REST API
                                                    ↓              NDWI         ↓
                               Database ← Rate Limiting ← Error Handling ← MSAVI ← Metadata
```

## Process Components

### 1. Data Ingestion (`api_client.py`)

**Purpose**: Fetch plot boundaries and satellite imagery

**Process Flow**:
1. **Fetch Plot Data**
   - Connects to external plot boundary API
   - Retrieves GeoJSON plot geometries
   - Validates plot metadata completeness
   - Error handling for API failures

2. **Search Satellite Data**
   - Queries Copernicus catalog for Sentinel-2 images
   - Filters by date range (planting to harvest)
   - Applies cloud coverage threshold (≤20%)
   - Returns available satellite acquisitions

3. **Download Satellite Images**
   - Uses Sentinel Hub Processing API
   - Downloads multi-spectral bands (B01-B12)
   - Handles TIFF and ZIP response formats
   - Implements retry logic with exponential backoff

**Configuration**:
```python
# API endpoints
PLOTS_API_URL = "https://example.com/api/plots"
COPERNICUS_SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
COPERNICUS_DOWNLOAD_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

# Processing parameters
MAX_CLOUD_COVERAGE = 20
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 1280
```

**Error Handling**:
- Network timeout handling
- Invalid response format handling
- Authentication failure recovery
- Rate limit compliance

---

### 2. Authentication Management (`auth.py`)

**Purpose**: Manage Copernicus Dataspace authentication tokens

**Process Flow**:
1. **Token Acquisition**
   - OAuth2 password grant flow
   - Username/password authentication
   - Bearer token generation
   - Expiration time tracking

2. **Token Refresh**
   - Automatic token renewal (5-minute buffer)
   - Error handling for failed refresh
   - Graceful degradation on auth failures

3. **Request Headers**
   - Automatic bearer token injection
   - Content-Type header management
   - Authorization header formatting

**Token Lifecycle**:
```
Request → Check Token Validity → Refresh if Needed → Add to Headers → API Call
    ↓            ↓                    ↓                ↓             ↓
 New Call → Valid Token? → No → Get New Token → Bearer Header → Success
            ↓ Yes
         Use Existing → Bearer Header → Success
```

---

### 3. Satellite Data Processing (`satellite_processor.py`)

**Purpose**: Extract and process spectral bands from satellite imagery

**Process Flow**:
1. **Data Format Detection**
   - Attempts TIFF direct loading
   - Falls back to ZIP extraction
   - Handles multi-format responses

2. **Band Extraction**
   - Reads 12 Sentinel-2 spectral bands
   - Extracts raster metadata (projection, dimensions)
   - Validates data quality and completeness

3. **Synthetic Data Generation** (when real data unavailable)
   - Creates realistic band value ranges
   - Applies spatial correlation (Gaussian filter)
   - Maintains consistent data structure

**Spectral Bands**:
| Band | Name | Wavelength | Resolution | Purpose |
|------|------|------------|------------|---------|
| B01 | Coastal aerosol | 443 nm | 60m | Atmospheric correction |
| B02 | Blue | 490 nm | 10m | True color composite |
| B03 | Green | 560 nm | 10m | True color composite |
| B04 | Red | 665 nm | 10m | True color, vegetation |
| B05 | Red Edge 1 | 705 nm | 20m | Vegetation analysis |
| B06 | Red Edge 2 | 740 nm | 20m | Vegetation analysis |
| B07 | Red Edge 3 | 783 nm | 20m | Vegetation analysis |
| B08 | NIR | 842 nm | 10m | Vegetation indices |
| B8A | Red Edge 4 | 865 nm | 20m | Vegetation analysis |
| B09 | Water vapor | 945 nm | 60m | Atmospheric correction |
| B11 | SWIR 1 | 1610 nm | 20m | Water content |
| B12 | SWIR 2 | 2190 nm | 20m | Water content |

---

### 4. Vegetation Index Calculation (`indices_calculator.py`)

**Purpose**: Calculate vegetation health indicators from spectral bands

**Process Flow**:
1. **Index Computation**
   - Applies mathematical formulas to band combinations
   - Handles division by zero scenarios
   - Scales results to 16-bit integer range

2. **Quality Validation**
   - Checks for invalid pixel values
   - Applies masking for bad data
   - Ensures proper data type conversion

3. **Multi-band Composites**
   - Creates RGB true color images
   - Stacks bands appropriately
   - Maintains proper band ordering

**Vegetation Indices**:

#### NDVI (Normalized Difference Vegetation Index)
```
Formula: (NIR - RED) / (NIR + RED)
Bands: B08 (NIR), B04 (RED)
Range: -1 to 1 (scaled to 0-10000)
Purpose: Overall vegetation health and biomass
```

#### NDRE (Normalized Difference Red Edge Index)
```
Formula: (NIR - RedEdge) / (NIR + RedEdge)
Bands: B08 (NIR), B05 (Red Edge)
Range: -1 to 1 (scaled to 0-10000)
Purpose: Chlorophyll content, more sensitive than NDVI
```

#### NDWI (Normalized Difference Water Index)
```
Formula: (GREEN - NIR) / (GREEN + NIR)
Bands: B03 (GREEN), B08 (NIR)
Range: -1 to 1 (scaled to 0-10000)
Purpose: Water content and plant water stress
```

#### MSAVI (Modified Soil Adjusted Vegetation Index)
```
Formula: (2 * NIR + 1 - sqrt((2 * NIR + 1)^2 - 8 * (NIR - RED))) / 2
Bands: B08 (NIR), B04 (RED)
Range: 0 to 1 (scaled to 0-10000)
Purpose: Vegetation with reduced soil background influence
```

#### TrueColor Composite
```
Composition: RGB composite
Bands: B04 (RED), B03 (GREEN), B02 (BLUE)
Channels: 3-band RGB
Purpose: Visual interpretation and reference
```

---

### 5. Database Management (`database_manager.py`)

**Purpose**: Track processing state and avoid redundant operations

**Process Flow**:
1. **Processing State Tracking**
   - Checks if plot/date combination already processed
   - Prevents redundant downloads and calculations
   - Maintains processing history

2. **Metadata Storage**
   - Stores plot information and processing records
   - Tracks file sizes and processing times
   - Maintains audit trail

3. **Query Operations**
   - Provides data access for API endpoints
   - Optimized queries for common operations
   - Handles database connections properly

**Database Operations**:
```python
# Check if already processed
is_processed = db_manager.is_already_processed(plot_id, date_str)

# Save processing record
db_manager.save_processing_record(
    plot_id, date_str, satellite_date,
    file_size, processing_time, indices, output_path
)

# Update statistics
db_manager.update_plot_processing_stats(plot_id, images_count)
```

---

### 6. Pipeline Orchestration (`pipeline.py`)

**Purpose**: Coordinate all pipeline components and manage workflow

**Process Flow**:
1. **Initialization**
   - Creates component instances
   - Validates configuration
   - Establishes database connections

2. **Plot Processing Loop**
   - Fetches plot data from external API
   - Processes plots in configurable batches
   - Implements rate limiting between requests

3. **Date Range Processing**
   - Generates date sequences from planting to harvest
   - Checks database for already processed dates
   - Downloads and processes new satellite data

4. **Error Recovery**
   - Continues processing on individual failures
   - Logs errors for debugging
   - Maintains processing statistics

**Batch Processing**:
```python
# Process in batches to optimize resource usage
batch_size = config.BATCH_SIZE  # Default: 2
for batch_start in range(0, len(plots_data), batch_size):
    batch = plots_data[batch_start:batch_start + batch_size]
    
    for plot_data in batch:
        process_single_plot(plot_data)
        rate_limit_request(config.REQUEST_DELAY)
    
    # Pause between batches
    time.sleep(config.REQUEST_DELAY * 2)
```

---

### 7. Output Management (`utils.py`)

**Purpose**: Handle file organization and metadata generation

**Process Flow**:
1. **Directory Structure Creation**
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
   ```

2. **GeoTIFF Generation**
   - Preserves spatial reference information
   - Applies LZW compression
   - Maintains proper data types

3. **Metadata Creation**
   - Combines plot and processing information
   - Timestamps all operations
   - Provides traceability

**Metadata Structure**:
```json
{
  "plot_data": {
    "type": "Feature",
    "properties": { "plot_id": "...", "crop_type": "..." },
    "geometry": { "type": "Polygon", "coordinates": [...] }
  },
  "processing_info": {
    "date_processed": "2025-06-10T07:45:58.552484",
    "indices_calculated": ["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"],
    "satellite_data_date": "2023-11-15",
    "image_dimensions": "1280x1280",
    "max_cloud_coverage": 20
  }
}
```

## Performance Optimization

### Rate Limiting Strategy

**Purpose**: Prevent API throttling and manage resource usage

**Implementation**:
- Configurable delays between requests (default: 1 second)
- Exponential backoff for failed requests
- Batch processing with longer pauses between batches

### Memory Management

**Strategies**:
- Process bands individually to reduce memory footprint
- Use temporary files for large raster operations
- Garbage collection after each plot processing

### CPU Optimization

**Techniques**:
- Batch processing to amortize overhead
- Parallel processing where possible
- Efficient numpy operations for index calculations

### Storage Optimization

**Methods**:
- LZW compression for GeoTIFF files
- Avoid storing redundant data
- Database indexing for fast queries

## Error Handling and Recovery

### Error Categories

1. **Network Errors**
   - Connection timeouts
   - API rate limiting
   - Service unavailability

2. **Data Errors**
   - Invalid satellite data
   - Missing spectral bands
   - Corrupted downloads

3. **Processing Errors**
   - Mathematical computation failures
   - File I/O errors
   - Memory allocation failures

### Recovery Strategies

1. **Retry Logic**
   - Exponential backoff for temporary failures
   - Maximum retry limits to prevent infinite loops
   - Different strategies for different error types

2. **Graceful Degradation**
   - Continue processing other plots on individual failures
   - Use synthetic data when real data unavailable
   - Log all errors for post-processing analysis

3. **State Persistence**
   - Database tracking prevents duplicate work
   - Resume processing from last successful state
   - Partial results preservation

## Monitoring and Logging

### Logging Levels

- **DEBUG**: Detailed computational information
- **INFO**: Progress updates and successful operations
- **WARNING**: Non-critical issues and fallbacks
- **ERROR**: Failed operations requiring attention

### Performance Metrics

- Processing time per plot
- File sizes and compression ratios
- API response times
- Error rates and types

### Health Checks

- Database connectivity
- API endpoint availability
- Disk space monitoring
- Memory usage tracking

## Scalability Considerations

### Horizontal Scaling

- Stateless processing design
- Database-coordinated work distribution
- Plot-level parallelization capability

### Vertical Scaling

- Configurable batch sizes
- Memory-efficient processing
- CPU optimization for index calculations

### Resource Management

- Configurable processing parameters
- Adaptive batch sizing based on system resources
- Graceful handling of resource constraints

## Maintenance and Operations

### Regular Maintenance Tasks

1. **Database Cleanup**
   - Archive old processing records
   - Optimize database indexes
   - Vacuum database for space reclamation

2. **File System Maintenance**
   - Monitor disk space usage
   - Compress old output files
   - Verify file integrity

3. **Configuration Updates**
   - Update API endpoints as needed
   - Adjust processing parameters
   - Update authentication credentials

### Backup and Recovery

1. **Database Backups**
   - Regular automated backups
   - Point-in-time recovery capability
   - Backup verification procedures

2. **File System Backups**
   - Output file preservation
   - Incremental backup strategies
   - Geographic distribution of backups

### Performance Tuning

1. **Processing Optimization**
   - Monitor processing times
   - Adjust batch sizes for optimal throughput
   - Identify and resolve bottlenecks

2. **Resource Optimization**
   - Memory usage profiling
   - CPU utilization monitoring
   - Network bandwidth optimization

This pipeline is designed to be robust, scalable, and maintainable while providing high-quality satellite-derived vegetation indices for agricultural monitoring applications.
