# src/utils/gitignore_utils.py
import os
from src.utils.console import aidm_console

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