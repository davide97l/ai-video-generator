#!/usr/bin/env python3
"""
Test script for Local AI Video Generator
Verifies all components work correctly
"""

import sys
import os
import time
import traceback

def test_memory_manager():
    """Test GPU memory management"""
    print("🧠 Testing Memory Manager...")
    try:
        sys.path.append('local_ai')
        from memory_manager import memory_manager
        
        # Test memory monitoring
        usage = memory_manager.get_gpu_memory_usage()
        print(f"   GPU Memory: {usage['used']:.1f}GB used, {usage['available']:.1f}GB available")
        
        if usage['total'] > 0:
            print("   ✅ GPU detected and accessible")
        else:
            print("   ⚠️  No GPU detected - will use CPU")
        
        return True
    except Exception as e:
        print(f"   ❌ Memory manager failed: {e}")
        return False

def test_ollama():
    """Test Ollama service"""
    print("🦙 Testing Ollama Service...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"   ✅ Ollama service running with {len(models)} models")
            
            # Check for Llama model
            llama_models = [m for m in models if "llama" in m.get("name", "").lower()]
            if llama_models:
                print(f"   ✅ Llama model available: {llama_models[0]['name']}")
            else:
                print("   ⚠️  No Llama model found - run: ollama pull llama3.1:8b-instruct-q4_K_M")
            
            return True
        else:
            print(f"   ❌ Ollama service error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ollama service not running: {e}")
        print("   💡 Start with: ollama serve")
        return False

def test_script_generation():
    """Test local script generation"""
    print("📝 Testing Script Generation...")
    try:
        sys.path.append('local_ai')
        from local_llm import LocalScriptGenerator
        
        generator = LocalScriptGenerator()
        
        # Test simple generation
        result = generator.generate_paragraph_script("Benefits of eating apples")
        
        if result and len(result) > 50:
            print("   ✅ Script generation working")
            print(f"   📄 Generated {len(result)} characters")
            return True
        else:
            print("   ❌ Script generation failed - output too short")
            return False
            
    except Exception as e:
        print(f"   ❌ Script generation failed: {e}")
        traceback.print_exc()
        return False

def test_tts():
    """Test local text-to-speech"""
    print("🎙️ Testing Text-to-Speech...")
    try:
        sys.path.append('local_ai')
        from local_tts import LocalTTS
        
        tts = LocalTTS()
        
        # Test simple TTS
        audio_url, duration = tts.generate_speech("Hello world test", "en", 1.0)
        
        if audio_url and duration > 0:
            print(f"   ✅ TTS working - generated {duration:.1f}s audio")
            print(f"   🔊 Audio saved: {audio_url}")
            return True
        else:
            print("   ❌ TTS generation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ TTS failed: {e}")
        traceback.print_exc()
        return False

def test_image_generation():
    """Test local image generation"""
    print("🎨 Testing Image Generation...")
    try:
        sys.path.append('local_ai')
        from local_image_gen import LocalImageGenerator
        
        generator = LocalImageGenerator()
        
        # Test with SD15 (smaller model)
        img_url = generator.generate_image(
            "A beautiful sunset",
            width=512,
            height=512,
            model="sd15",  # Use smaller model for testing
            num_inference_steps=10  # Fewer steps for faster testing
        )
        
        if img_url:
            print(f"   ✅ Image generation working")
            print(f"   🖼️  Image saved: {img_url}")
            return True
        else:
            print("   ❌ Image generation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Image generation failed: {e}")
        traceback.print_exc()
        return False

def test_music_generation():
    """Test local music generation"""
    print("🎵 Testing Music Generation...")
    try:
        sys.path.append('local_ai')
        from local_music_gen import LocalMusicGenerator
        
        generator = LocalMusicGenerator()
        
        # Test with small model and short duration
        music_url = generator.generate_music(
            "Calm ambient music",
            duration=5.0,  # Short duration for testing
            model_size="small"  # Use smaller model
        )
        
        if music_url:
            print(f"   ✅ Music generation working")
            print(f"   🎵 Music saved: {music_url}")
            return True
        else:
            print("   ❌ Music generation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Music generation failed: {e}")
        traceback.print_exc()
        return False

def test_mindsflow_functions():
    """Test the drop-in replacement functions"""
    print("🔄 Testing Mindsflow Functions...")
    try:
        # Test script generation function
        sys.path.append('agent-video-generator/functions')
        from local_generateVideoScript import mindsflow_function as script_func
        
        result = script_func({
            "topic": "Benefits of exercise",
            "text_style": "informative"
        }, None)
        
        if result and 'json_string' in result:
            print("   ✅ Local script function working")
        else:
            print("   ❌ Local script function failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Mindsflow functions failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 LOCAL AI VIDEO GENERATOR TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Memory Manager", test_memory_manager),
        ("Ollama Service", test_ollama),
        ("Script Generation", test_script_generation),
        ("Text-to-Speech", test_tts),
        ("Image Generation", test_image_generation),
        ("Music Generation", test_music_generation),
        ("Mindsflow Functions", test_mindsflow_functions)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 30)
        
        start_time = time.time()
        try:
            success = test_func()
            duration = time.time() - start_time
            
            results[test_name] = {
                'success': success,
                'duration': duration
            }
            
            if success:
                print(f"   ⏱️  Completed in {duration:.1f}s")
            else:
                print(f"   ⏱️  Failed after {duration:.1f}s")
                
        except KeyboardInterrupt:
            print(f"   ⏹️  Test interrupted by user")
            break
        except Exception as e:
            print(f"   💥 Test crashed: {e}")
            results[test_name] = {
                'success': False,
                'duration': time.time() - start_time
            }
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = result['duration']
        print(f"{status} {test_name:<20} ({duration:.1f}s)")
    
    print(f"\n🏆 Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your local AI setup is ready!")
        print("\n📋 Next steps:")
        print("1. Update your code to use local_ functions")
        print("2. Configure settings in local_ai_config.ini")
        print("3. Start generating videos locally!")
    else:
        print(f"\n⚠️  {total-passed} tests failed. Check the error messages above.")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure all dependencies are installed: python setup_local_ai.py")
        print("2. Ensure Ollama is running: ollama serve")
        print("3. Check GPU memory availability: nvidia-smi")
        print("4. Verify disk space for model downloads (~20GB needed)")

if __name__ == "__main__":
    main()