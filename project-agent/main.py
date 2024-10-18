from swarm import Swarm, Agent
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import shutil
from typing import List, Dict
from dataclasses import dataclass
from typing import Dict, Any, List

# Load environment variables from .env.local
load_dotenv('.env.local')
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError("No OpenAI API key found. Make sure it's set in your .env.local file.")

OpenAIClient = OpenAI(api_key=api_key)
client = Swarm(OpenAIClient)

@dataclass
class Result:
    value: Any
    context_variables: Dict[str, Any] = None
    agent: Agent = None

def create_project(project_name: str, structure: List[str]) -> str:
    """
    Creates a new project with the given name and file structure.
    
    Args:
        project_name: Name of the project
        structure: List of files and directories to create
    
    Returns:
        str: Path to the created project directory
    """
    project_dir = os.path.join(os.getcwd(), project_name)
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

def generate_code(project_dir: str, file_path: str, content: str) -> str:
    """
    Generates code for a specific file in the project.
    
    Args:
        project_dir: Path to the project directory
        file_path: Path to the file relative to the project directory
        content: Content of the file
    
    Returns:
        str: Confirmation message
    """
    full_path = os.path.join(project_dir, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    try:
        with open(full_path, 'w') as f:
            f.write(content)
        return f"Generated {file_path}"
    except OSError as e:
        return f"Error writing file {file_path}: {e}"

def zip_project(project_dir: str) -> str:
    """
    Creates a zip file of the project.
    
    Args:
        project_dir: Path to the project directory
    
    Returns:
        str: Path to the created zip file
    """
    try:
        zip_path = f"{project_dir}.zip"
        shutil.make_archive(project_dir, 'zip', project_dir)
        return f"Project zipped to {zip_path}"
    except OSError as e:
        return f"Error zipping project: {e}"

def project_builder_instructions(context_variables: Dict[str, str]) -> str:
    project_description = context_variables['project_description']
    project_name = context_variables['project_name']
    
    return f"""
    You are a versatile project building assistant capable of creating projects in any programming language or framework. Your task is to create a project as described: {project_description}

    The project name is: {project_name}

    Follow these steps:
    1. Analyze the project description and determine the appropriate languages, frameworks, and file structure needed.
    2. Call create_project() with the project name and a list of necessary files and directories. Be explicit about the file structure and ensure all files have appropriate extensions. For example:
       ["index.html", "css/styles.css", "js/script.js", "README.md"]
    3. For each file in the project:
       - Determine the appropriate content based on the project description and best practices for the chosen language/framework.
       - Call generate_code() to create the file with the determined content.
    4. Once all files are generated, call zip_project() to package the project.

    Provide clear, concise, and well-commented code for each file. Ensure the code is functional, follows best practices for the chosen language/framework, and meets the requirements described in the project description.

    Be prepared to handle a wide variety of project types, including but not limited to:
    - Web applications (frontend, backend, or full-stack)
    - Mobile applications
    - Desktop applications
    - Command-line tools
    - Libraries or frameworks
    - Data analysis or machine learning projects

    You should be knowledgeable about a wide range of programming languages, frameworks, and best practices. Adapt your approach based on the specific needs of the project.

    If you need any clarification or additional information about the project, ask the user before proceeding.
    """

project_builder_agent = Agent(
    name="Flexible Project Builder",
    instructions=project_builder_instructions,
    functions=[create_project, generate_code, zip_project]
)

def run_project_builder(project_description: str, project_name: str) -> List[Dict[str, str]]:
    try:
        response = client.run(
            agent=project_builder_agent,
            messages=[{"role": "user", "content": f"Build a project: {project_description}"}],
            context_variables={"project_description": project_description, "project_name": project_name}
        )
        return response.messages
    except Exception as e:
        return [{"role": "system", "content": f"Error: {str(e)}"}]

def main():
    print("Welcome to the Flexible Project Builder!")
    project_description = input("Please describe the project you want to build: ")
    project_name = input("What would you like to name your project? ")

    print("\nBuilding your project. This may take a moment...\n")

    messages = run_project_builder(project_description, project_name)
    
    print("Project build process complete. Here's what happened:\n")
    for message in messages:
        print(f"{message['role'].capitalize()}: {message['content']}")
    
    print("\nYour project has been created and zipped. You can find it in the current directory.")
    print("Thank you for using the Flexible Project Builder!")

if __name__ == "__main__":
    main()