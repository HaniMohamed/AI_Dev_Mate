# src/core/utils.py
import os
from typing import Dict, Any, Optional
from src.services.repo_indexer import RepoIndexer
from src.services.ollama_service import OllamaService
from src.utils.console import aidm_console

# Utility functions
def chunk_text(text: str, size: int = 1000):
    """Split text into chunks of size."""
    for i in range(0, len(text), size):
        yield text[i:i+size]

def check_and_load_index(repo_path: str = None, ollama: OllamaService = None) -> Optional[Dict[str, Any]]:
    """
    Check if indexed data exists and load it. If not available, ask user to index first.
    
    Args:
        repo_path: Path to repository. If None, uses current working directory.
        ollama: OllamaService instance for index operations.
    
    Returns:
        Dict containing index data if available, None if not available or user should index first.
    """
    if repo_path is None:
        repo_path = os.getcwd()
    
    if ollama is None:
        ollama = OllamaService()
    
    idx = RepoIndexer(ollama=ollama)
    
    if not idx.index_exists(repo_path):
        aidm_console.print_error(
            "No index found for current directory. Please run indexing first: "
            "python -m src.main --index . [--with-context]"
        )
        return None
    
    # Check if index needs refresh
    if idx.needs_refresh(repo_path):
        index_age = idx.get_index_age(repo_path)
        age_str = "unknown" if index_age is None else f"{index_age.strftime('%Y-%m-%d %H:%M:%S')}"
        aidm_console.print_warning(
            f"Index is stale (created: {age_str}). Use --force-refresh to update it. "
            "Continuing with existing index..."
        )
    
    # Load and return the index
    index_data = idx.load_index(repo_path)
    if not index_data:
        aidm_console.print_error("Failed to load index data. Please re-index the project.")
        return None
    
    return index_data

def create_aggressive_review_prompt(diff: str, project_context: dict = None) -> str:
    """
    Create an aggressive code review prompt that focuses on finding bugs, anti-patterns, and improvements.
    
    Args:
        diff: The git diff to review
        project_context: Project metadata from index
    
    Returns:
        Formatted prompt for aggressive code review
    """
    context_info = ""
    if project_context:
        languages = project_context.get('summary', {}).get('languages', {})
        frameworks = project_context.get('summary', {}).get('framework_hints', [])
        context_info = f"""
PROJECT CONTEXT:
- Languages: {languages}
- Frameworks: {frameworks}
"""
    
    prompt = f"""You are an expert senior software engineer conducting an AGGRESSIVE code review. Your job is to find EVERYTHING wrong with this code and provide brutally honest feedback.

{context_info}

REVIEW GUIDELINES - BE EXTREMELY CRITICAL:
1. **SECURITY VULNERABILITIES**: Look for SQL injection, XSS, CSRF, authentication bypasses, data leaks, unsafe deserialization, path traversal, etc.
2. **PERFORMANCE ISSUES**: Memory leaks, inefficient algorithms, N+1 queries, missing indexes, excessive API calls, blocking operations
3. **BUGS & LOGIC ERRORS**: Off-by-one errors, null pointer exceptions, race conditions, unhandled edge cases, incorrect calculations
4. **CODE SMELLS**: Long methods, deep nesting, magic numbers, duplicate code, god objects, feature envy
5. **ANTI-PATTERNS**: Singleton abuse, tight coupling, violation of SOLID principles, improper error handling
6. **MAINTAINABILITY**: Poor naming, lack of documentation, complex conditionals, missing tests
7. **ARCHITECTURAL ISSUES**: Violation of separation of concerns, improper layering, circular dependencies

IMPORTANT: You MUST respond with valid JSON format only. Do not include any markdown formatting, explanations, or additional text.

REQUIRED JSON FORMAT:
{{
  "reviews": [
    {{
      "file": "exact file path from diff",
      "line": "line number if visible in diff, or null",
      "category": "CRITICAL BUG|SECURITY|PERFORMANCE|CODE QUALITY|MAINTAINABILITY",
      "issue": "clear description of the problem",
      "recommendation": "specific recommendation to resolve the issue"
    }}
  ]
}}

BE BRUTALLY HONEST - Don't sugarcoat anything. If the code is bad, say it's bad. If there are security holes, call them out aggressively. If performance will suffer, be direct about it.

DIFF TO REVIEW:
{diff}

Respond with JSON only:"""
    
    return prompt

def update_gitignore_for_aidm(repo_path: str) -> None:
    """Update .gitignore file to exclude .aidm and .aidm_index folders and their contents."""
    gitignore_path = os.path.join(repo_path, ".gitignore")
    
    # Define the patterns to add to .gitignore
    aidm_patterns = [
        "# AI Dev Mate generated files",
        ".aidm/",
        ".aidm/**",
        ".aidm/**/*",
        ".aidm_index/",
        ".aidm_index/**",
        ".aidm_index/**/*"
    ]
    
    try:
        # Read existing .gitignore content
        existing_content = ""
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # Check if .aidm patterns are already present
        needs_update = False
        for pattern in aidm_patterns[1:]:  # Skip the comment line
            if pattern not in existing_content:
                needs_update = True
                break
        
        if needs_update:
            # Add new patterns to .gitignore
            new_content = existing_content
            if new_content and not new_content.endswith('\n'):
                new_content += '\n'
            
            # Add a separator if there's existing content
            if new_content.strip():
                new_content += '\n'
            
            # Add the .aidm patterns
            new_content += '\n'.join(aidm_patterns) + '\n'
            
            # Write updated .gitignore
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            aidm_console.print_info(f"📝 Updated .gitignore to exclude .aidm and .aidm_index folders")
        else:
            aidm_console.print_info(f"✅ .gitignore already excludes .aidm and .aidm_index folders")
            
    except Exception as e:
        aidm_console.print_warning(f"Could not update .gitignore: {e}")
