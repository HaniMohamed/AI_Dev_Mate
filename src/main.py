# src/main.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import logging
from src.services.ollama_service import OllamaService
from src.modules.code_review import CodeReviewTask
from src.modules.commit_generator import CommitGeneratorTask
from src.modules.test_generator import TestGeneratorTask
from src.modules.doc_generator import DocGeneratorTask
from src.services.repo_indexer import RepoIndexer
from src.modules.repo_indexer_task import RepoIndexTask
from src.utils.console import aidm_console

# ==========================
# Logging setup
# ==========================
import sys
from rich.logging import RichHandler

# Configure rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=aidm_console.console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

# ==========================
# Task Registration
# ==========================
ollama_service = OllamaService()
AVAILABLE_TASKS = {
    "code_review": lambda: CodeReviewTask(ollama_service),
    "commit_generator": lambda: CommitGeneratorTask(ollama_service),
    "test_generator": lambda: TestGeneratorTask(ollama_service),
    "doc_generator": lambda: DocGeneratorTask(ollama_service),
    "repo_indexer": lambda: RepoIndexTask(),
}

# ==========================
# CLI
# ==========================
def list_tasks():
    """Display available tasks with beautiful formatting."""
    aidm_console.print_header("🤖 AI Dev Mate", "Available Tasks")
    
    task_descriptions = {
        "code_review": "🔍 Aggressive AI-powered code review with branch comparison",
        "commit_generator": "📝 Intelligent commit message generation",
        "test_generator": "🧪 Automated test case generation",
        "doc_generator": "📚 AI-generated documentation",
        "repo_indexer": "📁 Project structure indexing and analysis"
    }
    
    from rich.table import Table
    from rich import box
    table = Table(title="Available Tasks", box=box.ROUNDED)
    table.add_column("Task Name", style="accent", width=20)
    table.add_column("Description", style="default")
    
    for task_name in AVAILABLE_TASKS.keys():
        description = task_descriptions.get(task_name, "AI-powered development task")
        table.add_row(f"[code]{task_name}[/code]", description)
    
    aidm_console.print_table(table)
    aidm_console.print_info("Use --run <task_name> to execute a task")

