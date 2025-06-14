"""
Database manager for tracking processed satellite data and avoiding redundant downloads.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.data.models import ProcessingRecord, PlotMetadata, get_database_session, create_tables

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manage database operations for satellite processing pipeline."""
    
    def __init__(self):
        create_tables()
        
    def is_already_processed(self, plot_id: str, date_str: str) -> bool:
        """Check if a plot/date combination has already been processed."""
        session = get_database_session()
        try:
            record_id = f"{plot_id}_{date_str}"
            record = session.query(ProcessingRecord).filter_by(id=record_id).first()
            return record is not None
        finally:
            session.close()
    
    def save_processing_record(self, plot_id: str, date_str: str, satellite_date: str,
                             file_size: int, processing_time: float, indices: List[str],
                             output_path: str) -> None:
        """Save a processing record to avoid future redundant processing."""
        session = get_database_session()
        try:
            record_id = f"{plot_id}_{date_str}"
            
            # Check if record exists
            existing_record = session.query(ProcessingRecord).filter_by(id=record_id).first()
            
            if existing_record:
                # Update existing record
                existing_record.satellite_date = satellite_date
                existing_record.file_size_bytes = file_size
                existing_record.processing_time_seconds = processing_time
                existing_record.indices_calculated = json.dumps(indices)
                existing_record.output_path = output_path
                existing_record.updated_at = datetime.utcnow()
            else:
                # Create new record
                record = ProcessingRecord(
                    id=record_id,
                    plot_id=plot_id,
                    processing_date=date_str,
                    satellite_date=satellite_date,
                    file_size_bytes=file_size,
                    processing_time_seconds=processing_time,
                    indices_calculated=json.dumps(indices),
                    output_path=output_path
                )
                session.add(record)
            
            session.commit()
            logger.info(f"Saved processing record for {plot_id} on {date_str}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save processing record: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_plot_metadata(self, plot_data: Dict[str, Any]) -> None:
        """Save or update plot metadata."""
        session = get_database_session()
        try:
            properties = plot_data["properties"]
            plot_id = properties["plot_id"]
            
            # Check if plot exists
            existing_plot = session.query(PlotMetadata).filter_by(plot_id=plot_id).first()
            
            if existing_plot:
                # Update existing plot
                existing_plot.area_hectares = properties.get("area_hectares")
                existing_plot.crop_type = properties.get("crop_type")
                existing_plot.owner = properties.get("owner")
                existing_plot.region = properties.get("region")
                existing_plot.planting_date = properties.get("planting_date")
                existing_plot.harvest_date = properties.get("harvest_date")
                existing_plot.irrigation_type = properties.get("irrigation_type")
                existing_plot.soil_type = properties.get("soil_type")
                existing_plot.elevation_m = properties.get("elevation_m")
                existing_plot.geometry = json.dumps(plot_data["geometry"])
                existing_plot.updated_at = datetime.utcnow()
            else:
                # Create new plot
                plot = PlotMetadata(
                    plot_id=plot_id,
                    area_hectares=properties.get("area_hectares"),
                    crop_type=properties.get("crop_type"),
                    owner=properties.get("owner"),
                    region=properties.get("region"),
                    planting_date=properties.get("planting_date"),
                    harvest_date=properties.get("harvest_date"),
                    irrigation_type=properties.get("irrigation_type"),
                    soil_type=properties.get("soil_type"),
                    elevation_m=properties.get("elevation_m"),
                    geometry=json.dumps(plot_data["geometry"])
                )
                session.add(plot)
            
            session.commit()
            logger.info(f"Saved plot metadata for {plot_id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save plot metadata: {str(e)}")
            raise
        finally:
            session.close()
    
    def update_plot_processing_stats(self, plot_id: str, images_processed: int) -> None:
        """Update plot processing statistics."""
        session = get_database_session()
        try:
            plot = session.query(PlotMetadata).filter_by(plot_id=plot_id).first()
            if plot:
                plot.last_processed = datetime.utcnow()
                plot.total_images_processed += images_processed
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update plot stats: {str(e)}")
        finally:
            session.close()
    
    def get_processing_records(self, plot_id: str = None) -> List[Dict[str, Any]]:
        """Get processing records, optionally filtered by plot_id."""
        session = get_database_session()
        try:
            query = session.query(ProcessingRecord)
            if plot_id:
                query = query.filter_by(plot_id=plot_id)
            
            records = query.all()
            result = []
            
            for record in records:
                result.append({
                    'id': record.id,
                    'plot_id': record.plot_id,
                    'processing_date': record.processing_date,
                    'satellite_date': record.satellite_date,
                    'file_size_bytes': record.file_size_bytes,
                    'processing_time_seconds': record.processing_time_seconds,
                    'indices_calculated': json.loads(record.indices_calculated or '[]'),
                    'output_path': record.output_path,
                    'created_at': record.created_at.isoformat(),
                    'updated_at': record.updated_at.isoformat()
                })
            
            return result
            
        finally:
            session.close()
    
    def get_plot_metadata(self, plot_id: str = None) -> List[Dict[str, Any]]:
        """Get plot metadata, optionally filtered by plot_id."""
        session = get_database_session()
        try:
            query = session.query(PlotMetadata)
            if plot_id:
                query = query.filter_by(plot_id=plot_id)
            
            plots = query.all()
            result = []
            
            for plot in plots:
                result.append({
                    'plot_id': plot.plot_id,
                    'area_hectares': plot.area_hectares,
                    'crop_type': plot.crop_type,
                    'owner': plot.owner,
                    'region': plot.region,
                    'planting_date': plot.planting_date,
                    'harvest_date': plot.harvest_date,
                    'irrigation_type': plot.irrigation_type,
                    'soil_type': plot.soil_type,
                    'elevation_m': plot.elevation_m,
                    'geometry': json.loads(plot.geometry or '{}'),
                    'last_processed': plot.last_processed.isoformat() if plot.last_processed else None,
                    'total_images_processed': plot.total_images_processed,
                    'created_at': plot.created_at.isoformat(),
                    'updated_at': plot.updated_at.isoformat()
                })
            
            return result
            
        finally:
            session.close()