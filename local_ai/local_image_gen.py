"""
Local Image Generation using FLUX.1-schnell and Stable Diffusion
Replacement for Replicate SDXL/SD models
"""

import torch
from diffusers import FluxPipeline, StableDiffusionPipeline, DPMSolverMultistepScheduler
from PIL import Image
import requests
import uuid
import os
import boto3
from memory_manager import memory_manager
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

class LocalImageGenerator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        # Model configurations
        self.models = {
            'flux': {
                'model_id': 'black-forest-labs/FLUX.1-schnell',
                'memory_usage': 7.0,  # GB
                'steps': 4
            },
            'sd15': {
                'model_id': 'runwayml/stable-diffusion-v1-5',
                'memory_usage': 3.5,  # GB
                'steps': 20
            },
            'sdxl': {
                'model_id': 'stabilityai/stable-diffusion-xl-base-1.0',
                'memory_usage': 6.0,  # GB
                'steps': 20
            }
        }
        
        # Currently loaded pipeline
        self.current_model = None
        self.current_pipeline = None
    
    def _load_flux_pipeline(self):
        """Load FLUX.1-schnell pipeline"""
        def loader():
            pipeline = FluxPipeline.from_pretrained(
                self.models['flux']['model_id'],
                torch_dtype=self.dtype,
                use_safetensors=True
            ).to(self.device)
            
            # Enable memory efficient attention
            if hasattr(pipeline, 'enable_attention_slicing'):
                pipeline.enable_attention_slicing()
            if hasattr(pipeline, 'enable_xformers_memory_efficient_attention'):
                try:
                    pipeline.enable_xformers_memory_efficient_attention()
                except:
                    pass
                    
            return pipeline
        return loader
    
    def _load_sd15_pipeline(self):
        """Load Stable Diffusion 1.5 pipeline"""
        def loader():
            pipeline = StableDiffusionPipeline.from_pretrained(
                self.models['sd15']['model_id'],
                torch_dtype=self.dtype,
                use_safetensors=True,
                safety_checker=None,
                requires_safety_checker=False
            ).to(self.device)
            
            # Use faster scheduler
            pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                pipeline.scheduler.config
            )
            
            # Enable memory optimizations
            pipeline.enable_attention_slicing()
            try:
                pipeline.enable_xformers_memory_efficient_attention()
            except:
                pass
                
            return pipeline
        return loader
    
    def _load_sdxl_pipeline(self):
        """Load SDXL pipeline"""
        def loader():
            pipeline = StableDiffusionPipeline.from_pretrained(
                self.models['sdxl']['model_id'],
                torch_dtype=self.dtype,
                use_safetensors=True,
                variant="fp16"
            ).to(self.device)
            
            # Enable memory optimizations
            if hasattr(pipeline, 'enable_attention_slicing'):
                pipeline.enable_attention_slicing()
            try:
                pipeline.enable_xformers_memory_efficient_attention()
            except:
                pass
                
            return pipeline
        return loader
    
    def _upload_to_aws(self, filename: str) -> str:
        """Upload image to AWS S3"""
        try:
            bucket_name = os.environ.get('bucket_name')
            region = os.environ.get('region')
            
            if not bucket_name or not region:
                logger.warning("AWS credentials not found, returning local path")
                return filename
            
            session = boto3.Session(
                aws_access_key_id=os.environ.get('access_key_id'),
                aws_secret_access_key=os.environ.get('secret_access_key')
            )
            
            s3_client = session.client('s3')
            bucket_path = 'ai-images'
            s3_client.upload_file(filename, bucket_name, f"{bucket_path}/{filename}")
            s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
            url = f'{s3_base_url}{bucket_path}/{filename}'
            
            return url
        except Exception as e:
            logger.error(f"Failed to upload to AWS: {e}")
            return filename
    
    def _resize_and_crop_image(self, image: Image.Image, width: int, height: int, crop_method: Optional[str] = None) -> Image.Image:
        """Resize and crop image to target dimensions"""
        if crop_method == 'resize':
            return image.resize((width, height), Image.LANCZOS)
        elif crop_method == 'crop_center':
            # Center crop
            img_width, img_height = image.size
            left = int((img_width - width) / 2)
            top = int((img_height - height) / 2)
            right = int((img_width + width) / 2)
            bottom = int((img_height + height) / 2)
            return image.crop((left, top, right, bottom))
        else:
            return image
    
    def generate_image(self, 
                      prompt: str, 
                      width: int = 1024, 
                      height: int = 1024,
                      model: str = 'flux',
                      negative_prompt: str = '',
                      crop_method: Optional[str] = None,
                      guidance_scale: float = 7.5,
                      num_inference_steps: Optional[int] = None) -> str:
        """
        Generate image from prompt
        
        Args:
            prompt: Text prompt for image generation
            width: Image width
            height: Image height  
            model: Model to use ('flux', 'sd15', 'sdxl')
            negative_prompt: Negative prompt
            crop_method: How to handle size ('resize', 'crop_center', None)
            guidance_scale: Guidance scale for generation
            num_inference_steps: Number of denoising steps
            
        Returns:
            URL or path to generated image
        """
        
        # Validate model
        if model not in self.models:
            model = 'flux'  # Default to FLUX
        
        model_config = self.models[model]
        
        # Set default steps if not provided
        if num_inference_steps is None:
            num_inference_steps = model_config['steps']
        
        # Generate filename
        filename = f'local_img_{uuid.uuid4().hex[:8]}.png'
        
        try:
            # Load appropriate pipeline
            model_name = f"{model}_pipeline"
            
            if model == 'flux':
                loader_func = self._load_flux_pipeline()
            elif model == 'sd15':
                loader_func = self._load_sd15_pipeline()
            elif model == 'sdxl':
                loader_func = self._load_sdxl_pipeline()
            else:
                raise ValueError(f"Unknown model: {model}")
            
            # Generate image with memory management
            with memory_manager.model_context(model_name, loader_func, model_config['memory_usage']):
                pipeline = memory_manager.loaded_models[model_name]
                
                # Prepare generation parameters
                gen_params = {
                    "prompt": prompt,
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "generator": torch.Generator(device=self.device).manual_seed(42)
                }
                
                # Add model-specific parameters
                if model == 'flux':
                    # FLUX uses different parameters
                    gen_params.pop("guidance_scale")  # FLUX doesn't use guidance scale
                    if width != 1024 or height != 1024:
                        # For non-standard sizes, generate at 1024x1024 and resize
                        gen_params["width"] = 1024
                        gen_params["height"] = 1024
                    else:
                        gen_params["width"] = width
                        gen_params["height"] = height
                else:
                    # SD models
                    gen_params["width"] = width if crop_method is None else 512
                    gen_params["height"] = height if crop_method is None else 512
                    if negative_prompt:
                        gen_params["negative_prompt"] = negative_prompt
                
                # Generate image
                logger.info(f"Generating image with {model}: {prompt[:50]}...")
                result = pipeline(**gen_params)
                image = result.images[0]
                
                # Apply resizing/cropping if needed
                if crop_method or (width != image.width or height != image.height):
                    image = self._resize_and_crop_image(image, width, height, crop_method)
                
                # Save image
                image.save(filename)
                
                logger.info(f"Generated image: {filename}")
                
                # Upload to AWS or return local path
                image_url = self._upload_to_aws(filename)
                
                # Clean up local file if uploaded
                if image_url != filename and os.path.exists(filename):
                    os.remove(filename)
                
                return image_url
                
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            # Cleanup on error
            if os.path.exists(filename):
                os.remove(filename)
            raise

def generate_image_replicate_compatible(prompt: str, 
                                      width: int = 1024, 
                                      height: int = 1024, 
                                      model: str = 'flux', 
                                      negative_prompt: str = '') -> str:
    """
    Replicate-compatible image generation function
    """
    generator = LocalImageGenerator()
    return generator.generate_image(
        prompt=prompt,
        width=width, 
        height=height,
        model=model,
        negative_prompt=negative_prompt
    )