# src/modules/test_generator.py
from src.core.models import BaseTask
from src.core.utils import check_and_load_index
from src.services.ollama_service import OllamaService
from src.services.file_service import FileService
from src.utils.console import aidm_console

class TestGeneratorTask(BaseTask):
    def __init__(self, ollama: OllamaService):
        super().__init__("Test Generator")
        self.ollama = ollama
        self.generated_tests = ""

    def run(self):
        """Run test generation with beautiful output."""
        aidm_console.print_header("🧪 Test Generator", "Generating unit tests")
        
        # Check if indexed data is available
        index_data = check_and_load_index(ollama=self.ollama)
        if index_data is None:
            self.generated_tests = "Test generation failed: No indexed data available. Please index the project first."
            self.completed = True
            return
        
        try:
            # Use indexed files instead of scanning manually
            indexed_files = index_data.get("files", [])
            py_files = [f["path"] for f in indexed_files if f.get("language") == "Python"]
            
            if not py_files:
                aidm_console.print_warning("No Python files found in indexed data.")
                self.generated_tests = "No Python files found to generate tests for."
            else:
                aidm_console.print_primary(f"Found {len(py_files)} Python files from index")
                
                # Show file list
                file_list = "\n".join([f"- {f}" for f in py_files[:5]])
                if len(py_files) > 5:
                    file_list += f"\n- ... and {len(py_files) - 5} more files"
                aidm_console.print_markdown(f"**Files to analyze:**\n{file_list}")
                
                # Generate tests using indexed context
                with aidm_console.create_progress("Generating tests") as progress:
                    task = progress.add_task("Analyzing code...", total=100)
                    # Include project context from index for better test generation
                    project_summary = index_data.get("summary", {})
                    context_info = f"Project languages: {project_summary.get('languages', {})}\nFramework hints: {project_summary.get('framework_hints', [])}"
                    self.generated_tests = self.ollama.run_prompt(
                        f"{context_info}\n\nGenerate comprehensive unit tests for the following Python files:\n{py_files[:5]}"
                    )
                    progress.update(task, completed=100)
                
                aidm_console.print_success("Tests generated successfully!")
        except Exception as e:
            aidm_console.print_error(f"Test generation failed: {e}")
            self.generated_tests = f"Test generation failed: {e}"
        
        self.completed = True

    def summarize(self) -> str:
        """Return generated tests with beautiful formatting."""
        if self.generated_tests:
            aidm_console.print_separator()
            aidm_console.print_header("📋 Generated Tests", "AI-powered unit tests")
            aidm_console.print_markdown(self.generated_tests)
        return self.generated_tests
