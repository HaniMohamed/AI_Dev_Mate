# src/services/file_service.py
import os

class FileService:
    @staticmethod
    def list_python_files(path: str):
        files = []
        for root, _, filenames in os.walk(path):
            for f in filenames:
                if f.endswith(".py"):
                    files.append(os.path.join(root, f))
        return files

    @staticmethod
    def read_file(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
