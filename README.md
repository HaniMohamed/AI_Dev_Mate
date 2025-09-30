# AI Dev Mate

An intelligent development assistant that helps with daily development tasks through AI-powered analysis and automation.

## Features

### 🗂️ Project Indexer
The core component that scans and indexes your project structure, providing comprehensive metadata for all other services.

**Key Capabilities:**
- **Multi-language Support**: Detects 20+ programming languages
- **Smart File Filtering**: Respects `.gitignore` rules and common ignore patterns
- **Dependency Detection**: Automatically parses `requirements.txt`, `pyproject.toml`, `package.json`, and `pubspec.yaml`
- **Framework Detection**: Identifies Django, Flask, FastAPI, React, Next.js, Flutter, and more
- **Git Integration**: Captures recent commits, current branch, and remote URL
- **AI Context Generation**: Optional LLM-generated context for each file (using Ollama)
- **Index Validation**: Automatically detects when indexes become stale
- **Progress Tracking**: Visual progress bars for large indexing operations

### 🔧 Other Services
- **Code Review**: AI-powered code analysis and suggestions
- **Commit Generator**: Intelligent commit message generation
- **Test Generator**: Automated test case generation
- **Documentation Generator**: AI-generated documentation

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AI_Dev_Mate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Basic Commands

```bash
# List all available tasks
python -m src.main --list

# Index a repository
python -m src.main --index /path/to/repo

# Index with AI context generation (slower but more detailed)
python -m src.main --index /path/to/repo --with-context

# Run a specific task
python -m src.main --run code_review
python -m src.main --run commit_generator
python -m src.main --run test_generator
python -m src.main --run doc_generator
```

### Advanced Index Management

```bash
# Check if index exists and is valid
python -m src.main --check-index /path/to/repo

# Force refresh stale indexes when running tasks
python -m src.main --run code_review --force-refresh

# Disable progress bars (useful for CI/CD)
python -m src.main --index /path/to/repo --no-progress
```

### Index Validation

The system automatically detects when indexes become stale by:
- Checking file modification times against index creation time
- Validating index format version compatibility
- Detecting when files are added or removed

When an index is stale, you'll see a warning like:
```
WARNING: Index is stale (created: 2024-01-15 10:30:00). Use --force-refresh to update it.
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Ollama Configuration
OLLAMA_MODEL=codellama:7b
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=120

# AI Generation Settings
MAX_TOKENS=1000
TEMPERATURE=0.3

# Git Settings
GIT_DEFAULT_BRANCH=main

# Logging
LOG_LEVEL=INFO
```

### Index Storage

Indexes are stored in `.aidm_index/index.json` within each repository. This location is:
- Automatically ignored by git (via `.gitignore` patterns)
- Portable across different machines
- Version-controlled for index format compatibility

## Architecture

### Core Components

- **`BaseTask`**: Abstract base class for all AI Dev Mate tasks
- **`RepoIndexer`**: Core indexing service with comprehensive project analysis
- **`FileService`**: Enhanced file operations with robust error handling
- **`GitService`**: Git integration with timeout and error handling
- **`OllamaService`**: AI model integration for context generation

### Error Handling

The system includes comprehensive error handling with custom exceptions:
- `FileServiceError`: File operation failures
- `GitServiceError`: Git command failures
- `IndexError`: Indexing operation failures
- `OllamaServiceError`: AI service failures
- `TaskError`: General task execution failures

### Performance Optimizations

- **Progress Indicators**: Visual feedback for long-running operations
- **Parallel Processing**: Efficient file scanning and processing
- **Smart Caching**: Index validation prevents unnecessary re-indexing
- **Size Limits**: Prevents indexing of extremely large files
- **Timeout Handling**: Prevents hanging on slow operations

## Development

### Running Tests

```bash
# Run the improvement test suite
python test_improvements.py

# Run specific tests
python -m pytest tests/
```

### Adding New Tasks

1. Create a new task class inheriting from `BaseTask`
2. Implement `run()` and `summarize()` methods
3. Register the task in `src/main.py`
4. Add appropriate error handling and progress indicators

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper error handling
4. Add tests for new functionality
5. Submit a pull request

## Troubleshooting

### Common Issues

**"No index found" error:**
```bash
# Create an index first
python -m src.main --index .
```

**"Index is stale" warning:**
```bash
# Refresh the index
python -m src.main --run your_task --force-refresh
```

**Git errors:**
- Ensure git is installed and accessible
- Check that the directory is a valid git repository
- Verify git permissions

**Ollama connection issues:**
- Ensure Ollama is running: `ollama serve`
- Check the `OLLAMA_HOST` environment variable
- Verify the model is available: `ollama list`

### Performance Tips

- Use `--no-progress` in CI/CD environments
- Avoid `--with-context` for large repositories unless needed
- Use `--force-refresh` sparingly; the system auto-detects stale indexes
- Consider indexing only specific subdirectories for very large projects

## License

[Add your license information here]

## Changelog

### Recent Improvements

- ✅ Enhanced error handling with custom exceptions
- ✅ Index validation and refresh mechanisms
- ✅ Progress indicators for better UX
- ✅ Force refresh capabilities
- ✅ Comprehensive CLI improvements
- ✅ Better git integration with timeout handling
- ✅ Robust file service with proper error handling
- ✅ Index format versioning for compatibility