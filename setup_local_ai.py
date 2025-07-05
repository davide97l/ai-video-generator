#!/usr/bin/env python3
"""
Setup script for Local AI Video Generator
Installs all dependencies and configures the environment for 12GB GPU
"""

import subprocess
import sys
import os
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - SUCCESS")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return None

def check_gpu():
    """Check if CUDA GPU is available"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA GPU detected")
            return True
        else:
            print("⚠️  No NVIDIA GPU detected - will use CPU (slower)")
            return False
    except FileNotFoundError:
        print("⚠️  nvidia-smi not found - will use CPU (slower)")
        return False

def install_dependencies():
    """Install all required dependencies"""
    
    print("🚀 Starting Local AI Video Generator Setup")
    print("=" * 50)
    
    # Check GPU
    has_gpu = check_gpu()
    
    # Update pip
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install PyTorch with CUDA support if GPU available
    if has_gpu:
        torch_command = f"{sys.executable} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    else:
        torch_command = f"{sys.executable} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
    
    run_command(torch_command, "Installing PyTorch")
    
    # Install core AI libraries
    run_command(f"{sys.executable} -m pip install transformers>=4.36.0", "Installing Transformers")
    run_command(f"{sys.executable} -m pip install diffusers>=0.24.0", "Installing Diffusers")
    run_command(f"{sys.executable} -m pip install accelerate", "Installing Accelerate")
    run_command(f"{sys.executable} -m pip install safetensors", "Installing SafeTensors")
    
    # Install TTS
    run_command(f"{sys.executable} -m pip install TTS>=0.22.0", "Installing Coqui TTS")
    
    # Install AudioCraft for music generation
    run_command(f"{sys.executable} -m pip install audiocraft", "Installing AudioCraft")
    
    # Install image processing
    run_command(f"{sys.executable} -m pip install opencv-python", "Installing OpenCV")
    run_command(f"{sys.executable} -m pip install Pillow", "Installing Pillow")
    
    # Install audio processing
    run_command(f"{sys.executable} -m pip install librosa", "Installing librosa")
    run_command(f"{sys.executable} -m pip install soundfile", "Installing soundfile")
    run_command(f"{sys.executable} -m pip install scipy", "Installing scipy")
    
    # Install utilities
    run_command(f"{sys.executable} -m pip install GPUtil", "Installing GPUtil")
    run_command(f"{sys.executable} -m pip install psutil", "Installing psutil")
    run_command(f"{sys.executable} -m pip install requests", "Installing requests")
    
    # Install video processing (if not already installed)
    run_command(f"{sys.executable} -m pip install moviepy", "Installing MoviePy")
    run_command(f"{sys.executable} -m pip install pydub", "Installing pydub")
    
    # Install AWS SDK (if needed)
    run_command(f"{sys.executable} -m pip install boto3", "Installing boto3")

def install_ollama():
    """Install and setup Ollama for local LLM"""
    
    print("\n🦙 Setting up Ollama for Local LLM")
    print("-" * 30)
    
    # Check if Ollama is already installed
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama already installed")
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        print("Installing Ollama...")
        
        # Install Ollama based on platform
        system = platform.system().lower()
        
        if system == 'linux':
            run_command("curl -fsSL https://ollama.ai/install.sh | sh", "Installing Ollama on Linux")
        elif system == 'darwin':  # macOS
            print("Please install Ollama manually from https://ollama.ai/download")
            return
        elif system == 'windows':
            print("Please install Ollama manually from https://ollama.ai/download")
            return
    
    # Start Ollama service
    print("Starting Ollama service...")
    subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait a moment for service to start
    import time
    time.sleep(3)
    
    # Pull the quantized Llama model
    run_command("ollama pull llama3.1:8b-instruct-q4_K_M", "Downloading Llama 3.1 8B (quantized)")

def setup_directories():
    """Create necessary directories"""
    directories = [
        'local_ai',
        'local_models',
        'temp_audio', 
        'temp_images',
        'temp_music'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def create_config_file():
    """Create configuration file for local AI"""
    config_content = """
# Local AI Configuration
# Adjust these settings based on your GPU memory and preferences

[models]
# LLM settings
llm_model = llama3.1:8b-instruct-q4_K_M
ollama_url = http://localhost:11434

# Image generation settings  
default_image_model = flux  # Options: flux, sd15, sdxl
image_steps_flux = 4
image_steps_sd = 20

# TTS settings
tts_model = xtts_v2
tts_language = en

# Music generation settings
music_model = medium  # Options: small, medium, large
music_max_duration = 28

[memory]
# GPU memory management (in GB)
max_gpu_memory = 11.0
buffer_memory = 1.0

[paths]
temp_dir = ./temp
models_dir = ./local_models
"""
    
    with open('local_ai_config.ini', 'w') as f:
        f.write(config_content)
    
    print("📄 Created configuration file: local_ai_config.ini")

def main():
    """Main setup function"""
    try:
        # Install Python dependencies
        install_dependencies()
        
        # Setup Ollama
        install_ollama()
        
        # Create directories
        setup_directories()
        
        # Create config file
        create_config_file()
        
        print("\n" + "=" * 50)
        print("🎉 LOCAL AI SETUP COMPLETE!")
        print("=" * 50)
        print("\n📋 Next Steps:")
        print("1. Make sure Ollama service is running: ollama serve")
        print("2. Test the installation by running a sample script")
        print("3. Configure your AWS credentials if using S3 upload")
        print("4. Adjust settings in local_ai_config.ini if needed")
        print("\n💡 Tips:")
        print("- Models will be downloaded automatically on first use")
        print("- FLUX model (~7GB) will be downloaded for image generation")
        print("- XTTS model (~2GB) will be downloaded for TTS")
        print("- MusicGen model (~4GB) will be downloaded for music")
        print("\n🚀 You're ready to generate AI videos locally!")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()