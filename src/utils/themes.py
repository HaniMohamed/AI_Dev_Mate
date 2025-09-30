# src/utils/themes.py
"""
Additional themes and styling utilities for AI Dev Mate.
"""

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box
from typing import Dict, Any

# Additional themes for different contexts
DARK_THEME = Theme({
    "info": "bright_cyan",
    "warning": "bright_yellow", 
    "error": "bright_red",
    "success": "bright_green",
    "primary": "bright_blue",
    "secondary": "bright_magenta",
    "accent": "bright_white",
    "muted": "dim white",
    "highlight": "bright_yellow",
    "code": "bright_white on black",
    "path": "bright_cyan",
    "number": "bright_green",
    "keyword": "bright_magenta",
    "string": "bright_green",
})

LIGHT_THEME = Theme({
    "info": "blue",
    "warning": "yellow",
    "error": "red", 
    "success": "green",
    "primary": "blue",
    "secondary": "magenta",
    "accent": "black",
    "muted": "dim black",
    "highlight": "yellow",
    "code": "black on white",
    "path": "blue",
    "number": "green",
    "keyword": "magenta",
    "string": "green",
})

MONOCHROME_THEME = Theme({
    "info": "white",
    "warning": "white",
    "error": "white",
    "success": "white", 
    "primary": "white",
    "secondary": "white",
    "accent": "white",
    "muted": "dim white",
    "highlight": "white",
    "code": "white",
    "path": "white",
    "number": "white",
    "keyword": "white",
    "string": "white",
})

class ThemeManager:
    """Manage different themes for AI Dev Mate."""
    
    def __init__(self):
        self.themes = {
            "default": Theme({
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
            }),
            "dark": DARK_THEME,
            "light": LIGHT_THEME,
            "monochrome": MONOCHROME_THEME,
        }
        self.current_theme = "default"
    
    def get_theme(self, theme_name: str = None) -> Theme:
        """Get a theme by name."""
        if theme_name is None:
            theme_name = self.current_theme
        return self.themes.get(theme_name, self.themes["default"])
    
    def set_theme(self, theme_name: str):
        """Set the current theme."""
        if theme_name in self.themes:
            self.current_theme = theme_name
        else:
            raise ValueError(f"Unknown theme: {theme_name}")
    
    def list_themes(self) -> list:
        """List available themes."""
        return list(self.themes.keys())

def create_banner(text: str, style: str = "primary") -> Panel:
    """Create a beautiful banner."""
    banner_text = Text(text, style=style, justify="center")
    return Panel(
        Align.center(banner_text),
        border_style=style,
        box=box.DOUBLE,
        padding=(1, 2)
    )

def create_info_box(title: str, content: str, style: str = "info") -> Panel:
    """Create an information box."""
    return Panel(
        content,
        title=f"[{style}]{title}[/{style}]",
        border_style=style,
        box=box.ROUNDED,
        padding=(1, 2)
    )

def create_warning_box(title: str, content: str) -> Panel:
    """Create a warning box."""
    return create_info_box(title, content, "warning")

def create_error_box(title: str, content: str) -> Panel:
    """Create an error box."""
    return create_info_box(title, content, "error")

def create_success_box(title: str, content: str) -> Panel:
    """Create a success box."""
    return create_info_box(title, content, "success")

# Global theme manager instance
theme_manager = ThemeManager()