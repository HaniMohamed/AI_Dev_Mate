# src/modules/doc_generator.py
from src.core.models import BaseTask
from src.services.ollama_service import OllamaService
from src.services.file_service import FileService
from src.utils.console import aidm_console

class DocGeneratorTask(BaseTask):
    def __init__(self, ollama: OllamaService):
        super().__init__("Documentation Generator")
        self.ollama = ollama
        self.documentation = ""

    def run(self):
        """Run documentation generation with beautiful output."""
        aidm_console.print_header("📚 Documentation Generator", "Generating project documentation")
        
        try:
            aidm_console.print_info("Scanning Python files...")
            py_files = FileService.list_python_files("src")
            
            if not py_files:
                aidm_console.print_warning("No Python files found in src directory.")
                self.documentation = "No Python files found to generate documentation for."
            else:
                aidm_console.print_primary(f"Found {len(py_files)} Python files")
                
                # Show file list
                file_list = "\n".join([f"- {f}" for f in py_files[:5]])
                if len(py_files) > 5:
                    file_list += f"\n- ... and {len(py_files) - 5} more files"
                aidm_console.print_markdown(f"**Files to analyze:**\n{file_list}")
                
                # Generate documentation
                with aidm_console.create_progress("Generating documentation") as progress:
                    task = progress.add_task("Analyzing code...", total=100)
                    self.documentation = self.ollama.run_prompt(
                        f"Generate Markdown documentation for the following Python files:\n{py_files[:5]}"
                    )
                    progress.update(task, completed=100)
                
                aidm_console.print_success("Documentation generated successfully!")
        except Exception as e:
            aidm_console.print_error(f"Documentation generation failed: {e}")
            self.documentation = f"Documentation generation failed: {e}"
        
        self.completed = True

    def summarize(self) -> str:
        """Return generated documentation with beautiful formatting."""
        if self.documentation:
            aidm_console.print_separator()
            aidm_console.print_header("📋 Generated Documentation", "AI-powered project documentation")
            aidm_console.print_markdown(self.documentation)
        return self.documentation
