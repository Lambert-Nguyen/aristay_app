"""
Memory management middleware for Heroku dynos
"""
import gc
import psutil
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class MemoryManagementMiddleware:
    """
    Middleware to manage memory usage and prevent memory leaks
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.memory_threshold = 0.8  # 80% memory usage threshold
        self.max_memory_mb = 400  # Max memory in MB before cleanup
        
    def __call__(self, request):
        # Check memory before processing request
        self._check_memory_usage()
        
        response = self.get_response(request)
        
        # Cleanup after processing request
        self._cleanup_memory()
        
        return response
    
    def _check_memory_usage(self):
        """Check current memory usage and trigger cleanup if needed"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Log memory usage
            logger.debug(f"Memory usage: {memory_mb:.2f} MB")
            
            # Trigger cleanup if memory usage is high
            if memory_mb > self.max_memory_mb:
                logger.warning(f"High memory usage detected: {memory_mb:.2f} MB")
                self._force_cleanup()
                
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
    
    def _cleanup_memory(self):
        """Perform memory cleanup after each request"""
        try:
            # Force garbage collection
            collected = gc.collect()
            if collected > 0:
                logger.debug(f"Garbage collected {collected} objects")
                
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
    
    def _force_cleanup(self):
        """Force aggressive memory cleanup"""
        try:
            # Multiple garbage collection passes
            for _ in range(3):
                gc.collect()
            
            # Clear Django's cache if it exists
            if hasattr(settings, 'CACHES'):
                from django.core.cache import cache
                cache.clear()
                
            logger.info("Forced memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during forced cleanup: {e}")
