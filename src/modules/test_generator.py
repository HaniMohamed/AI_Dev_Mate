# src/modules/test_generator.py
from src.core.models import BaseTask
from src.services.ollama_service import OllamaService
from src.services.file_service import FileService

class TestGeneratorTask(BaseTask):
    def __init__(self, ollama: OllamaService):
        super().__init__("Test Generator")
        self.ollama = ollama
        self.generated_tests = ""

    def run(self):
        py_files = FileService.list_python_files("src")
        self.generated_tests = self.ollama.run_prompt(
            f"Generate unit tests for the following Python files:\n{py_files[:5]}"
        )
        self.completed = True

    def summarize(self) -> str:
        return self.generated_tests
