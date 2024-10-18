# File: project_builder.py
# Location: project_root/services/project_builder.py

from swarm import Swarm, Agent
from models.result import Result
from utils.file_operations import create_project, generate_code, zip_project
from services.openai_client import client
from typing import List, Dict, Tuple, Optional

def project_builder_instructions(context_variables: Dict[str, str]) -> str:
    project_description = context_variables['project_description']
    project_name = context_variables['project_name']
    
    return f"""
    You are a versatile project building assistant capable of creating projects in any programming language or framework. Your task is to create a project as described: {project_description}

    The project name is: {project_name}

    Follow these steps:
    1. Analyze the project description and determine the appropriate languages, frameworks, and file structure needed.
    2. Call create_project() with the project name and a list of necessary files and directories.
    3. For each file in the project:
       - Determine the appropriate content based on the project description and best practices for the chosen language/framework.
       - Call generate_code() to create the file with the determined content.
    4. Once all files are generated, call zip_project() to package the project.

    Do not include the full code in your responses. Instead, provide a brief summary of what you're doing at each step.

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

def run_project_builder(project_description: str, project_name: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    try:
        response = client.run(
            agent=project_builder_agent,
            messages=[{"role": "user", "content": f"Build a project: {project_description}"}],
            context_variables={"project_description": project_description, "project_name": project_name}
        )
        
        formatted_messages = []
        zip_filename = None
        for message in response.messages:
            if message['role'] == 'function':
                if message['name'] == 'create_project':
                    formatted_messages.append({
                        'role': 'assistant',
                        'content': f"Creating project structure: {project_name}"
                    })
                elif message['name'] == 'generate_code':
                    file_path = message['content'].split(' ')[1]
                    formatted_messages.append({
                        'role': 'assistant',
                        'content': f"Generating: {file_path}"
                    })
                elif message['name'] == 'zip_project':
                    zip_filename = message['content']
                    if not zip_filename.startswith("Error"):
                        formatted_messages.append({
                            'role': 'assistant',
                            'content': f"Project has been zipped successfully. You can download it using this link: /download/{zip_filename}"
                        })
                    else:
                        formatted_messages.append({
                            'role': 'assistant',
                            'content': f"Error zipping project: {zip_filename}"
                        })
            elif message['role'] == 'assistant':
                formatted_messages.append(message)
        
        return formatted_messages, zip_filename
    except Exception as e:
        return [{"role": "system", "content": f"Error: {str(e)}"}], None