"""
Parallel processing implementation for satellite data processing.
"""

import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import multiprocessing as mp
from queue import Queue
#import psutil

logger = logging.getLogger(__name__)

class ParallelPlotProcessor:
    """Process multiple plots in parallel to optimize throughput."""
    
    def __init__(self, config):
        self.config = config
        self.max_workers = min(
            getattr(config, 'MAX_PARALLEL_WORKERS', 4),
            mp.cpu_count(),
            8  # Cap at 8 to avoid overloading
        )
        self.memory_limit_gb = getattr(config, 'MEMORY_LIMIT_GB', 4)
        self.processing_mode = getattr(config, 'PARALLEL_MODE', 'thread')  # 'thread' or 'process'
        
        # Rate limiting for API calls
        self.api_semaphore = threading.Semaphore(2)  # Max 2 concurrent API calls
        self.last_api_call = {}
        self.min_api_interval = 2.0  # Minimum seconds between API calls
        
        logger.info(f"Initialized parallel processor: {self.max_workers} workers, "
                   f"mode: {self.processing_mode}")
    
    def process_plots_parallel(self, plots_data: List[Dict[str, Any]], 
                              processing_function: Callable,
                              progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Process multiple plots in parallel."""
        
        logger.info(f"Starting parallel processing of {len(plots_data)} plots")
        start_time = time.time()
        
        results = []
        failed_plots = []
        
        # Choose executor based on configuration
        executor_class = ThreadPoolExecutor if self.processing_mode == 'thread' else ProcessPoolExecutor
        
        try:
            with executor_class(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_plot = {
                    executor.submit(self._process_single_plot_wrapper, plot_data, processing_function): plot_data
                    for plot_data in plots_data
                }
                
                # Collect results as they complete
                completed = 0
                for future in as_completed(future_to_plot):
                    plot_data = future_to_plot[future]
                    plot_id = plot_data.get("properties", {}).get("plot_id", "unknown")
                    
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                        completed += 1
                        
                        if progress_callback:
                            progress_callback(completed, len(plots_data), plot_id)
                            
                        logger.info(f"Completed plot {plot_id} ({completed}/{len(plots_data)})")
                        
                    except Exception as e:
                        logger.error(f"Failed to process plot {plot_id}: {str(e)}")
                        failed_plots.append({"plot_id": plot_id, "error": str(e)})
                        completed += 1
        
        except Exception as e:
            logger.error(f"Parallel processing failed: {str(e)}")
            raise
        
        processing_time = time.time() - start_time
        logger.info(f"Parallel processing completed: {len(results)} successful, "
                   f"{len(failed_plots)} failed, {processing_time:.1f}s total")
        
        return {
            "results": results,
            "failed": failed_plots,
            "statistics": {
                "total_plots": len(plots_data),
                "successful": len(results),
                "failed": len(failed_plots),
                "processing_time": processing_time,
                "plots_per_second": len(plots_data) / processing_time if processing_time > 0 else 0
            }
        }
    
    def _process_single_plot_wrapper(self, plot_data: Dict[str, Any], 
                                   processing_function: Callable) -> Optional[Dict[str, Any]]:
        """Wrapper for processing a single plot with error handling and rate limiting."""
        
        plot_id = plot_data.get("properties", {}).get("plot_id", "unknown")
        
        try:
            # Check memory usage before processing
            if not self._check_memory_availability():
                logger.warning(f"Skipping plot {plot_id} due to high memory usage")
                return None
            
            # Apply rate limiting for API calls
            self._apply_rate_limiting(plot_id)
            
            # Process the plot
            result = processing_function(plot_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing plot {plot_id}: {str(e)}")
            raise
    
    def _apply_rate_limiting(self, plot_id: str):
        """Apply rate limiting to prevent API overload."""
        
        current_time = time.time()
        last_call = self.last_api_call.get(plot_id, 0)
        
        if current_time - last_call < self.min_api_interval:
            sleep_time = self.min_api_interval - (current_time - last_call)
            time.sleep(sleep_time)
        
        self.last_api_call[plot_id] = time.time()
    
    def _check_memory_availability(self) -> bool:
        """Check if sufficient memory is available for processing."""
        
        try:
            # memory = psutil.virtual_memory()
            # available_gb = memory.available / (1024**3)
            
            # if available_gb < self.memory_limit_gb:
            #     logger.warning(f"Low memory: {available_gb:.1f}GB available, "
            #                  f"limit: {self.memory_limit_gb}GB")
            #     return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Could not check memory availability: {str(e)}")
            return True  # Assume available if check fails
    
    def process_plots_in_batches(self, plots_data: List[Dict[str, Any]], 
                                processing_function: Callable,
                                batch_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process plots in smaller batches to manage memory and resources."""
        
        if batch_size is None:
            batch_size = min(self.max_workers * 2, 10)
        
        logger.info(f"Processing {len(plots_data)} plots in batches of {batch_size}")
        
        all_results = []
        all_failed = []
        total_stats = {
            "total_plots": len(plots_data),
            "successful": 0,
            "failed": 0,
            "processing_time": 0,
            "plots_per_second": 0
        }
        
        start_time = time.time()
        
        # Process in batches
        for i in range(0, len(plots_data), batch_size):
            batch = plots_data[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(plots_data) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} plots)")
            
            try:
                batch_result = self.process_plots_parallel(
                    batch, 
                    processing_function,
                    lambda completed, total, plot_id: logger.debug(f"Batch {batch_num}: {completed}/{total}")
                )
                
                all_results.extend(batch_result["results"])
                all_failed.extend(batch_result["failed"])
                
                # Update statistics
                total_stats["successful"] += batch_result["statistics"]["successful"]
                total_stats["failed"] += batch_result["statistics"]["failed"]
                
                # Pause between batches to allow system recovery
                if i + batch_size < len(plots_data):
                    time.sleep(2.0)
                    
            except Exception as e:
                logger.error(f"Batch {batch_num} failed: {str(e)}")
                # Mark all plots in batch as failed
                for plot_data in batch:
                    plot_id = plot_data.get("properties", {}).get("plot_id", "unknown")
                    all_failed.append({"plot_id": plot_id, "error": f"Batch processing failed: {str(e)}"})
                    total_stats["failed"] += 1
        
        total_time = time.time() - start_time
        total_stats["processing_time"] = total_time
        total_stats["plots_per_second"] = len(plots_data) / total_time if total_time > 0 else 0
        
        logger.info(f"Batch processing completed: {total_stats['successful']} successful, "
                   f"{total_stats['failed']} failed, {total_time:.1f}s total")
        
        return {
            "results": all_results,
            "failed": all_failed,
            "statistics": total_stats
        }


