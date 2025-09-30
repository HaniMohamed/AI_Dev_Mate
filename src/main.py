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

# ==========================
# Logging setup
# ==========================
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
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
    print("Available tasks:")
    for task_name in AVAILABLE_TASKS.keys():
        print(f" - {task_name}")

def run_task(task_name: str):
    if task_name not in AVAILABLE_TASKS:
        logger.error(f"Task '{task_name}' not found!")
        return
    # Require repository index for all tasks except the indexer itself
    if task_name != "repo_indexer":
        repo_root = os.getcwd()
        idx = RepoIndexer(ollama=ollama_service)
        if not idx.index_exists(repo_root):
            logger.error(
                "No index found for current directory. Please run indexing first: "
                "python -m src.main --index . [--with-context]"
            )
            return
    logger.info(f"Running task: {task_name}")
    task = AVAILABLE_TASKS[task_name]()
    task.run()
    print("\n=== Task Summary ===")
    print(task.summarize())
    logger.info(f"Task '{task_name}' completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Ollama Dev-Mate CLI")
    parser.add_argument("--list", action="store_true", help="List all available tasks")
    parser.add_argument("--run", type=str, help="Run a specific task by name")
    parser.add_argument("--index", type=str, metavar="PATH", help="Index a repository at PATH and output a summary")
    parser.add_argument("--with-context", action="store_true", help="Generate per-file AI context using the configured Ollama model (slow)")

    args = parser.parse_args()

    if args.list:
        list_tasks()
    elif args.run:
        run_task(args.run)
    elif args.index:
        idx = RepoIndexer(ollama=ollama_service)
        index = idx.index(args.index, generate_context=bool(args.with_context))
        print("\n=== Index Summary ===")
        print(idx.summarize(index))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
