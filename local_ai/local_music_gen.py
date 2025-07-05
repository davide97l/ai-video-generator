"""
Local Music Generation using AudioCraft MusicGen
Replacement for Replicate MusicGen model
"""

import torch
import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import uuid
import os
import boto3
from memory_manager import memory_manager
import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)

class LocalMusicGenerator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Model configurations  
        self.models = {
            'small': {
                'model_name': 'facebook/musicgen-small',
                'memory_usage': 2.0,  # GB
                'max_duration': 30
            },
            'medium': {
                'model_name': 'facebook/musicgen-medium', 
                'memory_usage': 4.0,  # GB
                'max_duration': 30
            },
            'large': {
                'model_name': 'facebook/musicgen-large',
                'memory_usage': 6.0,  # GB
                'max_duration': 30
            }
        }
        
        # Default model based on available memory
        self.default_model = 'medium'  # Good balance for 12GB GPU
    
    def _load_musicgen_model(self, model_size: str = 'medium'):
        """Load MusicGen model"""
        def loader():
            model_config = self.models.get(model_size, self.models['medium'])
            model = MusicGen.get_pretrained(model_config['model_name'])
            model.set_generation_params(duration=8)  # Default 8 seconds
            return model
        return loader
    
    def _upload_to_aws(self, filename: str) -> str:
        """Upload audio file to AWS S3"""
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
            bucket_path = 'ai-music'
            s3_client.upload_file(filename, bucket_name, f"{bucket_path}/{filename}")
            s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
            url = f'{s3_base_url}{bucket_path}/{filename}'
            
            return url
        except Exception as e:
            logger.error(f"Failed to upload to AWS: {e}")
            return filename
    
    def generate_music(self,
                      prompt: str,
                      duration: float = 15.0,
                      temperature: float = 1.0,
                      top_k: int = 250,
                      top_p: float = 0.0,
                      model_size: str = 'medium') -> str:
        """
        Generate music from text prompt
        
        Args:
            prompt: Text description of the music
            duration: Duration in seconds (max 30)
            temperature: Sampling temperature
            top_k: Top-k sampling parameter
            top_p: Top-p sampling parameter  
            model_size: Model size ('small', 'medium', 'large')
            
        Returns:
            URL or path to generated audio file
        """
        
        # Validate inputs
        if model_size not in self.models:
            model_size = self.default_model
            
        model_config = self.models[model_size]
        duration = min(duration, model_config['max_duration'])
        duration = max(duration, 1.0)  # Minimum 1 second
        
        # Generate unique filename
        filename = f'local_music_{uuid.uuid4().hex[:8]}'
        
        try:
            # Load MusicGen model with memory management
            model_name = f"musicgen_{model_size}"
            
            with memory_manager.model_context(
                model_name, 
                lambda: self._load_musicgen_model(model_size)(), 
                model_config['memory_usage']
            ):
                model = memory_manager.loaded_models[model_name]
                
                # Set generation parameters
                model.set_generation_params(
                    duration=duration,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p
                )
                
                logger.info(f"Generating {duration}s music with {model_size} model: {prompt[:50]}...")
                
                # Generate music
                descriptions = [prompt]
                wav = model.generate(descriptions)
                
                # Save audio file
                # AudioCraft expects the filename without extension
                audio_write(
                    filename, 
                    wav[0].cpu(), 
                    model.sample_rate, 
                    strategy="loudness",
                    loudness_compressor=True
                )
                
                # The audio_write function adds .wav extension
                actual_filename = f"{filename}.wav"
                
                logger.info(f"Generated music: {actual_filename}")
                
                # Upload to AWS or return local path
                music_url = self._upload_to_aws(actual_filename)
                
                # Clean up local file if uploaded
                if music_url != actual_filename and os.path.exists(actual_filename):
                    os.remove(actual_filename)
                
                return music_url
                
        except Exception as e:
            logger.error(f"Music generation failed: {e}")
            # Cleanup on error
            potential_files = [f"{filename}.wav", f"{filename}.mp3"]
            for file in potential_files:
                if os.path.exists(file):
                    os.remove(file)
            raise

def mindsflow_function(event, context) -> dict:
    """
    Mindsflow-compatible function for local music generation
    """
    prompt = event.get("music_prompt")
    duration = event.get("duration", 15)
    temperature = event.get("temperature", 1.0)
    model_size = event.get("model_size", "medium")
    
    if not prompt:
        raise ValueError("Music prompt is required")
    
    # Ensure duration is reasonable
    duration = min(float(duration), 28)  # Max 28 seconds like original
    if isinstance(duration, float):
        duration = math.ceil(duration)
    
    # Initialize music generator
    generator = LocalMusicGenerator()
    
    # Generate music
    music_url = generator.generate_music(
        prompt=prompt,
        duration=duration,
        temperature=temperature,
        model_size=model_size
    )
    
    return {
        'music_url': music_url
    }