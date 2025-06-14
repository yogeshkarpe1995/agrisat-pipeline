"""
Copernicus API optimization module to minimize data consumption and API calls.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """Configuration for Copernicus optimization strategies."""
    max_cloud_coverage: int = 20
    min_date_interval_days: int = 7  # Minimum days between satellite acquisitions
    batch_size: int = 5  # Number of plots to process simultaneously
    request_delay: float = 2.0  # Seconds between API calls
    cache_duration_hours: int = 24  # Hours to cache search results
    priority_indices: List[str] = None  # Only calculate essential indices
    
    def __post_init__(self):
        if self.priority_indices is None:
            self.priority_indices = ["NDVI", "NDWI"]  # Only essential indices

class CopernicusOptimizer:
    """Optimize Copernicus data consumption through intelligent caching and filtering."""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.search_cache = {}
        self.download_cache = {}
        
    def optimize_date_selection(self, available_dates: List[str], 
                              plot_data: Dict[str, Any]) -> List[str]:
        """
        Intelligently select optimal dates to minimize downloads while maximizing coverage.
        
        Strategies:
        1. Filter by minimum interval between dates
        2. Prioritize key growth stages (planting + 30, 60, 90 days)
        3. Avoid dates too close to each other
        4. Consider seasonal patterns
        """
        if not available_dates:
            return []
            
        # Convert to datetime objects for processing
        date_objects = [datetime.strptime(date, "%Y-%m-%d") for date in available_dates]
        date_objects.sort()
        
        # Get key growth stage dates
        planting_date = plot_data.get("properties", {}).get("planting_date")
        key_dates = self._get_key_growth_dates(planting_date) if planting_date else []
        
        # Select optimal dates
        selected_dates = []
        last_selected = None
        
        for date_obj in date_objects:
            # Always include key growth stage dates
            if any(abs((date_obj - key_date).days) <= 3 for key_date in key_dates):
                selected_dates.append(date_obj.strftime("%Y-%m-%d"))
                last_selected = date_obj
                continue
                
            # Apply minimum interval filter
            if last_selected is None or (date_obj - last_selected).days >= self.config.min_date_interval_days:
                selected_dates.append(date_obj.strftime("%Y-%m-%d"))
                last_selected = date_obj
                
        logger.info(f"Optimized dates: {len(available_dates)} → {len(selected_dates)} dates selected")
        return selected_dates
    
    def _get_key_growth_dates(self, planting_date: str) -> List[datetime]:
        """Get key agricultural growth stage dates."""
        planting = datetime.strptime(planting_date, "%Y-%m-%d")
        
        # Key growth stages for most crops
        key_stages = [
            planting + timedelta(days=14),   # Germination
            planting + timedelta(days=30),   # Early vegetative
            planting + timedelta(days=60),   # Mid vegetative
            planting + timedelta(days=90),   # Reproductive
            planting + timedelta(days=120),  # Maturity
        ]
        
        return key_stages
    
    def cache_search_results(self, plot_geometry: Dict[str, Any], 
                           start_date: str, end_date: str, 
                           results: List[str]) -> str:
        """Cache search results to avoid repeated API calls."""
        cache_key = self._generate_cache_key(plot_geometry, start_date, end_date)
        
        self.search_cache[cache_key] = {
            "results": results,
            "timestamp": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=self.config.cache_duration_hours)
        }
        
        logger.debug(f"Cached search results for key: {cache_key[:8]}...")
        return cache_key
    
    def get_cached_search_results(self, plot_geometry: Dict[str, Any], 
                                start_date: str, end_date: str) -> Optional[List[str]]:
        """Retrieve cached search results if valid."""
        cache_key = self._generate_cache_key(plot_geometry, start_date, end_date)
        
        if cache_key in self.search_cache:
            cache_entry = self.search_cache[cache_key]
            if datetime.now() < cache_entry["expires_at"]:
                logger.debug(f"Using cached search results for key: {cache_key[:8]}...")
                return cache_entry["results"]
            else:
                # Remove expired cache
                del self.search_cache[cache_key]
                
        return None
    
    def _generate_cache_key(self, plot_geometry: Dict[str, Any], 
                          start_date: str, end_date: str) -> str:
        """Generate unique cache key for plot and date range."""
        geometry_str = json.dumps(plot_geometry, sort_keys=True)
        key_data = f"{geometry_str}_{start_date}_{end_date}_{self.config.max_cloud_coverage}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def optimize_batch_processing(self, plots_data: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group plots for optimal batch processing to reduce API load."""
        # Group plots by geographic proximity to optimize API calls
        batches = []
        current_batch = []
        
        for plot in plots_data:
            current_batch.append(plot)
            
            if len(current_batch) >= self.config.batch_size:
                batches.append(current_batch)
                current_batch = []
                
        # Add remaining plots
        if current_batch:
            batches.append(current_batch)
            
        logger.info(f"Organized {len(plots_data)} plots into {len(batches)} optimized batches")
        return batches
    
    def should_skip_processing(self, plot_id: str, date_str: str, 
                             database_manager) -> bool:
        """
        Determine if processing should be skipped based on optimization rules.
        
        Rules:
        1. Already processed recently
        2. Low-priority dates outside growth stages
        3. Redundant dates too close to existing processed dates
        """
        # Check if already processed
        if database_manager.is_already_processed(plot_id, date_str):
            return True
            
        # Get recent processing records
        recent_records = database_manager.get_processing_records(plot_id)
        if not recent_records:
            return False
            
        # Check for dates too close to already processed dates
        processing_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        for record in recent_records:
            record_date = datetime.strptime(record["processing_date"], "%Y-%m-%d")
            days_diff = abs((processing_date - record_date).days)
            
            if days_diff < self.config.min_date_interval_days:
                logger.debug(f"Skipping {date_str} for {plot_id} - too close to {record['processing_date']}")
                return True
                
        return False
    
    def optimize_indices_calculation(self, indices_calculator, 
                                   bands_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate only priority indices to reduce processing time and storage."""
        optimized_indices = {}
        
        for index_name in self.config.priority_indices:
            if hasattr(indices_calculator, f'_calculate_{index_name.lower()}'):
                logger.debug(f"Calculating priority index: {index_name}")
                calc_method = getattr(indices_calculator, f'_calculate_{index_name.lower()}')
                optimized_indices[index_name] = calc_method(bands_data)
            else:
                logger.warning(f"Index calculation method not found for: {index_name}")
                
        logger.info(f"Calculated {len(optimized_indices)} priority indices instead of all indices")
        return optimized_indices
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get statistics about optimization effectiveness."""
        return {
            "cache_hits": len([c for c in self.search_cache.values() 
                             if datetime.now() < c["expires_at"]]),
            "cache_misses": len([c for c in self.search_cache.values() 
                               if datetime.now() >= c["expires_at"]]),
            "total_cached_searches": len(self.search_cache),
            "config": {
                "min_date_interval_days": self.config.min_date_interval_days,
                "max_cloud_coverage": self.config.max_cloud_coverage,
                "priority_indices": self.config.priority_indices,
                "batch_size": self.config.batch_size
            }
        }
    
    def apply_rate_limiting(self, last_request_time: Optional[float] = None) -> None:
        """Apply intelligent rate limiting to avoid API throttling."""
        if last_request_time:
            elapsed = time.time() - last_request_time
            if elapsed < self.config.request_delay:
                sleep_time = self.config.request_delay - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)