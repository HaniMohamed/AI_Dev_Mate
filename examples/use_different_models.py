#!/usr/bin/env python3
"""
Examples of using different Ollama models with AI Dev Mate
"""

import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and display the result."""
    print(f"\n🚀 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="..")
        if result.returncode == 0:
            print("✅ Success!")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ Error:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Demonstrate different ways to use Ollama models."""
    
    print("🤖 AI Dev Mate - Different Model Usage Examples")
    print("=" * 60)
    
    # Example 1: Using environment variables
    print("\n📋 Example 1: Using Environment Variables")
    print("Set OLLAMA_MODEL=codellama:13b in your environment or .env file")
    
    # Example 2: Command line with specific model
    run_command([
        "python", "-m", "src.main", "--run", "code_review", 
        "--repo-path", ".", "--model", "codellama:13b"
    ], "Code review with CodeLlama 13B model")
    
    # Example 3: Using Llama 3.1 with custom temperature
    run_command([
        "python", "-m", "src.main", "--run", "code_review", 
        "--repo-path", ".", "--model", "llama3.1:8b", "--temperature", "0.2"
    ], "Code review with Llama 3.1 8B and custom temperature")
    
    # Example 4: Fast mode with smaller model
    run_command([
        "python", "-m", "src.main", "--run", "code_review", 
        "--repo-path", ".", "--model", "codellama:7b", "--fast-mode"
    ], "Fast code review with CodeLlama 7B")
    
    # Example 5: High quality review with larger model
    run_command([
        "python", "-m", "src.main", "--run", "code_review", 
        "--repo-path", ".", "--model", "codellama:34b", "--max-tokens", "8000"
    ], "High quality review with CodeLlama 34B")
    
    # Example 6: Using remote Ollama server
    run_command([
        "python", "-m", "src.main", "--run", "code_review", 
        "--repo-path", ".", "--model", "deepseek-coder:6.7b",
        "--ollama-host", "http://192.168.1.100:11434"
    ], "Code review using remote Ollama server")
    
    print("\n🎯 Summary of Model Options:")
    print("• --model: Specify the Ollama model (e.g., codellama:13b)")
    print("• --ollama-host: Specify Ollama server URL")
    print("• --temperature: Control model creativity (0.0-1.0)")
    print("• --max-tokens: Limit response length")
    print("• Environment variables: OLLAMA_MODEL, OLLAMA_HOST, etc.")
    
    print("\n📚 Recommended Models:")
    print("• codellama:7b - Fast, good for quick reviews")
    print("• codellama:13b - Balanced speed and quality")
    print("• codellama:34b - High quality, slower")
    print("• llama3.1:8b - General purpose, good balance")
    print("• deepseek-coder:6.7b - Specialized for coding")
    print("• qwen2.5-coder:7b - Multi-language support")

if __name__ == "__main__":
    main()