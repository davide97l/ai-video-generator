"""
Local LLM for Script Generation using Ollama
Replacement for GPT-4 via Mindsflow agents
"""

import json
import requests
import uuid
import os
import boto3
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class LocalLLM:
    def __init__(self, model_name: str = "llama3.1:8b-instruct-q4_K_M"):
        """
        Initialize Local LLM with Ollama
        
        Args:
            model_name: Ollama model name (quantized for memory efficiency)
        """
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434"
        self.ensure_model_available()
    
    def ensure_model_available(self):
        """Ensure the model is available in Ollama"""
        try:
            # Check if model is available
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                if self.model_name not in model_names:
                    logger.info(f"Model {self.model_name} not found, pulling...")
                    self._pull_model()
                else:
                    logger.info(f"Model {self.model_name} is available")
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            raise
    
    def _pull_model(self):
        """Pull model from Ollama registry"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": self.model_name},
                stream=True
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully pulled model {self.model_name}")
            else:
                raise Exception(f"Failed to pull model: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            raise
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate text using local LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        try:
            messages = []
            
            if system_prompt is not None:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["message"]["content"].strip()
            else:
                raise Exception(f"LLM request failed: {response.text}")
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

class LocalScriptGenerator:
    def __init__(self):
        self.llm = LocalLLM()
        
        # Prompts for different types of content
        self.story_prompt = """You are a creative storyteller. Generate a compelling short story script for a video.

Topic: {topic}

Return your response as a JSON object with the following structure:
{{
    "Title": "Story title",
    "Text": "Complete story text suitable for narration",
    "Summary": "Brief summary of the story",
    "Segments": [
        {{"text": "First segment", "scene": "Scene description"}},
        {{"text": "Second segment", "scene": "Scene description"}}
    ]
}}

Make the story engaging, emotional, and suitable for a short video (2-3 minutes when narrated).
Ensure the text flows naturally for voice narration."""

        self.paragraph_prompt = """You are an expert content creator. Generate an informative and engaging script for a video.

Topic: {topic}

Return your response as a JSON object with the following structure:
{{
    "Title": "Video title",
    "Text": "Complete script text suitable for narration", 
    "Summary": "Brief summary of the content",
    "Segments": [
        {{"text": "First segment", "scene": "Visual description"}},
        {{"text": "Second segment", "scene": "Visual description"}}
    ]
}}

Make the content informative, engaging, and suitable for a short video (2-3 minutes when narrated).
Break the content into natural segments for easy visualization.
Ensure the text flows naturally for voice narration."""

        self.music_prompt = """Generate a detailed music prompt for background music that would complement this video topic.

Topic: {topic}

Return only a descriptive music prompt (not JSON) that includes:
- Mood and emotion
- Instruments or style
- Tempo and energy level
- Duration preference

Keep it concise but descriptive for a music generation model."""

        self.personalization_prompt = """Rewrite the following text to match the specified style while maintaining the core message and structure.

TEXT: {text}
STYLE: {style}

Return only the rewritten text, maintaining the same length and structure but adapting the tone and style as requested."""

    def upload_to_aws(self, filename: str) -> str:
        """Upload file to AWS S3"""
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
            bucket_path = 'ai-video'
            s3_client.upload_file(filename, bucket_name, f"{bucket_path}/{filename}")
            s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
            url = f'{s3_base_url}{bucket_path}/{filename}'
            
            return url
        except Exception as e:
            logger.error(f"Failed to upload to AWS: {e}")
            return filename

    def generate_story_script(self, topic: str) -> str:
        """Generate story script"""
        prompt = self.story_prompt.format(topic=topic)
        return self.llm.generate(prompt)

    def generate_paragraph_script(self, topic: str) -> str:
        """Generate informational script"""
        prompt = self.paragraph_prompt.format(topic=topic)
        return self.llm.generate(prompt)

    def generate_music_prompt(self, topic: str) -> str:
        """Generate music prompt"""
        prompt = self.music_prompt.format(topic=topic)
        return self.llm.generate(prompt)

    def personalize_text(self, text: str, style: str) -> str:
        """Personalize text to match style"""
        prompt = self.personalization_prompt.format(text=text, style=style)
        return self.llm.generate(prompt)

def mindsflow_function(event, context) -> dict:
    """
    Mindsflow-compatible function for local script generation
    """
    topic = event.get("topic")
    style = event.get("text_style", None)
    return_url = event.get("return_url", True)
    
    if not topic:
        raise ValueError("Topic is required for script generation")
    
    # Initialize script generator
    generator = LocalScriptGenerator()
    
    # Determine script type based on topic
    if 'story' in topic.lower():
        json_string = generator.generate_story_script(topic)
    else:
        json_string = generator.generate_paragraph_script(topic)
    
    try:
        # Parse the generated JSON
        dict_object = json.loads(json_string)
    except json.JSONDecodeError:
        # If JSON parsing fails, create a simple structure
        logger.warning("Failed to parse generated JSON, creating simple structure")
        dict_object = {
            "Title": f"Video about {topic}",
            "Text": json_string,
            "Summary": f"Content about {topic}",
            "Segments": [{"text": json_string, "scene": f"Visual for {topic}"}]
        }
    
    # Generate music prompt
    music_prompt = generator.generate_music_prompt(topic)
    dict_object['music_prompt'] = music_prompt.replace('//', '').replace('"', '')
    
    # Apply style if specified
    if style:
        dict_object['original_text'] = dict_object['Text']
        dict_object['Text'] = generator.personalize_text(dict_object['Text'], style)
    
    # Save JSON file
    json_path = f"script_{uuid.uuid4()}.json"
    with open(json_path, 'w') as f:
        json.dump(dict_object, f)
    
    # Upload to AWS
    json_url = generator.upload_to_aws(json_path)
    
    # Clean up local file
    if os.path.exists(json_path):
        os.remove(json_path)
    
    # Prepare result
    result = {
        'json_string': json.dumps(dict_object),
        'json_url': json_url
    }
    
    # Add all keys from the generated object
    for key, value in dict_object.items():
        result[key.lower()] = value
    
    logger.info(f"Generated script for topic: {topic}")
    
    return result