from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
from swarm import Swarm, Agent
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import shutil
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

# Load environment variables from .env.local
load_dotenv('.env.local')
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError("No OpenAI API key found. Make sure it's set in your .env.local file.")

OpenAIClient = OpenAI(api_key=api_key)
client = Swarm(OpenAIClient)

# Create GeneratedContent directory if it doesn't exist
GENERATED_CONTENT_DIR = os.path.join(os.getcwd(), "GeneratedContent")
os.makedirs(GENERATED_CONTENT_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@dataclass
class Result:
    value: Any
    context_variables: Dict[str, Any] = None
    agent: Agent = None

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

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/api/build_project', methods=['POST', 'OPTIONS'])
def api_build_project():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    elif request.method == "POST":
        data = request.json
        project_description = data.get('project_description')
        project_name = data.get('project_name')
        
        if not project_description or not project_name:
            return jsonify({"error": "Missing project description or name"}), 400
        
        messages, zip_filename = run_project_builder(project_description, project_name)
        
        if zip_filename and not zip_filename.startswith("Error"):
            download_url = f"{request.url_root}download/{zip_filename}"
            return jsonify({
                "messages": messages,
                "downloadUrl": download_url
            })
        else:
            error_message = zip_filename if zip_filename else "Zip file not created"
            return jsonify({
                "messages": messages,
                "error": error_message
            })
    else:
        raise RuntimeError("Weird - don't know how to handle method {}".format(request.method))

@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    return send_file(os.path.join(GENERATED_CONTENT_DIR, filename), as_attachment=True)

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
    response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
    return response

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
