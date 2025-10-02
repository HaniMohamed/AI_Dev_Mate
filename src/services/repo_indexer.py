# src/services/repo_indexer.py
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from fnmatch import fnmatch
from tqdm import tqdm

from src.services.file_service import FileService
from src.services.git_service import GitService
from src.services.ollama_service import OllamaService
from src.core.exceptions import IndexError, FileServiceError, GitServiceError
from src.utils.console import aidm_console
from src.utils.gitignore_utils import update_gitignore_for_aidm


IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    ".pytest_cache",
    "dist",
    "build",
}

LANG_BY_EXT = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".cxx": "C++",
    ".cc": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".hpp": "C++",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".scala": "Scala",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".md": "Markdown",
    ".dart": "Dart",
}


class RepoIndexer:
    """
    Scans a repository directory and produces an index JSON file with metadata:
    - files with language, size, and hash
    - language summary (counts)
    - simple dependency hints (requirements.txt, pyproject.toml, package.json)
    - basic git context (recent commits)
    Persisted under `<repo>/.aidm_index/index.json`.
    """

    def __init__(self, ollama: OllamaService | None = None):
        self.file_service = FileService()
        self.git_service = GitService()
        self.ollama = ollama
        # Mutable ignore config populated from .gitignore
        self.ignore_names: set[str] = set(IGNORED_DIRS)
        self.ignore_patterns: List[str] = []  # glob patterns relative to repo root

    def _load_gitignore(self, repo_path: str) -> None:
        """Load .gitignore rules into in-memory ignore sets.
        Notes:
        - Supports basic glob patterns via fnmatch.
        - Lines starting with '#' are comments.
        - Negation patterns ('!pat') are currently ignored for simplicity.
        - Trailing slashes indicate directories; we keep both name and pattern.
        """
        gi_path = os.path.join(repo_path, ".gitignore")
        if not os.path.isfile(gi_path):
            return
        try:
            with open(gi_path, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("!"):
                        # Negations not supported in this simple implementation
                        continue
                    # Normalize windows-style paths
                    line = line.replace("\\", "/")
                    if line.endswith("/"):
                        name = line.rstrip("/")
                        base = os.path.basename(name)
                        if base:
                            self.ignore_names.add(base)
                        self.ignore_patterns.append(name + "**")
                        continue
                    # If plain name without slash or glob, treat as name ignore too
                    if "/" not in line and not any(ch in line for ch in "*?[]"):
                        self.ignore_names.add(line)
                    self.ignore_patterns.append(line)
        except Exception:
            # Ignore parse errors silently to keep indexing robust
            return

    def _is_ignored(self, rel_path: str, is_dir: bool = False) -> bool:
        """Return True if rel_path should be ignored based on names or patterns.
        rel_path: path relative to repo root using os.sep separators.
        """
        # Name-based quick check for any segment
        parts = rel_path.split(os.sep)
        if any(p in self.ignore_names for p in parts):
            return True
        # Pattern-based check; convert to forward slashes for patterns
        rel_posix = rel_path.replace(os.sep, "/")
        for pat in self.ignore_patterns:
            # Support root-anchored patterns starting with '/'
            if pat.startswith('/'):
                if fnmatch('/' + rel_posix, pat):
                    return True
            if fnmatch(rel_posix, pat) or fnmatch(os.path.basename(rel_posix), pat):
                return True
        return False

    def _detect_language(self, filename: str) -> str:
        _, ext = os.path.splitext(filename)
        return LANG_BY_EXT.get(ext.lower(), "Unknown")

    def _file_hash(self, full_path: str) -> str:
        h = hashlib.sha1()
        try:
            with open(full_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return ""

    def _read_text(self, path: str) -> str:
        try:
            return self.file_service.read_file(path)
        except Exception:
            return ""

    def _generate_file_context(self, repo_root: str, rel_path: str, language: str, max_chars: int = 20000) -> str:
        """Use Ollama to generate a concise, structured context for a file.
        Returns plain text suitable to store under 'llm_context'.
        """
        if not self.ollama:
            return ""
        full = os.path.join(repo_root, rel_path)
        try:
            content = self._read_text(full)
        except Exception:
            content = ""
        if not content:
            return ""
        # Cap content size to avoid huge prompts: take head and tail slices
        if len(content) > max_chars:
            head = content[: max_chars // 2]
            tail = content[-max_chars // 2 :]
            content_snippet = head + "\n\n...\n\n" + tail
        else:
            content_snippet = content
        prompt = (
            "You are an expert software engineer generating context for code navigation and modification.\n"
            f"Language: {language}\n"
            f"Relative path: {rel_path}\n"
            "Provide a concise summary that helps another AI quickly locate where to implement changes.\n"
            "Include: purpose, key responsibilities, main classes/functions (with brief roles), important dependencies, and how it interacts with other parts of the project.\n"
            "Keep it under 180-220 words.\n\n"
            "File content (may be truncated):\n\n" + content_snippet
        )
        try:
            return self.ollama.run_prompt(prompt, max_tokens=600, temperature=0.1)
        except Exception:
            return ""

    def _parse_requirements(self, repo_path: str) -> List[str]:
        req_path = os.path.join(repo_path, "requirements.txt")
        if os.path.isfile(req_path):
            content = self._read_text(req_path)
            return [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
        return []

    def _parse_pyproject(self, repo_path: str) -> Dict[str, Any]:
        py_path = os.path.join(repo_path, "pyproject.toml")
        if not os.path.isfile(py_path):
            return {}
        # Minimal, heuristic parsing to avoid adding a TOML dependency
        data: Dict[str, Any] = {}
        current_section: List[str] = []
        for raw in self._read_text(py_path).splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                # section like [tool.poetry.dependencies]
                section_name = line[1:-1]
                current_section = section_name.split(".")
                d = data
                for part in current_section:
                    d = d.setdefault(part, {})
                continue
            if "=" in line and current_section:
                key, val = [p.strip() for p in line.split("=", 1)]
                # remove quotes if present
                if val.startswith(('"', "'")) and val.endswith(('"', "'")):
                    val = val[1:-1]
                d = data
                for part in current_section:
                    d = d.setdefault(part, {})
                d[key] = val
        return data

    def _parse_package_json(self, repo_path: str) -> Dict[str, Any]:
        pkg_path = os.path.join(repo_path, "package.json")
        if os.path.isfile(pkg_path):
            try:
                with open(pkg_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _parse_pubspec(self, repo_path: str) -> Dict[str, Any]:
        """Best-effort parse for Dart/Flutter pubspec.yaml without external deps.
        Returns a dict with minimal info: { 'has_flutter': bool }
        """
        for name in ("pubspec.yaml", "pubspec.yml"):
            pp = os.path.join(repo_path, name)
            if os.path.isfile(pp):
                try:
                    txt = self._read_text(pp)
                except Exception:
                    txt = ""
                txt_lower = txt.lower()
                has_flutter = False
                # Common signals of Flutter projects
                if "\nflutter:\n" in txt_lower or txt_lower.strip().startswith("flutter:"):
                    has_flutter = True
                if "sdk: flutter" in txt_lower:
                    has_flutter = True
                return {"has_flutter": has_flutter}
        return {}

    def _collect_files(self, repo_path: str, show_progress: bool = True) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        files: List[Dict[str, Any]] = []
        lang_counts: Dict[str, int] = {}
        
        # First pass: count total files for progress bar
        total_files = 0
        for root, dirs, filenames in os.walk(repo_path):
            rel_dir = os.path.relpath(root, repo_path)
            if rel_dir == ".":
                rel_dir = ""
            # Check directories against ignore patterns
            pruned = []
            for d in dirs:
                d_rel = os.path.join(rel_dir, d) if rel_dir else d
                if not self._is_ignored(d_rel, is_dir=True):
                    pruned.append(d)
            dirs[:] = pruned
            
            for fname in filenames:
                if fname == "index.json" and os.path.basename(root) == ".aidm_index":
                    continue
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, repo_path)
                if not self._is_ignored(rel, is_dir=False):
                    total_files += 1
        
        # Second pass: process files with progress bar
        if show_progress:
            with aidm_console.create_progress("Indexing files") as progress:
                task = progress.add_task("Processing files...", total=total_files)
                
                for root, dirs, filenames in os.walk(repo_path):
                    rel_dir = os.path.relpath(root, repo_path)
                    if rel_dir == ".":
                        rel_dir = ""
                    # mutate dirs in-place to prune ignored directories using .gitignore
                    pruned = []
                    for d in dirs:
                        d_rel = os.path.join(rel_dir, d) if rel_dir else d
                        if not self._is_ignored(d_rel, is_dir=True):
                            pruned.append(d)
                    dirs[:] = pruned
                    
                    for fname in filenames:
                        if fname == "index.json" and os.path.basename(root) == ".aidm_index":
                            continue
                        full = os.path.join(root, fname)
                        rel = os.path.relpath(full, repo_path)
                        # Skip ignored files
                        if self._is_ignored(rel, is_dir=False):
                            continue
                        
                        language = self._detect_language(fname)
                        try:
                            size = os.path.getsize(full)
                        except Exception:
                            size = 0
                        
                        files.append({
                            "path": rel,
                            "language": language,
                            "size": size,
                            "sha1": self._file_hash(full),
                        })
                        lang_counts[language] = lang_counts.get(language, 0) + 1
                        progress.update(task, advance=1)
        else:
            # Process without progress bar
            for root, dirs, filenames in os.walk(repo_path):
                rel_dir = os.path.relpath(root, repo_path)
                if rel_dir == ".":
                    rel_dir = ""
                # mutate dirs in-place to prune ignored directories using .gitignore
                pruned = []
                for d in dirs:
                    d_rel = os.path.join(rel_dir, d) if rel_dir else d
                    if not self._is_ignored(d_rel, is_dir=True):
                        pruned.append(d)
                dirs[:] = pruned
                
                for fname in filenames:
                    if fname == "index.json" and os.path.basename(root) == ".aidm_index":
                        continue
                    full = os.path.join(root, fname)
                    rel = os.path.relpath(full, repo_path)
                    # Skip ignored files
                    if self._is_ignored(rel, is_dir=False):
                        continue
                    
                    language = self._detect_language(fname)
                    try:
                        size = os.path.getsize(full)
                    except Exception:
                        size = 0
                    
                    files.append({
                        "path": rel,
                        "language": language,
                        "size": size,
                        "sha1": self._file_hash(full),
                    })
                    lang_counts[language] = lang_counts.get(language, 0) + 1
        return files, lang_counts

    def _framework_hints(self, repo_path: str) -> List[str]:
        hints: List[str] = []
        if os.path.isfile(os.path.join(repo_path, "manage.py")) or os.path.isdir(os.path.join(repo_path, "django")):
            hints.append("Django")
        if os.path.isfile(os.path.join(repo_path, "pyproject.toml")):
            pp = self._parse_pyproject(repo_path)
            if "tool" in pp and "poetry" in pp["tool"]:
                deps = pp["tool"]["poetry"].get("dependencies", {})
                for k in deps.keys() if isinstance(deps, dict) else []:
                    lk = k.lower()
                    if lk in ("fastapi", "flask", "django", "pydantic"):
                        hints.append(lk.capitalize())
        if os.path.isfile(os.path.join(repo_path, "package.json")):
            pkg = self._parse_package_json(repo_path)
            dep_sections = [pkg.get("dependencies", {}), pkg.get("devDependencies", {})]
            for sect in dep_sections:
                for k in sect.keys():
                    lk = k.lower()
                    if lk in ("react", "next", "vite", "vue", "svelte", "angular"):
                        hints.append(lk.capitalize())
        # Flutter via pubspec
        pubspec = self._parse_pubspec(repo_path)
        if pubspec.get("has_flutter"):
            hints.append("Flutter")
        # Heuristic: Flutter apps often have lib/main.dart
        if os.path.isfile(os.path.join(repo_path, "lib", "main.dart")):
            if "Flutter" not in hints:
                hints.append("Flutter")
        return sorted(list(set(hints)))

    def index(self, repo_path: str, generate_context: bool = False, show_progress: bool = True) -> Dict[str, Any]:
        repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(repo_path):
            raise ValueError(f"Path is not a directory: {repo_path}")

        # Load .gitignore rules for this repository
        self._load_gitignore(repo_path)

        files, lang_counts = self._collect_files(repo_path, show_progress)
        requirements = self._parse_requirements(repo_path)
        pyproject = self._parse_pyproject(repo_path)
        package_json = self._parse_package_json(repo_path)
        pubspec = self._parse_pubspec(repo_path)
        recent_commits = []
        try:
            recent_commits = self.git_service.get_recent_commits(5, repo_path)
        except GitServiceError:
            # In case the path is not a git repo or git is unavailable
            recent_commits = []

        # Optionally enrich with LLM-generated context per file (can be slow)
        if generate_context and self.ollama:
            context_files = [f for f in files if f.get("language") not in ["Unknown", "Binary"]]
            if context_files:
                aidm_console.print_info(f"Generating AI context for {len(context_files)} files...")
                with aidm_console.create_progress("Generating AI context") as progress:
                    task = progress.add_task("Processing files...", total=len(context_files))
                    for f in context_files:
                        ctx = self._generate_file_context(repo_path, f["path"], f.get("language", "Unknown"))
                        if ctx:
                            f["llm_context"] = ctx
                        progress.update(task, advance=1)

        index: Dict[str, Any] = {
            "index_version": "1.0",
            "indexed_at": datetime.utcnow().isoformat() + "Z",
            "root": repo_path,
            "summary": {
                "file_count": len(files),
                "languages": lang_counts,
                "framework_hints": self._framework_hints(repo_path),
            },
            "files": files,
            "dependencies": {
                "requirements": requirements,
                "pyproject": pyproject.get("tool", {}).get("poetry", {}).get("dependencies", {}),
                "package_json": {
                    "dependencies": package_json.get("dependencies", {}),
                    "devDependencies": package_json.get("devDependencies", {}),
                },
                "pubspec": pubspec,
            },
            "git": {
                "recent_commits": recent_commits,
                "current_branch": self.git_service.get_current_branch(repo_path) if self.git_service.is_git_repo(repo_path) else "",
                "remote_url": self.git_service.get_remote_url(repo_path) if self.git_service.is_git_repo(repo_path) else "",
            },
        }

        # Update .gitignore to exclude .aidm and .aidm_index folders
        update_gitignore_for_aidm(repo_path)
        
        # Persist under .aidm_index/index.json inside the repo
        index_dir = os.path.join(repo_path, ".aidm_index")
        os.makedirs(index_dir, exist_ok=True)
        out_path = os.path.join(index_dir, "index.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        return index

    def summarize(self, index: Dict[str, Any]) -> str:
        """Generate a beautiful summary of the index."""
        s = index.get("summary", {})
        langs = s.get("languages", {})
        top_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:5]
        hints = s.get("framework_hints", [])
        
        # Use Rich console for beautiful output
        aidm_console.print_index_summary(index)
        
        # Return simple text version for compatibility
        lines = [
            f"Indexed root: {index.get('root')}",
            f"Files: {s.get('file_count', 0)}",
            "Top languages: " + ", ".join([f"{k}({v})" for k, v in top_langs]) if top_langs else "Top languages: -",
            "Framework hints: " + (", ".join(hints) if hints else "-"),
        ]
        return "\n".join(lines)

    # --------------------------
    # Index file helpers
    # --------------------------
    def _index_file_path(self, repo_path: str) -> str:
        root = os.path.abspath(repo_path)
        return os.path.join(root, ".aidm_index", "index.json")

    def index_exists(self, repo_path: str) -> bool:
        """Return True if an index file exists under <repo>/.aidm_index/index.json."""
        return os.path.isfile(self._index_file_path(repo_path))

    def load_index(self, repo_path: str) -> Dict[str, Any]:
        """Load and return the index JSON if present; otherwise return an empty dict."""
        path = self._index_file_path(repo_path)
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    
    def is_index_valid(self, repo_path: str) -> bool:
        """Check if the existing index is still valid (not stale)."""
        index = self.load_index(repo_path)
        if not index:
            return False
        
        # Check if index format version is compatible
        index_version = index.get("index_version", "1.0")
        if index_version != "1.0":
            return False
        
        # Check if any files have been modified since indexing
        indexed_at_str = index.get("indexed_at", "")
        if not indexed_at_str:
            return False
        
        try:
            indexed_at = datetime.fromisoformat(indexed_at_str.replace("Z", "+00:00"))
        except ValueError:
            return False
        
        # Check if any tracked files have been modified since indexing
        files = index.get("files", [])
        for file_info in files:
            file_path = os.path.join(repo_path, file_info["path"])
            if os.path.exists(file_path):
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    # Make file_mtime timezone-aware for comparison
                    if file_mtime.tzinfo is None:
                        file_mtime = file_mtime.replace(tzinfo=indexed_at.tzinfo)
                    if file_mtime > indexed_at:
                        return False
                except OSError:
                    continue
            else:
                # File no longer exists
                return False
        
        return True
    
    def needs_refresh(self, repo_path: str) -> bool:
        """Check if the index needs to be refreshed."""
        return not self.is_index_valid(repo_path)
    
    def get_index_age(self, repo_path: str) -> Optional[datetime]:
        """Get the age of the current index."""
        index = self.load_index(repo_path)
        if not index:
            return None
        
        indexed_at_str = index.get("indexed_at", "")
        if not indexed_at_str:
            return None
        
        try:
            return datetime.fromisoformat(indexed_at_str.replace("Z", "+00:00"))
        except ValueError:
            return None
    
    def force_refresh_index(self, repo_path: str, generate_context: bool = False, show_progress: bool = True) -> Dict[str, Any]:
        """Force refresh the index regardless of validity."""
        return self.index(repo_path, generate_context, show_progress)