def run_task(task_name: str, force_refresh: bool = False, base_branch: str = None, target_branch: str = None, repo_path: str = None, max_files: int = None, fast_mode: bool = False, serial_mode: bool = False, model: str = None, ollama_host: str = None, temperature: float = None, max_tokens: int = None):
    """Run a specific task with beautiful output."""
    if task_name not in AVAILABLE_TASKS:
        aidm_console.print_error(f"Task '{task_name}' not found!")
        return
    
    # Show task header
    task_descriptions = {
        "code_review": "🔍 Aggressive Code Review",
        "commit_generator": "📝 Commit Generator", 
        "test_generator": "🧪 Test Generator",
        "doc_generator": "📚 Documentation Generator",
        "repo_indexer": "📁 Repository Indexer"
    }
    
    task_title = task_descriptions.get(task_name, f"Task: {task_name}")
    aidm_console.print_header(task_title, "Executing AI-powered development task")
    
    # Create OllamaService with custom parameters if provided
    custom_ollama = None
    if model or ollama_host or temperature is not None or max_tokens is not None:
        custom_ollama = OllamaService(
            model_name=model,
            host=ollama_host,
            timeout=ollama_service.timeout
        )
        # Update settings if provided
        if temperature is not None:
            custom_ollama.temperature = temperature
        if max_tokens is not None:
            custom_ollama.max_tokens = max_tokens
        
        aidm_console.print_info(f"🤖 Using custom model: {custom_ollama.model_name}")
        if ollama_host:
            aidm_console.print_info(f"🌐 Ollama host: {custom_ollama.host}")
    
    # Use custom OllamaService if provided, otherwise use default
    active_ollama = custom_ollama or ollama_service
    
    # Require repository index for all tasks except the indexer itself
    if task_name != "repo_indexer":
        repo_root = os.getcwd()
        idx = RepoIndexer(ollama=active_ollama)
        
        if not idx.index_exists(repo_root):
            aidm_console.print_error(
                "No index found for current directory. Please run indexing first: "
                "python -m src.main --index . [--with-context]"
            )
            return
        
        # Check if index needs refresh
        if idx.needs_refresh(repo_root):
            if force_refresh:
                aidm_console.print_info("Index is stale, refreshing...")
                with aidm_console.create_progress("Refreshing index") as progress:
                    task_progress = progress.add_task("Refreshing...", total=100)
                    idx.force_refresh_index(repo_root, generate_context=False, show_progress=True)
                    progress.update(task_progress, completed=100)
                aidm_console.print_success("Index refreshed successfully!")
            else:
                index_age = idx.get_index_age(repo_root)
                age_str = "unknown" if index_age is None else f"{index_age.strftime('%Y-%m-%d %H:%M:%S')}"
                aidm_console.print_warning(
                    f"Index is stale (created: {age_str}). Use --force-refresh to update it. "
                    "Continuing with existing index..."
                )
    
    aidm_console.print_primary(f"Running task: {task_name}")
    
    try:
        # Create task with repo_path if provided
        if task_name == "code_review":
            task = CodeReviewTask(active_ollama, repo_path)
        elif task_name == "repo_indexer":
            task = RepoIndexTask(repo_path, force_refresh)
        else:
            # For other tasks, create with custom OllamaService
            if task_name in ["commit_generator", "test_generator", "doc_generator"]:
                if task_name == "commit_generator":
                    task = CommitGeneratorTask(active_ollama)
                elif task_name == "test_generator":
                    task = TestGeneratorTask(active_ollama)
                elif task_name == "doc_generator":
                    task = DocGeneratorTask(active_ollama)
            else:
                task = AVAILABLE_TASKS[task_name]()
        
        # Pass additional arguments to code review task
        if task_name == "code_review" and hasattr(task, 'set_review_params'):
            task.set_review_params(base_branch, target_branch, max_files, fast_mode, serial_mode)
        
        task.run()
        
        aidm_console.print_separator()
        aidm_console.print_header("📋 Task Summary", "Execution completed")
        aidm_console.print_task_summary(task_name, "Completed", task.summarize())
        aidm_console.print_success(f"Task '{task_name}' completed successfully!")
        
    except Exception as e:
        aidm_console.print_error(f"Task '{task_name}' failed: {str(e)}")
        logger.error(f"Task execution failed: {e}")

