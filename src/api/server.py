"""
API server for accessing satellite monitoring output data.
"""

import os
import json
from pathlib import Path
from flask import Flask, jsonify, request, send_file, abort
from flask_cors import CORS
from src.data.database_manager import DatabaseManager
from src.core.config import Config

app = Flask(__name__)
CORS(app)

# Initialize components
config = Config()
db_manager = DatabaseManager()

@app.route('/', methods=['GET'])
def index():
    """API server status and optimization info."""
    return jsonify({
        "status": "running",
        "service": "Satellite Agriculture Monitoring API",
        "optimization": {
            "bands_reduced": "50% (6 instead of 12 bands)",
            "processing_units_saved": "50%",
            "supported_indices": ["NDVI", "NDRE", "MSAVI", "NDMI", "TrueColor"]
        },
        "endpoints": {
            "/api/plots": "Get all plots",
            "/api/plots/{id}": "Get specific plot",
            "/api/processing-records": "Get processing records",
            "/api/stats": "Get processing statistics",
            "/health": "Health check"
        }
    })

@app.route('/api/plots', methods=['GET'])
def get_plots():
    """Get all plot metadata."""
    try:
        plots = db_manager.get_plot_metadata()
        return jsonify({
            "status": "success",
            "data": plots,
            "count": len(plots)
        })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/api/plots/<plot_id>', methods=['GET'])
def get_plot(plot_id):
    """Get specific plot metadata."""
    try:
        plots = db_manager.get_plot_metadata(plot_id)
        if not plots:
            return jsonify({
                "status": "error",
                "message": "Plot not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "data": plots[0]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/plots/<plot_id>/processing', methods=['GET'])
def get_plot_processing_records(plot_id):
    """Get processing records for a specific plot."""
    try:
        records = db_manager.get_processing_records(plot_id)
        return jsonify({
            "status": "success",
            "data": records,
            "count": len(records)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/processing', methods=['GET'])
def get_all_processing_records():
    """Get all processing records."""
    try:
        records = db_manager.get_processing_records()
        return jsonify({
            "status": "success",
            "data": records,
            "count": len(records)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/plots/<plot_id>/dates', methods=['GET'])
def get_plot_dates(plot_id):
    """Get available processing dates for a plot."""
    try:
        plot_dir = config.OUTPUT_DIR / plot_id
        if not plot_dir.exists():
            return jsonify({
                "status": "error",
                "message": "Plot not found"
            }), 404
        
        dates = []
        for date_dir in plot_dir.iterdir():
            if date_dir.is_dir():
                date_info = {
                    "date": date_dir.name,
                    "indices": []
                }
                
                # Get available indices for this date
                for file_path in date_dir.glob("*.tif"):
                    date_info["indices"].append(file_path.stem)
                
                # Get metadata if available
                metadata_path = date_dir / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        date_info["metadata"] = metadata
                
                dates.append(date_info)
        
        # Sort dates chronologically
        dates.sort(key=lambda x: x["date"])
        
        return jsonify({
            "status": "success",
            "data": dates,
            "count": len(dates)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/plots/<plot_id>/dates/<date>/indices', methods=['GET'])
def get_plot_date_indices(plot_id, date):
    """Get available indices for a specific plot and date."""
    try:
        date_dir = config.OUTPUT_DIR / plot_id / date
        if not date_dir.exists():
            return jsonify({
                "status": "error",
                "message": "Plot or date not found"
            }), 404
        
        indices = []
        for file_path in date_dir.glob("*.tif"):
            file_info = {
                "name": file_path.stem,
                "file_size": file_path.stat().st_size,
                "file_path": str(file_path.relative_to(config.OUTPUT_DIR))
            }
            indices.append(file_info)
        
        return jsonify({
            "status": "success",
            "data": indices,
            "count": len(indices)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/plots/<plot_id>/dates/<date>/indices/<index_name>/download', methods=['GET'])
def download_index_file(plot_id, date, index_name):
    """Download a specific vegetation index file."""
    try:
        file_path = config.OUTPUT_DIR / plot_id / date / f"{index_name}.tif"
        
        if not file_path.exists():
            return jsonify({
                "status": "error",
                "message": "File not found"
            }), 404
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=f"{plot_id}_{date}_{index_name}.tif",
            mimetype='image/tiff'
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/plots/<plot_id>/dates/<date>/metadata', methods=['GET'])
def get_processing_metadata(plot_id, date):
    """Get processing metadata for a specific plot and date."""
    try:
        metadata_path = config.OUTPUT_DIR / plot_id / date / "metadata.json"
        
        if not metadata_path.exists():
            return jsonify({
                "status": "error",
                "message": "Metadata not found"
            }), 404
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return jsonify({
            "status": "success",
            "data": metadata
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get processing statistics."""
    try:
        # Get basic stats from database
        all_plots = db_manager.get_plot_metadata()
        all_records = db_manager.get_processing_records()
        
        # Calculate file system stats
        total_files = 0
        total_size = 0
        for plot_dir in config.OUTPUT_DIR.iterdir():
            if plot_dir.is_dir():
                for file_path in plot_dir.rglob("*.tif"):
                    total_files += 1
                    total_size += file_path.stat().st_size
        
        stats = {
            "total_plots": len(all_plots),
            "total_processing_records": len(all_records),
            "total_output_files": total_files,
            "total_output_size_bytes": total_size,
            "total_output_size_mb": round(total_size / (1024*1024), 2),
            "indices_available": config.INDICES
        }
        
        return jsonify({
            "status": "success",
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Satellite Agriculture Monitoring API",
        "version": "1.0.0"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)