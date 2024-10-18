import os
import json
import logging
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv
from swarm import Swarm, Agent
from openai import OpenAI

# Load environment variables from .env.local
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a file handler for conversation logging
conversation_logger = logging.getLogger("conversation")
conversation_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("conversation_log.txt")
file_handler.setFormatter(logging.Formatter('%(message)s'))
conversation_logger.addHandler(file_handler)

# Get the API key from environment variables
api_key = os.getenv('key')

if not api_key:
    raise ValueError("No OpenAI API key found. Make sure it's set in your .env.local file.")

OpenAIClient = OpenAI(api_key=api_key)
client = Swarm(OpenAIClient)
@dataclass
class CharacterProfile:
    name: str
    age: int
    occupation: str
    personality: List[str]
    relationships: Dict[str, Any]

@dataclass
class StoryEvent:
    section: int
    title: str
    details: List[str]

@dataclass
class StoryContext:
    title: str
    characters: Dict[str, CharacterProfile]
    events: List[StoryEvent]
    current_event_index: int = 0



def load_json_file(filename: str) -> Dict:
    with open(filename, 'r') as file:
        return json.load(file)

def load_character_profiles(filename: str) -> Dict[str, CharacterProfile]:
    data = load_json_file(filename)
    characters = {}
    for char_data in data['characters']:
        characters[char_data['name']] = CharacterProfile(
            name=char_data['name'],
            age=char_data['age'],
            occupation=char_data['occupation'],
            personality=char_data['personality'],
            relationships=char_data['relationships']
        )
    return characters

def load_story_events(filename: str) -> List[StoryEvent]:
    data = load_json_file(filename)
    events = []
    for section in data['summary']:
        events.append(StoryEvent(
            section=section['section'],
            title=section['title'],
            details=section['details']
        ))
    return events

def update_story_state(context_variables: Dict[str, Any], new_state: str) -> Result:
    context_variables["story_context"].current_event_index += 1
    return Result(value="Story state updated", context_variables=context_variables)

def create_character_agent(character: CharacterProfile) -> Agent:
    return Agent(
        name=character.name,
        instructions=f"""
        You are {character.name}, age {character.age}, occupation: {character.occupation}.
        Personality traits: {', '.join(character.personality)}
        Relationships:
        {json.dumps(character.relationships, indent=2)}

        Your goal is to interact with other characters and make decisions that progress the story.
        Always stay in character and make decisions based on your personality, relationships, and the current story context.
        Use the update_story_state function to move the story forward when you've taken a significant action or made an important decision.
        """,
        functions=[update_story_state]
    )

def run_story(story_context: StoryContext):
    context_variables = {"story_context": story_context}
    agents = [create_character_agent(char) for char in story_context.characters.values()]
    current_agent_index = 0

    conversation_logger.info(f"Story Title: {story_context.title}")
    for char in story_context.characters.values():
        conversation_logger.info(f"\nCharacter Profile - {char.name}:")
        conversation_logger.info(f"  Age: {char.age}")
        conversation_logger.info(f"  Occupation: {char.occupation}")
        conversation_logger.info(f"  Personality: {', '.join(char.personality)}")
        conversation_logger.info(f"  Relationships: {json.dumps(char.relationships, indent=2)}")

    # Agents learn from past events
    learning_context = "Characters are aware of the following events:\n"
    for event in story_context.events:
        learning_context += f"- {event.title}: {' '.join(event.details)}\n"

    # Pass the learning context to agents
    for agent in agents:
        agent.instructions += f"\nAs a character, you have learned:\n{learning_context}"

    # Proceed with the story
    while story_context.current_event_index < len(story_context.events):
        current_event = story_context.events[story_context.current_event_index]
        current_agent = agents[current_agent_index]

        event_context = f"""
        Current event: {current_event.title}
        Details:
        {chr(10).join(['- ' + detail for detail in current_event.details])}
        """
        print(f"\n{event_context}")
        conversation_logger.info(event_context)

        # Rate limiter: retry logic for API requests
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                response = client.run(
                    agent=current_agent,
                    messages=[{"role": "system", "content": event_context}],
                    context_variables=context_variables
                )
                
                agent_message = f"{current_agent.name}: {response.messages[-1]['content']}"
                print(f"\n{agent_message}")
                conversation_logger.info(agent_message)

                context_variables = response.context_variables

                # Move to the next event
                if current_agent_index == len(agents) - 1:
                    # Only update event index after all agents have acted on the event
                    story_context.current_event_index += 1
                current_agent_index = (current_agent_index + 1) % len(agents)

                break  # Break out of retry loop if successful

            except Exception as e:
                if "429" in str(e):  # Check for rate limit error
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limit reached. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)  # Wait before retrying
                else:
                    error_message = f"An error occurred: {e}"
                    logger.error(error_message)
                    print("An error occurred in the story simulation. Ending the story.")
                    conversation_logger.error(error_message)
                    return  # Exit the story on other errors

    print("\nStory simulation complete.")
    conversation_logger.info("Story simulation complete.")

if __name__ == "__main__":
    print("Welcome to the Story Agent System!")
    
    characters = load_character_profiles("character_profiles.json")
    events = load_story_events("story_events.json")
    
    story_context = StoryContext(
        title="Rent-A-Girlfriend",
        characters=characters,
        events=events
    )
    
    print("\nStarting the story simulation...")
    run_story(story_context)
    print("\nStory simulation complete. Check 'conversation_log.txt' for the full conversation log.")
