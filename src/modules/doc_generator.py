# src/modules/doc_generator.py
from src.core.models import BaseTask
from src.core.utils import check_and_load_index
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
        
        # Check if indexed data is available
        index_data = check_and_load_index(ollama=self.ollama)
        if index_data is None:
            self.documentation = "Documentation generation failed: No indexed data available. Please index the project first."
            self.completed = True
            return
        
        try:
            # Use indexed files instead of scanning manually
            indexed_files = index_data.get("files", [])
            py_files = [f["path"] for f in indexed_files if f.get("language") == "Python"]
            
            if not py_files:
                aidm_console.print_warning("No Python files found in indexed data.")
                self.documentation = "No Python files found to generate documentation for."
            else:
                aidm_console.print_primary(f"Found {len(py_files)} Python files from index")
                
                # Show file list
                file_list = "\n".join([f"- {f}" for f in py_files[:5]])
                if len(py_files) > 5:
                    file_list += f"\n- ... and {len(py_files) - 5} more files"
                aidm_console.print_markdown(f"**Files to analyze:**\n{file_list}")
                
                # Generate documentation using indexed context
                with aidm_console.create_progress("Generating documentation") as progress:
                    task = progress.add_task("Analyzing code...", total=100)
                    # Include project context from index for better documentation
                    project_summary = index_data.get("summary", {})
                    context_info = f"Project languages: {project_summary.get('languages', {})}\nFramework hints: {project_summary.get('framework_hints', [])}"
                    self.documentation = self.ollama.run_prompt(
                        f"{context_info}\n\nGenerate comprehensive Markdown documentation for the following Python files:\n{py_files[:5]}"
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
