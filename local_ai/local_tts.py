"""
Local Text-to-Speech using Coqui XTTS v2
Replacement for Azure TTS with voice cloning and multilingual support
"""

import os
import torch
import torchaudio
import uuid
import tempfile
from typing import Optional, Tuple
from TTS.api import TTS
from pydub import AudioSegment
import boto3
from memory_manager import memory_manager
import logging

logger = logging.getLogger(__name__)

class LocalTTS:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = None
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        
        # Language mapping for XTTS
        self.lang_mapping = {
            'en': 'en',
            'es': 'es', 
            'fr': 'fr',
            'de': 'de',
            'it': 'it',
            'pt': 'pt',
            'pl': 'pl',
            'tr': 'tr',
            'ru': 'ru',
            'nl': 'nl',
            'cs': 'cs',
            'ar': 'ar',
            'zh': 'zh-cn',
            'ch': 'zh-cn',
            'ja': 'ja',
            'hu': 'hu',
            'ko': 'ko'
        }
    
    def _load_tts_model(self):
        """Load XTTS v2 model"""
        def loader():
            tts = TTS(model_name=self.model_name).to(self.device)
            return tts
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
            bucket_path = 'temp_audio'
            s3_client.upload_file(filename, bucket_name, f"{bucket_path}/{filename}")
            s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
            url = f'{s3_base_url}{bucket_path}/{filename}'
            
            return url
        except Exception as e:
            logger.error(f"Failed to upload to AWS: {e}")
            return filename
    
    def _adjust_speed(self, audio_path: str, speed: float) -> str:
        """Adjust audio speed using pydub"""
        if speed == 1.0:
            return audio_path
            
        try:
            audio = AudioSegment.from_wav(audio_path)
            
            # Adjust speed by changing frame rate
            if speed > 1.0:
                # Speed up
                new_frame_rate = int(audio.frame_rate * speed)
                audio_fast = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
                audio_fast = audio_fast.set_frame_rate(audio.frame_rate)
            else:
                # Slow down
                new_frame_rate = int(audio.frame_rate * speed)
                audio_slow = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
                audio_slow = audio_slow.set_frame_rate(audio.frame_rate)
                audio_fast = audio_slow
            
            # Save adjusted audio
            speed_adjusted_path = f"speed_adjusted_{os.path.basename(audio_path)}"
            audio_fast.export(speed_adjusted_path, format="wav")
            
            # Remove original file
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
            return speed_adjusted_path
            
        except Exception as e:
            logger.error(f"Failed to adjust speed: {e}")
            return audio_path
    
    def generate_speech(self, 
                       text: str, 
                       language: str = "en", 
                       voice_speed: float = 1.0,
                       speaker_wav: Optional[str] = None) -> Tuple[str, float]:
        """
        Generate speech from text
        
        Args:
            text: Text to convert to speech
            language: Language code
            voice_speed: Speech speed multiplier
            speaker_wav: Path to reference speaker audio for voice cloning
            
        Returns:
            Tuple of (audio_url, duration_seconds)
        """
        
        # Map language
        lang = self.lang_mapping.get(language, "en")
        
        # Generate unique filename
        filename = f'local_tts_{uuid.uuid4().hex[:8]}.wav'
        
        try:
            # Load TTS model with memory management
            with memory_manager.model_context("xtts_v2", self._load_tts_model(), 2.5):
                tts = memory_manager.loaded_models["xtts_v2"]
                
                # Generate speech
                if speaker_wav and os.path.exists(speaker_wav):
                    # Voice cloning
                    tts.tts_to_file(
                        text=text,
                        file_path=filename,
                        speaker_wav=speaker_wav,
                        language=lang
                    )
                else:
                    # Default voice
                    tts.tts_to_file(
                        text=text,
                        file_path=filename,
                        language=lang
                    )
            
            # Adjust speed if needed
            if voice_speed != 1.0:
                filename = self._adjust_speed(filename, voice_speed)
            
            # Get duration
            audio = AudioSegment.from_wav(filename)
            duration = audio.duration_seconds
            
            # Upload to AWS or return local path
            audio_url = self._upload_to_aws(filename)
            
            # Clean up local file if uploaded to AWS
            if audio_url != filename and os.path.exists(filename):
                os.remove(filename)
            
            logger.info(f"Generated speech: {duration:.2f}s, Language: {lang}")
            
            return audio_url, duration
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            # Cleanup on error
            if os.path.exists(filename):
                os.remove(filename)
            raise

def mindsflow_function(event, context) -> dict:
    """
    Mindsflow-compatible function for local TTS
    """
    text = event.get("text")
    language = event.get("language", "en")
    voice_speed = event.get("voice_speed", 1.0)
    speaker_wav = event.get("speaker_wav", None)  # Optional voice cloning
    
    if not text:
        raise ValueError("Text is required for TTS generation")
    
    # Initialize TTS
    tts = LocalTTS()
    
    # Generate speech
    audio_url, duration = tts.generate_speech(
        text=text,
        language=language,
        voice_speed=voice_speed,
        speaker_wav=speaker_wav
    )
    
    return {
        'audio_url': audio_url,
        'duration': duration
    }