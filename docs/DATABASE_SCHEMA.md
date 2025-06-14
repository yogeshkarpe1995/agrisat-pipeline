
# Database Schema Documentation

This document describes the database schema used by the Satellite Agriculture Monitoring Pipeline.

## Overview

The system uses SQLite as the database engine for storing metadata about agricultural plots and tracking processing records. The database automatically creates tables on first run and handles schema migrations.

## Database Setup

### Automatic Creation
The database is automatically created when you first run the pipeline. However, you can also create and populate it manually using the provided scripts.

### Manual Database Creation

To manually create the database with sample data, run the database creation script:

```bash
python create_database.py
```

This script will:
1. Create the database tables (`plot_metadata` and `processing_records`)
2. Create performance indexes
3. Populate the database with 5 sample agricultural plots from India
4. Verify the database setup

### Alternative SQL Script

You can also use the raw SQL script if preferred:

```bash
sqlite3 satellite_monitoring.db < create_database.sql
```

**Note**: The SQL script only creates the schema and indexes, but does not populate sample data.

### Verification

After running the creation script, you should see output similar to:

```
2025-06-10 08:00:22,382 - create_database - INFO - Creating database: sqlite:///satellite_monitoring.db
2025-06-10 08:00:22,382 - create_database - INFO - Database tables and indexes created successfully
2025-06-10 08:00:22,683 - create_database - INFO - Added sample plot: IND001
2025-06-10 08:00:22,684 - create_database - INFO - Added sample plot: IND002
...
2025-06-10 08:00:22,687 - create_database - INFO - Sample plot data populated successfully
2025-06-10 08:00:22,688 - create_database - INFO - Database verification:
2025-06-10 08:00:22,688 - create_database - INFO -   - Plot metadata records: 5
2025-06-10 08:00:22,688 - create_database - INFO -   - Processing records: 0
```

## Database Configuration

- **Engine**: SQLite
- **File Location**: `satellite_monitoring.db` (in project root)
- **ORM**: SQLAlchemy
- **Connection**: Via environment variable `DATABASE_URL`

## Tables

### 1. plot_metadata

Stores comprehensive information about agricultural plots.

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `plot_id` | String | PRIMARY KEY | Unique plot identifier |
| `area_hectares` | Float | NULL allowed | Plot area in hectares |
| `crop_type` | String | NULL allowed | Type of crop being grown |
| `owner` | String | NULL allowed | Plot owner/operator name |
| `region` | String | NULL allowed | Geographic region |
| `planting_date` | String | NULL allowed | Crop planting date (YYYY-MM-DD) |
| `harvest_date` | String | NULL allowed | Expected harvest date (YYYY-MM-DD) |
| `irrigation_type` | String | NULL allowed | Irrigation method |
| `soil_type` | String | NULL allowed | Soil classification |
| `elevation_m` | Float | NULL allowed | Elevation in meters |
| `geometry` | Text | NULL allowed | GeoJSON geometry as text |
| `last_processed` | DateTime | NULL allowed | Last processing timestamp |
| `total_images_processed` | Integer | Default: 0 | Count of processed images |
| `created_at` | DateTime | Default: UTC now | Record creation timestamp |
| `updated_at` | DateTime | Default: UTC now | Last update timestamp |

#### Example Data

```sql
INSERT INTO plot_metadata (
    plot_id, area_hectares, crop_type, owner, region,
    planting_date, harvest_date, irrigation_type, soil_type,
    elevation_m, geometry, total_images_processed
) VALUES (
    'IND001', 12.5, 'wheat', 'Bharat Agro Pvt Ltd', 'Punjab, India',
    '2023-11-15', '2024-04-10', 'drip', 'clay_loam',
    260, '{"type":"Polygon","coordinates":[[[75,31.25],[75.01,31.25],[75.01,31.255],[75,31.255],[75,31.25]]]}',
    11
);
```

#### Indexes

- Primary key index on `plot_id`
- Index on `region` for regional queries
- Index on `crop_type` for crop-based filtering

---

### 2. processing_records

Tracks processed satellite data to prevent redundant processing and maintain processing history.

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | String | PRIMARY KEY | Composite key: {plot_id}_{date} |
| `plot_id` | String | NOT NULL | Reference to plot |
| `processing_date` | String | NOT NULL | Date being processed (YYYY-MM-DD) |
| `satellite_date` | String | NOT NULL | Actual satellite acquisition date |
| `file_size_bytes` | Integer | NULL allowed | Total size of processed files |
| `processing_time_seconds` | Float | NULL allowed | Processing duration |
| `indices_calculated` | Text | NULL allowed | JSON array of calculated indices |
| `output_path` | String | NULL allowed | Path to output directory |
| `created_at` | DateTime | Default: UTC now | Record creation timestamp |
| `updated_at` | DateTime | Default: UTC now | Last update timestamp |

#### Example Data

```sql
INSERT INTO processing_records (
    id, plot_id, processing_date, satellite_date,
    file_size_bytes, processing_time_seconds,
    indices_calculated, output_path
) VALUES (
    'IND001_2023-11-15', 'IND001', '2023-11-15', '2023-11-15',
    15728640, 2.5,
    '["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"]',
    'output/IND001/2023-11-15'
);
```

#### Indexes

