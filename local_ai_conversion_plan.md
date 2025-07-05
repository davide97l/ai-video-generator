# Local AI Video Generator Conversion Plan

## Current External API Dependencies

Your AI video generator currently uses these external services:

1. **GPT-4 via Mindsflow agents** - Script generation (`generateVideoScript.py`)
2. **Replicate API** - Image generation using SDXL/SD (`PromptImagesToVideo.py`)
3. **Replicate API** - Music generation using MusicGen (`MusicGeneration.py`)  
4. **Azure Text-to-Speech** - Voice synthesis (`textToSpeech.py`)

## Local Alternatives for 12GB GPU RAM

### 1. Text Generation (GPT-4 Replacement)

**Recommended: Llama 3.1 8B Instruct**
- **Memory requirement**: ~5-6GB VRAM
- **Installation**: Use Ollama for easy setup
- **Performance**: Excellent for script generation tasks

**Alternative: Mistral 7B Instruct**
- **Memory requirement**: ~4-5GB VRAM
- **Faster inference but slightly lower quality

### 2. Image Generation (SDXL/SD Replacement)

**Recommended: FLUX.1-schnell (4-step)**
- **Memory requirement**: ~6-8GB VRAM
- **Quality**: Superior to SDXL
- **Speed**: 4-step generation is very fast

**Alternative: Stable Diffusion 1.5 + LoRAs**
- **Memory requirement**: ~3-4GB VRAM
- **More memory efficient option

### 3. Music Generation (MusicGen Replacement)

**Recommended: AudioCraft MusicGen Medium**
- **Memory requirement**: ~4-5GB VRAM
- **Quality**: Similar to Replicate version
- **Local inference**: Facebook's open-source model

### 4. Text-to-Speech (Azure TTS Replacement)

**Recommended: Coqui XTTS v2**
- **Memory requirement**: ~2-3GB VRAM
- **Features**: Voice cloning, multilingual, high quality
- **Real-time capable**: Very natural sounding

**Alternative: Bark**
- **Memory requirement**: ~3-4GB VRAM
- **Features**: Supports emotions, multiple languages

## Memory Management Strategy

Since you have 12GB GPU RAM, we'll implement smart model loading/unloading:

1. **Sequential Processing**: Load models only when needed
2. **Memory Clearing**: Explicit GPU memory cleanup between stages
3. **Optimization**: Use quantized models where possible

## Implementation Plan

### Phase 1: Setup Local Model Infrastructure

1. Install Ollama for LLM management
2. Setup Hugging Face Transformers
3. Install Coqui TTS
4. Setup AudioCraft

### Phase 2: Convert Each Component

1. **Script Generation**: Replace Mindsflow agents with local Llama
2. **Image Generation**: Replace Replicate with local FLUX/SD
3. **Music Generation**: Replace Replicate MusicGen with local version
4. **TTS**: Replace Azure with Coqui XTTS v2

### Phase 3: Memory Optimization

1. Implement model loading/unloading
2. Add GPU memory monitoring
3. Optimize batch sizes and parameters

## Estimated Performance Impact

- **Script Generation**: ~5-10 seconds (vs ~2-3 seconds external)
- **Image Generation**: ~3-5 seconds per image (vs ~5-10 seconds external)
- **Music Generation**: ~30-60 seconds (vs ~20-30 seconds external)
- **TTS**: ~1-3 seconds (vs ~2-5 seconds external)

**Overall**: Comparable or better performance with complete privacy and no API costs.

## Next Steps

Would you like me to start implementing the conversion? I recommend starting with the TTS replacement since it will have the most noticeable quality improvement and uses the least GPU memory.