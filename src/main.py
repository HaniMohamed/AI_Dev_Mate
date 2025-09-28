# src/main.py
import argparse
import logging
from services.ollama_service import OllamaService
from modules.code_review import CodeReviewTask
from modules.commit_generator import CommitGeneratorTask
from modules.test_generator import TestGeneratorTask
from modules.doc_generator import DocGeneratorTask

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

    args = parser.parse_args()

    if args.list:
        list_tasks()
    elif args.run:
        run_task(args.run)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