- Primary key index on `id`
- Index on `plot_id` for plot-based queries
- Index on `processing_date` for date-based queries
- Composite index on `(plot_id, processing_date)`

## Relationships

```
plot_metadata (1) -----> (*) processing_records
     plot_id                    plot_id
```

- One plot can have many processing records
- Each processing record belongs to exactly one plot
- Foreign key relationship via `plot_id`

## Database Operations

### Connection Management

```python
from models import get_database_session

# Get database session
session = get_database_session()
try:
    # Perform operations
    pass
finally:
    session.close()
```

### Common Queries

#### Get All Plots

```python
from models import PlotMetadata

session = get_database_session()
plots = session.query(PlotMetadata).all()
```

#### Check if Already Processed

```python
from models import ProcessingRecord

session = get_database_session()
record_id = f"{plot_id}_{date_str}"
exists = session.query(ProcessingRecord).filter_by(id=record_id).first() is not None
```

#### Get Processing History for Plot

```python
from models import ProcessingRecord

session = get_database_session()
records = session.query(ProcessingRecord).filter_by(plot_id=plot_id).all()
```

#### Update Plot Statistics

```python
from models import PlotMetadata
from datetime import datetime

session = get_database_session()
plot = session.query(PlotMetadata).filter_by(plot_id=plot_id).first()
if plot:
    plot.last_processed = datetime.utcnow()
    plot.total_images_processed += 1
    session.commit()
```

## Data Types and Validation

### Date Formats

- All dates stored as strings in ISO format: `YYYY-MM-DD`
- Timestamps stored as ISO datetime: `YYYY-MM-DDTHH:MM:SS.ssssss`

### JSON Fields

- `geometry`: GeoJSON Polygon format
- `indices_calculated`: Array of strings

```json
{
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[75, 31.25], [75.01, 31.25], [75.01, 31.255], [75, 31.255], [75, 31.25]]]
  },
  "indices_calculated": ["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"]
}
```

### Constraints and Validation

- `plot_id`: Must be unique, non-empty string
- `processing_date`: Must be valid ISO date format
- `file_size_bytes`: Non-negative integer
- `processing_time_seconds`: Non-negative float

## Database Maintenance

### Backup

```bash
# Create backup
cp satellite_monitoring.db satellite_monitoring_backup_$(date +%Y%m%d).db

# Verify backup
sqlite3 satellite_monitoring_backup_$(date +%Y%m%d).db ".tables"
```

### Statistics

```sql
-- Plot statistics
SELECT 
    COUNT(*) as total_plots,
    COUNT(DISTINCT crop_type) as unique_crops,
    SUM(area_hectares) as total_area,
    AVG(area_hectares) as avg_area
FROM plot_metadata;

-- Processing statistics
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT plot_id) as plots_processed,
    SUM(file_size_bytes) as total_file_size,
    AVG(processing_time_seconds) as avg_processing_time
FROM processing_records;

-- Monthly processing volume
SELECT 
    strftime('%Y-%m', processing_date) as month,
    COUNT(*) as records_count,
    SUM(file_size_bytes) as month_file_size
FROM processing_records
GROUP BY strftime('%Y-%m', processing_date)
ORDER BY month;
```

### Data Cleanup

```sql
-- Remove old processing records (older than 1 year)
DELETE FROM processing_records 
WHERE created_at < datetime('now', '-1 year');

-- Remove plots with no processing records
DELETE FROM plot_metadata 
WHERE plot_id NOT IN (SELECT DISTINCT plot_id FROM processing_records);
```

## Performance Considerations

### Indexing Strategy

- Primary keys provide clustered indexing
- Additional indexes on frequently queried columns
- Composite indexes for multi-column queries

### Query Optimization

- Use parameter binding to prevent SQL injection
- Limit result sets with LIMIT clauses
- Use transactions for bulk operations

### Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

engine = create_engine(
    database_url,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

## Schema Evolution

### Migration Strategy

1. Create new columns with NULL allowed
2. Populate new columns with default values
3. Update application code to use new columns
4. Add constraints if needed

### Version Control

- Database schema version tracked in application config
- Migration scripts stored in `migrations/` directory
- Automated migration on application startup

## Security Considerations

### Data Protection

- Database file permissions: 600 (owner read/write only)
- No sensitive authentication data stored
- Plot coordinates are public information

### SQL Injection Prevention

- Use SQLAlchemy ORM for all database operations
- Parameter binding for dynamic queries
- Input validation before database operations

## Monitoring and Logging

### Database Operations Logging

```python
import logging

# Enable SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)
```

### Health Checks

```python
def check_database_health():
    try:
        session = get_database_session()
        session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
    finally:
        session.close()
```

### Storage Monitoring

```sql
-- Check database size
SELECT 
    name,
    COUNT(*) as record_count,
    MAX(rowid) as max_rowid
FROM (
    SELECT 'plot_metadata' as name FROM plot_metadata
    UNION ALL
    SELECT 'processing_records' as name FROM processing_records
)
GROUP BY name;
```

## Best Practices

1. **Always use sessions properly**: Open, use, close
2. **Handle exceptions**: Rollback transactions on errors
3. **Validate input data**: Before database operations
4. **Use transactions**: For related operations
5. **Monitor performance**: Log slow queries
6. **Regular backups**: Automated backup strategy
7. **Index maintenance**: Monitor query performance
8. **Data archival**: Archive old records periodically
