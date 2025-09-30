# src/utils/console.py
"""
Beautiful terminal output using Rich library.
"""

from rich.console import Console
from rich.theme import Theme
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.status import Status
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich.columns import Columns
from rich import box
import sys
from typing import Optional, Any, Dict, List

# Custom theme for AI Dev Mate
AIDM_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "primary": "blue",
    "secondary": "magenta",
    "accent": "bright_blue",
    "muted": "dim white",
    "highlight": "bright_yellow",
    "code": "bright_white on black",
    "path": "bright_cyan",
    "number": "bright_green",
    "keyword": "bright_magenta",
    "string": "bright_green",
})

# Global console instance
console = Console(theme=AIDM_THEME, width=120)

class AIDMConsole:
    """Enhanced console with AI Dev Mate styling."""
    
    def __init__(self):
        self.console = console
        self.theme = AIDM_THEME
    
    def print_header(self, title: str, subtitle: Optional[str] = None):
        """Print a beautiful header."""
        header_text = Text(title, style="bold bright_blue")
        if subtitle:
            header_text.append(f"\n{subtitle}", style="muted")
        
        panel = Panel(
            Align.center(header_text),
            border_style="bright_blue",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def print_success(self, message: str, icon: str = "✓"):
        """Print success message."""
        self.console.print(f"[success]{icon}[/success] {message}")
    
    def print_error(self, message: str, icon: str = "✗"):
        """Print error message."""
        self.console.print(f"[error]{icon}[/error] {message}")
    
    def print_warning(self, message: str, icon: str = "⚠"):
        """Print warning message."""
        self.console.print(f"[warning]{icon}[/warning] {message}")
    
    def print_info(self, message: str, icon: str = "ℹ"):
        """Print info message."""
        self.console.print(f"[info]{icon}[/info] {message}")
    
    def print_primary(self, message: str, icon: str = "▶"):
        """Print primary message."""
        self.console.print(f"[primary]{icon}[/primary] {message}")
    
    def print_task_summary(self, task_name: str, status: str, details: Optional[str] = None):
        """Print task summary with beautiful formatting."""
        status_style = "success" if status.lower() == "completed" else "warning"
        status_icon = "✓" if status.lower() == "completed" else "⏳"
        
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_column("Property", style="primary", width=15)
        table.add_column("Value", style="default")
        
        table.add_row("Task", f"[accent]{task_name}[/accent]")
        table.add_row("Status", f"[{status_style}]{status_icon} {status}[/{status_style}]")
        if details:
            table.add_row("Details", details)
        
        self.console.print(table)
    
    def print_index_summary(self, index_data: Dict[str, Any]):
        """Print beautiful index summary."""
        summary = index_data.get("summary", {})
        files = index_data.get("files", [])
        
        # Create summary table
        table = Table(title="📁 Project Index Summary", box=box.ROUNDED)
        table.add_column("Metric", style="primary", width=20)
        table.add_column("Value", style="default")
        
        table.add_row("📂 Root Path", f"[path]{index_data.get('root', 'Unknown')}[/path]")
        table.add_row("📄 Total Files", f"[number]{summary.get('file_count', 0)}[/number]")
        table.add_row("📅 Indexed At", f"[muted]{index_data.get('indexed_at', 'Unknown')}[/muted]")
        
        # Language breakdown
        languages = summary.get("languages", {})
        if languages:
            top_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
            lang_text = ", ".join([f"[code]{lang}[/code] ([number]{count}[/number])" for lang, count in top_langs])
            table.add_row("🔤 Top Languages", lang_text)
        
        # Framework hints
        frameworks = summary.get("framework_hints", [])
        if frameworks:
            framework_text = ", ".join([f"[accent]{fw}[/accent]" for fw in frameworks])
            table.add_row("🏗️ Frameworks", framework_text)
        
        # Git info
        git_info = index_data.get("git", {})
        if git_info.get("current_branch"):
            table.add_row("🌿 Branch", f"[code]{git_info['current_branch']}[/code]")
        
        self.console.print(table)
    
    def print_file_list(self, files: List[Dict[str, Any]], max_files: int = 10):
        """Print a beautiful file list."""
        if not files:
            self.print_info("No files found")
            return
        
        table = Table(title="📄 Indexed Files", box=box.ROUNDED)
        table.add_column("Path", style="path", width=40)
        table.add_column("Language", style="code", width=12)
        table.add_column("Size", style="number", width=10)
        table.add_column("Hash", style="muted", width=12)
        
        for i, file_info in enumerate(files[:max_files]):
            path = file_info.get("path", "")
            language = file_info.get("language", "Unknown")
            size = file_info.get("size", 0)
            sha1 = file_info.get("sha1", "")[:8] + "..." if file_info.get("sha1") else ""
            
            # Format size
            size_str = self._format_size(size)
            
            table.add_row(path, language, size_str, sha1)
        
        if len(files) > max_files:
            table.add_row("...", f"[muted]and {len(files) - max_files} more files[/muted]", "", "")
        
        self.console.print(table)
    
    def print_dependencies(self, dependencies: Dict[str, Any]):
        """Print dependency information."""
        if not any(dependencies.values()):
            self.print_info("No dependencies found")
            return
        
        table = Table(title="📦 Dependencies", box=box.ROUNDED)
        table.add_column("Type", style="primary", width=15)
        table.add_column("Dependencies", style="default")
        
        # Python requirements
        if dependencies.get("requirements"):
            reqs = dependencies["requirements"]
            req_text = "\n".join([f"[code]{req}[/code]" for req in reqs[:5]])
            if len(reqs) > 5:
                req_text += f"\n[muted]... and {len(reqs) - 5} more[/muted]"
            table.add_row("🐍 Python", req_text)
        
        # PyProject dependencies
        pyproject_deps = dependencies.get("pyproject", {})
        if pyproject_deps:
            deps_text = "\n".join([f"[code]{name}[/code]: [muted]{version}[/muted]" 
                                 for name, version in list(pyproject_deps.items())[:5]])
            table.add_row("📋 PyProject", deps_text)
        
        # Package.json dependencies
        pkg_json = dependencies.get("package_json", {})
        if pkg_json.get("dependencies"):
            deps = pkg_json["dependencies"]
            deps_text = "\n".join([f"[code]{name}[/code]: [muted]{version}[/muted]" 
                                 for name, version in list(deps.items())[:5]])
            table.add_row("📦 NPM", deps_text)
        
        self.console.print(table)
    
    def print_git_info(self, git_data: Dict[str, Any]):
        """Print git information."""
        if not git_data:
            self.print_info("No git information available")
            return
        
        table = Table(title="🌿 Git Information", box=box.ROUNDED)
        table.add_column("Property", style="primary", width=15)
        table.add_column("Value", style="default")
        
        if git_data.get("current_branch"):
            table.add_row("Branch", f"[code]{git_data['current_branch']}[/code]")
        
        if git_data.get("remote_url"):
            table.add_row("Remote", f"[path]{git_data['remote_url']}[/path]")
        
        commits = git_data.get("recent_commits", [])
        if commits:
            table.add_row("Recent Commits", f"[number]{len(commits)}[/number] commits")
            for i, commit in enumerate(commits[:3]):
                commit_msg = commit.split(" ", 1)[1] if " " in commit else commit
                table.add_row("", f"[muted]{i+1}.[/muted] {commit_msg[:50]}...")
        
        self.console.print(table)
    
    def create_progress(self, description: str = "Processing") -> Progress:
        """Create a beautiful progress bar."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        )
    
    def print_code_syntax(self, code: str, language: str = "python"):
        """Print code with syntax highlighting."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)
    
    def print_markdown(self, markdown_text: str):
        """Print markdown content."""
        markdown = Markdown(markdown_text)
        self.console.print(markdown)
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """Show a confirmation prompt."""
        return Confirm.ask(f"[primary]{message}[/primary]", default=default)
    
    def prompt(self, message: str, default: str = "") -> str:
        """Show a text prompt."""
        return Prompt.ask(f"[primary]{message}[/primary]", default=default)
    
    def print_separator(self, char: str = "─", style: str = "muted"):
        """Print a separator line."""
        self.console.print(char * 80, style=style)
    
    def print_columns(self, items: List[str], title: Optional[str] = None):
        """Print items in columns."""
        if title:
            self.console.print(f"[primary]{title}[/primary]")
        
        columns = Columns(items, equal=True, expand=True)
        self.console.print(columns)
    
    def print_table(self, table):
        """Print a Rich table."""
        self.console.print(table)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def print_banner(self, text: str, style: str = "primary"):
        """Print a beautiful banner."""
        from rich.panel import Panel
        from rich.align import Align
        from rich import box
        
        banner_text = Text(text, style=style, justify="center")
        panel = Panel(
            Align.center(banner_text),
            border_style=style,
            box=box.DOUBLE,
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def print_info_box(self, title: str, content: str, style: str = "info"):
        """Print an information box."""
        from rich.panel import Panel
        from rich import box
        
        panel = Panel(
            content,
            title=f"[{style}]{title}[/{style}]",
            border_style=style,
            box=box.ROUNDED,
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def print_welcome(self):
        """Print welcome message."""
        self.print_banner("🤖 AI Dev Mate", "primary")
        self.print_info_box(
            "Welcome!",
            "Your intelligent development assistant is ready to help with:\n"
            "• 🔍 Code Review\n"
            "• 📝 Commit Generation\n" 
            "• 🧪 Test Generation\n"
            "• 📚 Documentation\n"
            "• 📁 Project Indexing",
            "info"
        )
    
    def print_help_menu(self):
        """Print help menu."""
        self.print_banner("📖 Help & Commands", "accent")
        
        commands = [
            ("--list", "List all available tasks"),
            ("--run <task>", "Run a specific task"),
            ("--index <path>", "Index a repository"),
            ("--check-index <path>", "Check index status"),
            ("--force-refresh", "Force refresh stale indexes"),
            ("--with-context", "Generate AI context (slow)"),
            ("--no-progress", "Disable progress bars"),
        ]
        
        table = Table(title="Available Commands", box=box.ROUNDED)
        table.add_column("Command", style="code", width=25)
        table.add_column("Description", style="default")
        
        for cmd, desc in commands:
            table.add_row(f"[accent]{cmd}[/accent]", desc)
        
        self.console.print(table)

# Global instance
aidm_console = AIDMConsole()