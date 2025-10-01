# 🤖 Ollama Model Quick Reference

## 🚀 **Quick Commands**

### Basic Usage
```bash
# Use default model
python -m src.main --run code_review --repo-path .

# Use specific model
python -m src.main --run code_review --repo-path . --model codellama:13b

# Use custom temperature
python -m src.main --run code_review --repo-path . --model llama3.1:8b --temperature 0.2

# Use remote server
python -m src.main --run code_review --repo-path . --ollama-host http://remote:11434
```

### Environment Variables
```bash
# Set in .env file or environment
export OLLAMA_MODEL=codellama:13b
export OLLAMA_HOST=http://localhost:11434
export TEMPERATURE=0.2
export MAX_TOKENS=4000
```

## 📊 **Model Comparison**

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `codellama:7b` | 7B | ⚡⚡⚡ | ⭐⭐ | Quick reviews |
| `codellama:13b` | 13B | ⚡⚡ | ⭐⭐⭐⭐ | Balanced |
| `codellama:34b` | 34B | ⚡ | ⭐⭐⭐⭐⭐ | Deep analysis |
| `llama3.1:8b` | 8B | ⚡⚡ | ⭐⭐⭐ | General purpose |
| `deepseek-coder:6.7b` | 6.7B | ⚡⚡⚡ | ⭐⭐⭐⭐ | Code-specific |
| `qwen2.5-coder:7b` | 7B | ⚡⚡ | ⭐⭐⭐⭐ | Multi-language |

## 🎯 **Use Case Examples**

### Fast Development Workflow
```bash
python -m src.main --run code_review --repo-path . --model codellama:7b --fast-mode
```

### High Quality Review
```bash
python -m src.main --run code_review --repo-path . --model codellama:34b --max-tokens 8000
```

### Balanced Review
```bash
python -m src.main --run code_review --repo-path . --model codellama:13b --temperature 0.2
```

### Remote Server
```bash
python -m src.main --run code_review --repo-path . --model llama3.1:8b --ollama-host http://192.168.1.100:11434
```

## ⚙️ **Parameter Guide**

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| `--temperature` | 0.0-1.0 | 0.3 | Higher = more creative |
| `--max-tokens` | 100-8000 | 4000 | Response length limit |
| `--fast-mode` | flag | false | Faster, shorter responses |

## 🔧 **Troubleshooting**

### Model Not Found
```bash
# Check available models
ollama list

# Pull model
ollama pull codellama:13b
```

### Slow Performance
```bash
# Use smaller model
--model codellama:7b

# Enable fast mode
--fast-mode

# Reduce tokens
--max-tokens 2000
```

### Memory Issues
```bash
# Use smaller model
--model codellama:7b

# Reduce context
--max-tokens 2000
```

## 📝 **Configuration Files**

### .env File
```bash
OLLAMA_MODEL=codellama:13b
OLLAMA_HOST=http://localhost:11434
TEMPERATURE=0.2
MAX_TOKENS=4000
```

### Command Line
```bash
python -m src.main --run code_review \
  --repo-path . \
  --model codellama:13b \
  --temperature 0.2 \
  --max-tokens 4000
```

## 🎯 **Best Practices**

1. **Start with defaults** - Use `codellama:7b` first
2. **Test different models** - Find what works for your codebase
3. **Balance speed vs quality** - Use `13b` for most cases
4. **Use fast mode** for quick iterations
5. **Increase tokens** for detailed analysis
6. **Lower temperature** for consistent results
7. **Monitor performance** - Adjust based on response times

## 🚀 **Quick Start Commands**

```bash
# First time setup
ollama pull codellama:7b
python -m src.main --index .
python -m src.main --run code_review --repo-path .

# Try different models
python -m src.main --run code_review --repo-path . --model codellama:13b
python -m src.main --run code_review --repo-path . --model llama3.1:8b
python -m src.main --run code_review --repo-path . --model deepseek-coder:6.7b
```

This quick reference should help you get started with different Ollama models! 🎉