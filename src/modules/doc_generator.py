# src/modules/doc_generator.py
from core.models import BaseTask
from services.ollama_service import OllamaService
from services.file_service import FileService

class DocGeneratorTask(BaseTask):
    def __init__(self, ollama: OllamaService):
        super().__init__("Documentation Generator")
        self.ollama = ollama
        self.documentation = ""

    def run(self):
        py_files = FileService.list_python_files("src")
        self.documentation = self.ollama.run_prompt(
            f"Generate Markdown documentation for the following Python files:\n{py_files[:5]}"
        )
        self.completed = True

    def summarize(self) -> str:
        return self.documentation