class AsyncPlotProcessor:
    """Asynchronous plot processor for real-time processing."""
    
    def __init__(self, config):
        self.config = config
        self.processing_queue = Queue()
        self.result_queue = Queue()
        self.workers = []
        self.running = False
        
    def start_processing(self, num_workers: int = 2):
        """Start background processing workers."""
        
        self.running = True
        
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"PlotWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {num_workers} async processing workers")
    
    def stop_processing(self):
        """Stop background processing workers."""
        
        self.running = False
        
        # Add sentinel values to wake up workers
        for _ in self.workers:
            self.processing_queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5.0)
        
        self.workers.clear()
        logger.info("Stopped async processing workers")
    
    def submit_plot(self, plot_data: Dict[str, Any], processing_function: Callable) -> str:
        """Submit a plot for asynchronous processing."""
        
        plot_id = plot_data.get("properties", {}).get("plot_id", "unknown")
        
        task = {
            "plot_id": plot_id,
            "plot_data": plot_data,
            "processing_function": processing_function,
            "submitted_at": time.time()
        }
        
        self.processing_queue.put(task)
        logger.debug(f"Submitted plot {plot_id} for async processing")
        
        return plot_id
    
    def get_result(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Get a completed processing result."""
        
        try:
            return self.result_queue.get(timeout=timeout)
        except:
            return None
    
    def _worker_loop(self):
        """Main worker loop for processing plots."""
        
        worker_name = threading.current_thread().name
        logger.debug(f"Started worker {worker_name}")
        
        while self.running:
            try:
                task = self.processing_queue.get(timeout=1.0)
                
                if task is None:  # Sentinel value to stop
                    break
                
                plot_id = task["plot_id"]
                logger.debug(f"Worker {worker_name} processing plot {plot_id}")
                
                start_time = time.time()
                
                try:
                    result = task["processing_function"](task["plot_data"])
                    
                    processing_time = time.time() - start_time
                    
                    result_data = {
                        "plot_id": plot_id,
                        "result": result,
                        "processing_time": processing_time,
                        "worker": worker_name,
                        "completed_at": time.time()
                    }
                    
                    self.result_queue.put(result_data)
                    logger.debug(f"Worker {worker_name} completed plot {plot_id} in {processing_time:.1f}s")
                    
                except Exception as e:
                    error_data = {
                        "plot_id": plot_id,
                        "error": str(e),
                        "worker": worker_name,
                        "completed_at": time.time()
                    }
                    
                    self.result_queue.put(error_data)
                    logger.error(f"Worker {worker_name} failed to process plot {plot_id}: {str(e)}")
                
                finally:
                    self.processing_queue.task_done()
                    
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    logger.warning(f"Worker {worker_name} encountered error: {str(e)}")
        
        logger.debug(f"Worker {worker_name} stopped")