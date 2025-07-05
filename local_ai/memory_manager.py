"""
GPU Memory Manager for Local AI Video Generator
Handles efficient loading/unloading of models to stay within 12GB GPU RAM
"""

import torch
import gc
import psutil
import GPUtil
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, max_gpu_memory_gb: float = 11.0):  # Leave 1GB buffer
        """
        Initialize memory manager
        
        Args:
            max_gpu_memory_gb: Maximum GPU memory to use in GB
        """
        self.max_gpu_memory_gb = max_gpu_memory_gb
        self.loaded_models = {}
        self.model_memory_usage = {}
        
    def clear_gpu_memory(self):
        """Clear GPU memory cache"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        
    def get_gpu_memory_usage(self) -> Dict[str, float]:
        """Get current GPU memory usage"""
        if not torch.cuda.is_available():
            return {"used": 0, "available": 0, "total": 0}
            
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]  # Use first GPU
            return {
                "used": gpu.memoryUsed / 1024,  # Convert MB to GB
                "available": gpu.memoryFree / 1024,
                "total": gpu.memoryTotal / 1024
            }
        return {"used": 0, "available": 12, "total": 12}
    
    def can_load_model(self, estimated_memory_gb: float) -> bool:
        """Check if we can load a model with estimated memory usage"""
        current_usage = self.get_gpu_memory_usage()
        return (current_usage["used"] + estimated_memory_gb) <= self.max_gpu_memory_gb
    
    def unload_model(self, model_name: str):
        """Unload a specific model from memory"""
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            if model_name in self.model_memory_usage:
                del self.model_memory_usage[model_name]
            self.clear_gpu_memory()
            logger.info(f"Unloaded model: {model_name}")
    
    def unload_all_models(self):
        """Unload all models from memory"""
        self.loaded_models.clear()
        self.model_memory_usage.clear()
        self.clear_gpu_memory()
        logger.info("Unloaded all models")
    
    @contextmanager
    def model_context(self, model_name: str, model_loader_func, estimated_memory_gb: float):
        """
        Context manager for loading models temporarily
        
        Args:
            model_name: Name of the model
            model_loader_func: Function that returns the loaded model
            estimated_memory_gb: Estimated memory usage in GB
        """
        # Check if model is already loaded
        if model_name in self.loaded_models:
            yield self.loaded_models[model_name]
            return
            
        # Check if we need to free memory
        if not self.can_load_model(estimated_memory_gb):
            logger.info(f"Insufficient memory for {model_name}, clearing all models")
            self.unload_all_models()
        
        try:
            # Load the model
            logger.info(f"Loading model: {model_name}")
            memory_before = self.get_gpu_memory_usage()["used"]
            
            model = model_loader_func()
            
            memory_after = self.get_gpu_memory_usage()["used"]
            actual_memory = memory_after - memory_before
            
            self.loaded_models[model_name] = model
            self.model_memory_usage[model_name] = actual_memory
            
            logger.info(f"Loaded {model_name}, using {actual_memory:.2f}GB GPU memory")
            
            yield model
            
        finally:
            # Keep the model loaded for potential reuse
            # Models will be unloaded when memory is needed for other models
            pass
    
    def log_memory_status(self):
        """Log current memory status"""
        usage = self.get_gpu_memory_usage()
        logger.info(f"GPU Memory - Used: {usage['used']:.2f}GB, "
                   f"Available: {usage['available']:.2f}GB, "
                   f"Total: {usage['total']:.2f}GB")
        
        if self.loaded_models:
            logger.info(f"Loaded models: {list(self.loaded_models.keys())}")

# Global memory manager instance
memory_manager = MemoryManager()