def main():
    """Main CLI entry point with beautiful output."""
    parser = argparse.ArgumentParser(
        description="🤖 AI Dev Mate - Intelligent Development Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --list                    # List all available tasks
  python -m src.main --index .                 # Index current directory
  python -m src.main --run code_review --repo-path .  # Run code review on current directory
  python -m src.main --run code_review --repo-path /path/to/repo --base-branch main --target-branch feature-branch
  python -m src.main --run code_review --repo-path . --base-branch develop  # Compare current changes with develop branch
  python -m src.main --run code_review --model codellama:13b  # Use specific model
  python -m src.main --run code_review --model llama3.1:8b --temperature 0.2  # Custom model and temperature
  python -m src.main --run code_review --ollama-host http://remote:11434  # Use remote Ollama server
  python -m src.main --run repo_indexer --repo-path /path/to/repo  # Index specific repository
  python -m src.main --check-index /path/to/repo  # Check index status
        """
    )
    
    parser.add_argument("--list", action="store_true", help="List all available tasks")
    parser.add_argument("--run", type=str, help="Run a specific task by name")
    parser.add_argument("--index", type=str, metavar="PATH", help="Index a repository at PATH and output a summary")
    parser.add_argument("--with-context", action="store_true", help="Generate per-file AI context using the configured Ollama model (slow)")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh index if stale when running tasks")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bars during indexing")
    parser.add_argument("--check-index", type=str, metavar="PATH", help="Check if index exists and is valid for PATH")
    parser.add_argument("--repo-path", type=str, metavar="PATH", help="Path to repository (for tasks that require it)")
    
    # Code review specific arguments
    parser.add_argument("--base-branch", type=str, metavar="BRANCH", help="Base branch to compare against (default: main)")
    parser.add_argument("--target-branch", type=str, metavar="BRANCH", help="Target branch to compare (default: current changes)")
    parser.add_argument("--max-files", type=int, metavar="N", help="Maximum number of files to review (default: 50)")
    parser.add_argument("--fast-mode", action="store_true", help="Enable fast mode with parallel processing and shorter responses")
    parser.add_argument("--serial", action="store_true", help="Force serial processing instead of parallel (slower but more reliable)")
    
    # Model configuration arguments
    parser.add_argument("--model", type=str, metavar="MODEL", help="Ollama model to use (e.g., codellama:13b, llama3.1:8b)")
    parser.add_argument("--ollama-host", type=str, metavar="HOST", help="Ollama server host (default: http://localhost:11434)")
    parser.add_argument("--temperature", type=float, metavar="TEMP", help="Model temperature (0.0-1.0, default: 0.3)")
    parser.add_argument("--max-tokens", type=int, metavar="TOKENS", help="Maximum response tokens (default: 4000)")

    args = parser.parse_args()

    if args.list:
        list_tasks()
    elif args.run:
        run_task(args.run, force_refresh=args.force_refresh, 
                base_branch=args.base_branch, target_branch=args.target_branch,
                repo_path=args.repo_path, max_files=args.max_files, fast_mode=args.fast_mode,
                serial_mode=args.serial, model=args.model, ollama_host=args.ollama_host, 
                temperature=args.temperature, max_tokens=args.max_tokens)
    elif args.index:
        aidm_console.print_header("📁 Repository Indexing", f"Indexing: {args.index}")
        
        idx = RepoIndexer(ollama=ollama_service)
        show_progress = not args.no_progress
        
        try:
            with aidm_console.create_progress("Indexing repository") as progress:
                task_progress = progress.add_task("Processing...", total=100)
                index = idx.index(args.index, generate_context=bool(args.with_context), show_progress=show_progress)
                progress.update(task_progress, completed=100)
            
            aidm_console.print_separator()
            aidm_console.print_index_summary(index)
            
            # Show file list if not too many files
            files = index.get("files", [])
            if len(files) <= 20:
                aidm_console.print_file_list(files)
            
            # Show dependencies
            dependencies = index.get("dependencies", {})
            aidm_console.print_dependencies(dependencies)
            
            # Show git info
            git_info = index.get("git", {})
            aidm_console.print_git_info(git_info)
            
        except Exception as e:
            aidm_console.print_error(f"Indexing failed: {str(e)}")
            
    elif args.check_index:
        idx = RepoIndexer(ollama=ollama_service)
        path = os.path.abspath(args.check_index)
        
        aidm_console.print_header("🔍 Index Status Check", f"Checking: {path}")
        
        if not idx.index_exists(path):
            aidm_console.print_error(f"No index found for: {path}")
        elif idx.is_index_valid(path):
            index_age = idx.get_index_age(path)
            age_str = "unknown" if index_age is None else index_age.strftime('%Y-%m-%d %H:%M:%S')
            aidm_console.print_success(f"Index is valid for: {path}")
            aidm_console.print_info(f"Created: {age_str}")
        else:
            index_age = idx.get_index_age(path)
            age_str = "unknown" if index_age is None else index_age.strftime('%Y-%m-%d %H:%M:%S')
            aidm_console.print_warning(f"Index is stale for: {path}")
            aidm_console.print_info(f"Created: {age_str}")
            aidm_console.print_info("Use --force-refresh to update the index")
    else:
        # Show welcome and help with beautiful formatting
        aidm_console.print_welcome()
        aidm_console.print_help_menu()
        aidm_console.print_separator()
        parser.print_help()

if __name__ == "__main__":
    main()
