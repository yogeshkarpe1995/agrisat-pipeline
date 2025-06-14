
-- Database Schema for Satellite Agriculture Monitoring Pipeline
-- This script creates tables, indexes, and sample data for the system

-- Create plot_metadata table
CREATE TABLE IF NOT EXISTS plot_metadata (
    plot_id TEXT PRIMARY KEY,
    area_hectares REAL,
    crop_type TEXT,
    owner TEXT,
    region TEXT,
    planting_date TEXT,
    harvest_date TEXT,
    irrigation_type TEXT,
    soil_type TEXT,
    elevation_m REAL,
    geometry TEXT,
    last_processed TIMESTAMP,
    total_images_processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create processing_records table
CREATE TABLE IF NOT EXISTS processing_records (
    id TEXT PRIMARY KEY,
    plot_id TEXT NOT NULL,
    processing_date TEXT NOT NULL,
    satellite_date TEXT NOT NULL,
    file_size_bytes INTEGER,
    processing_time_seconds REAL,
    indices_calculated TEXT,
    output_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_plot_region ON plot_metadata(region);
CREATE INDEX IF NOT EXISTS idx_plot_crop_type ON plot_metadata(crop_type);
CREATE INDEX IF NOT EXISTS idx_processing_date ON processing_records(processing_date);
CREATE INDEX IF NOT EXISTS idx_plot_processing_date ON processing_records(plot_id, processing_date);

-- Insert sample plot data
INSERT OR IGNORE INTO plot_metadata (
    plot_id, area_hectares, crop_type, owner, region,
    planting_date, harvest_date, irrigation_type, soil_type,
    elevation_m, geometry, total_images_processed
) VALUES 
(
    'IND001', 12.5, 'wheat', 'Bharat Agro Pvt Ltd', 'Punjab, India',
    '2023-11-15', '2024-04-10', 'drip', 'clay_loam',
    260, '{"type":"Polygon","coordinates":[[[75,31.25],[75.01,31.25],[75.01,31.255],[75,31.255],[75,31.25]]]}',
    0
),
(
    'IND002', 8.3, 'rice', 'Green Fields Agriculture', 'Tamil Nadu, India',
    '2024-06-01', '2024-10-15', 'flood', 'clay',
    45, '{"type":"Polygon","coordinates":[[[78.5,12.5],[78.51,12.5],[78.51,12.505],[78.5,12.505],[78.5,12.5]]]}',
    0
),
(
    'IND003', 15.2, 'cotton', 'Maharashtra Cotton Co.', 'Maharashtra, India',
    '2023-12-05', '2024-11-20', 'sprinkler', 'black_soil',
    450, '{"type":"Polygon","coordinates":[[[75.8,19.2],[75.81,19.2],[75.81,19.205],[75.8,19.205],[75.8,19.2]]]}',
    0
),
(
    'IND004', 6.7, 'maize', 'Karnataka Farmers Union', 'Karnataka, India',
    '2024-06-20', '2024-12-10', 'drip', 'red_soil',
    800, '{"type":"Polygon","coordinates":[[[77.2,15.3],[77.21,15.3],[77.21,15.305],[77.2,15.305],[77.2,15.3]]]}',
    0
),
(
    'IND005', 20.1, 'sugarcane', 'Uttar Pradesh Sugar Mills', 'Uttar Pradesh, India',
    '2024-07-10', '2024-11-05', 'flood', 'alluvial',
    180, '{"type":"Polygon","coordinates":[[[80.1,26.8],[80.11,26.8],[80.11,26.805],[80.1,26.805],[80.1,26.8]]]}',
    0
);

-- Insert sample processing records
INSERT OR IGNORE INTO processing_records (
    id, plot_id, processing_date, satellite_date,
    file_size_bytes, processing_time_seconds,
    indices_calculated, output_path
) VALUES 
(
    'IND001_2023-11-15', 'IND001', '2023-11-15', '2023-11-15',
    15728640, 2.5,
    '["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"]',
    'output/IND001/2023-11-15'
),
(
    'IND002_2024-06-01', 'IND002', '2024-06-01', '2024-06-01',
    12455936, 2.1,
    '["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"]',
    'output/IND002/2024-06-01'
),
(
    'IND003_2023-12-05', 'IND003', '2023-12-05', '2023-12-05',
    18874368, 3.2,
    '["NDVI", "NDRE", "NDWI", "MSAVI", "TrueColor"]',
    'output/IND003/2023-12-05'
);

-- Create views for common queries
CREATE VIEW IF NOT EXISTS plot_summary AS
SELECT 
    p.plot_id,
    p.crop_type,
    p.region,
    p.area_hectares,
    p.total_images_processed,
    p.last_processed,
    COUNT(pr.id) as processing_count,
    SUM(pr.file_size_bytes) as total_file_size,
    AVG(pr.processing_time_seconds) as avg_processing_time
FROM plot_metadata p
LEFT JOIN processing_records pr ON p.plot_id = pr.plot_id
GROUP BY p.plot_id;

-- Create view for processing statistics
CREATE VIEW IF NOT EXISTS processing_stats AS
SELECT 
    DATE(processing_date) as date,
    COUNT(*) as records_processed,
    SUM(file_size_bytes) as total_size_bytes,
    AVG(processing_time_seconds) as avg_processing_time,
    COUNT(DISTINCT plot_id) as unique_plots
FROM processing_records
GROUP BY DATE(processing_date)
ORDER BY date DESC;

-- Display summary information
SELECT 'Database Schema Created Successfully' as status;
SELECT COUNT(*) as total_plots FROM plot_metadata;
SELECT COUNT(*) as total_processing_records FROM processing_records;
SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';
