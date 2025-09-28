import os
from datetime import datetime

from src.config.settings import Settings

def save_report(task_name: str, content: str):
    os.makedirs(Settings.REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{Settings.REPORTS_DIR}/{task_name}_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {task_name} Report\n")
        f.write(f"Generated at: {datetime.now()}\n\n")
        f.write(content)
    return filename
