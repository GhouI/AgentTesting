# File: openai_client.py
# Location: project_root/services/openai_client.py

from openai import OpenAI
from swarm import Swarm
from dotenv import load_dotenv
import os

# Get the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the .env.local file in the project root
env_path = os.path.join(current_dir, '..', 'config','.env.local')

print(env_path)

# Load environment variables from .env.local
load_dotenv(env_path)

# Get the API key from the environment variables
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    raise ValueError("No OpenAI API key found. Make sure it's set in your .env.local file.")

OpenAIClient = OpenAI(api_key=api_key)
client = Swarm(OpenAIClient)