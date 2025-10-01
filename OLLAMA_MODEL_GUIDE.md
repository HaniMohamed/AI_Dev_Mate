# Using Different Ollama Models

This guide shows you how to configure and use different Ollama models with the AI Dev Mate code review system.

## 🎯 **Quick Start**

### Method 1: Environment Variables (Recommended)

Create a `.env` file in your project root:

```bash
# .env file
OLLAMA_MODEL=llama3.1:8b
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=300
```

### Method 2: Command Line Arguments

The system supports passing model parameters directly:

```bash
python -m src.main --run code_review --repo-path . --model llama3.1:8b
```

## 🔧 **Configuration Options**

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `codellama:7b` | The Ollama model to use |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_TIMEOUT` | `300` | Request timeout in seconds |
| `OLLAMA_MAX_RETRIES` | `3` | Number of retry attempts |
| `OLLAMA_RETRY_DELAY` | `2` | Initial retry delay in seconds |
| `MAX_TOKENS` | `4000` | Maximum response length |
| `TEMPERATURE` | `0.3` | Model creativity (0.0-1.0) |

### Example .env Configuration

```bash
# .env
OLLAMA_MODEL=llama3.1:8b
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=600
OLLAMA_MAX_RETRIES=5
OLLAMA_RETRY_DELAY=3
MAX_TOKENS=8000
TEMPERATURE=0.2
```

## 🤖 **Recommended Models for Code Review**

### **Best for Code Review:**

1. **`codellama:13b`** - Excellent for code analysis
   ```bash
   OLLAMA_MODEL=codellama:13b
   ```

2. **`llama3.1:8b`** - Good balance of speed and quality
   ```bash
   OLLAMA_MODEL=llama3.1:8b
   ```

3. **`deepseek-coder:6.7b`** - Specialized for coding tasks
   ```bash
   OLLAMA_MODEL=deepseek-coder:6.7b
   ```

4. **`qwen2.5-coder:7b`** - Strong code understanding
   ```bash
   OLLAMA_MODEL=qwen2.5-coder:7b
   ```

### **Fast Models (Less Quality):**

1. **`codellama:7b`** - Default, fast but basic
   ```bash
   OLLAMA_MODEL=codellama:7b
   ```

2. **`llama3.1:7b`** - Good speed/quality balance
   ```bash
   OLLAMA_MODEL=llama3.1:7b
   ```

### **High Quality Models (Slower):**

1. **`codellama:34b`** - Best quality, requires more resources
   ```bash
   OLLAMA_MODEL=codellama:34b
   ```

2. **`llama3.1:70b`** - Excellent but very resource intensive
   ```bash
   OLLAMA_MODEL=llama3.1:70b
   ```

## 🚀 **Usage Examples**

### Example 1: Using a Different Model for Code Review

```bash
# Set environment variable
export OLLAMA_MODEL=llama3.1:8b

# Run code review
python -m src.main --run code_review --repo-path /path/to/your/repo
```

### Example 2: Using a Remote Ollama Server

```bash
# .env file
OLLAMA_MODEL=codellama:13b
OLLAMA_HOST=http://192.168.1.100:11434
OLLAMA_TIMEOUT=600

# Run with remote server
python -m src.main --run code_review --repo-path .
```

### Example 3: High-Quality Review with Larger Model

```bash
# .env file
OLLAMA_MODEL=codellama:34b
OLLAMA_TIMEOUT=900
MAX_TOKENS=8000
TEMPERATURE=0.1

# Run comprehensive review
python -m src.main --run code_review --repo-path . --fast-mode
```

## 🔍 **Model Comparison for Code Review**

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `codellama:7b` | 7B | ⚡⚡⚡ | ⭐⭐ | Quick reviews |
| `codellama:13b` | 13B | ⚡⚡ | ⭐⭐⭐⭐ | Balanced reviews |
| `codellama:34b` | 34B | ⚡ | ⭐⭐⭐⭐⭐ | Deep analysis |
| `llama3.1:8b` | 8B | ⚡⚡ | ⭐⭐⭐ | General purpose |
| `deepseek-coder:6.7b` | 6.7B | ⚡⚡⚡ | ⭐⭐⭐⭐ | Code-specific tasks |
| `qwen2.5-coder:7b` | 7B | ⚡⚡ | ⭐⭐⭐⭐ | Multi-language support |

## 🛠️ **Advanced Configuration**

### Custom Model Parameters

You can modify the Ollama service to use custom parameters:

```python
# In src/services/ollama_service.py
def run_prompt(self, prompt: str, **kwargs):
    payload = {
        "model": self.model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": kwargs.get("temperature", 0.3),
            "num_predict": kwargs.get("max_tokens", 4000),
            "num_ctx": kwargs.get("context_size", 4096),
            # Add more custom options here
        }
    }
```

### Model-Specific Optimizations

Different models may benefit from different settings:

**For CodeLlama models:**
```bash
TEMPERATURE=0.1
MAX_TOKENS=6000
```

**For Llama models:**
```bash
TEMPERATURE=0.2
MAX_TOKENS=4000
```

**For DeepSeek models:**
```bash
TEMPERATURE=0.15
MAX_TOKENS=5000
```

## 🔧 **Troubleshooting**

### Common Issues:

1. **Model not found:**
   ```bash
   # Check available models
   ollama list
   
   # Pull the model if needed
   ollama pull codellama:13b
   ```

2. **Timeout errors:**
   ```bash
   # Increase timeout for larger models
   OLLAMA_TIMEOUT=900
   ```

3. **Memory issues:**
   ```bash
   # Use smaller model or reduce context
   OLLAMA_MODEL=codellama:7b
   MAX_TOKENS=2000
   ```

4. **Slow responses:**
   ```bash
   # Use faster model
   OLLAMA_MODEL=codellama:7b
   TEMPERATURE=0.1
   ```

## 📊 **Performance Tips**

### For Speed:
- Use smaller models (`7b` variants)
- Reduce `MAX_TOKENS`
- Lower `TEMPERATURE`
- Enable `--fast-mode`

### For Quality:
- Use larger models (`13b`, `34b` variants)
- Increase `MAX_TOKENS`
- Higher `TEMPERATURE` (0.2-0.3)
- Disable `--fast-mode`

### For Balance:
- Use medium models (`8b`, `13b`)
- Default settings work well
- Monitor response times

## 🎯 **Best Practices**

1. **Start with defaults** and adjust based on your needs
2. **Test different models** to find the best fit for your codebase
3. **Monitor performance** - balance speed vs quality
4. **Use appropriate model sizes** for your hardware
5. **Keep models updated** - pull latest versions regularly

## 🔗 **Useful Commands**

```bash
# List available models
ollama list

# Pull a new model
ollama pull codellama:13b

# Remove a model
ollama rm codellama:7b

# Check model info
ollama show codellama:13b

# Test model locally
ollama run codellama:13b "Review this Python code for security issues"
```

This guide should help you choose and configure the best Ollama model for your code review needs! 🚀