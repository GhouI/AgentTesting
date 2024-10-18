# File: file_operations.py
# Location: project_root/utils/file_operations.py

import os
import shutil
from typing import List

GENERATED_CONTENT_DIR = os.path.join(os.getcwd(), "GeneratedContent")
os.makedirs(GENERATED_CONTENT_DIR, exist_ok=True)

def create_project(project_name: str, structure: List[str]) -> str:
    project_dir = os.path.join(GENERATED_CONTENT_DIR, project_name)
    try:
        os.makedirs(project_dir, exist_ok=True)
        for item in structure:
            path = os.path.join(project_dir, item)
            if item.endswith('/'):
                os.makedirs(path, exist_ok=True)
            elif '.' in item:  # Only create files with extensions
                os.makedirs(os.path.dirname(path), exist_ok=True)
                open(path, 'a').close()
        return f"Created project at '{project_dir}'"
    except OSError as e:
        return f"Error creating project: {e}"

def generate_code(project_name: str, file_path: str, content: str) -> str:
    project_dir = os.path.join(GENERATED_CONTENT_DIR, project_name)
    full_path = os.path.join(project_dir, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    try:
        with open(full_path, 'w') as f:
            f.write(content)
        return f"Generated {file_path}"
    except OSError as e:
        return f"Error writing file {file_path}: {e}"

def zip_project(project_name: str) -> str:
    project_dir = os.path.join(GENERATED_CONTENT_DIR, project_name)
    try:
        zip_path = os.path.join(GENERATED_CONTENT_DIR, f"{project_name}.zip")
        shutil.make_archive(os.path.join(GENERATED_CONTENT_DIR, project_name), 'zip', project_dir)
        return f"{project_name}.zip"
    except Exception as e:
        return f"Error zipping project: {str(e)}"