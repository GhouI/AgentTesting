import os
import json
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from swarm import Swarm, Agent
from openai import OpenAI
import random

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
class Result:
    value: Optional[str] = None
    agent: Optional[Agent] = None
    context_variables: Optional[Dict[str, Any]] = None

@dataclass
class CharacterProfile:
    name: str
    age: int
    occupation: str
    personality: List[str]
    relationships: Dict[str, Any]
    decision_making_tendencies: List[str]

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
    summary: str = ""
    decisions: Dict[str, str] = None  # Added to store decisions for coherence check

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
            relationships=char_data['relationships'],
            decision_making_tendencies=char_data.get('decision_making_tendencies', [])
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

def generate_story_summary(story_context: StoryContext) -> str:
    summary = f"Story Title: {story_context.title}\n\n"
    summary += "Characters:\n"
    for character in story_context.characters.values():
        summary += f"- {character.name}: {character.occupation}, {', '.join(character.personality)}\n"
    summary += "\nMajor Events:\n"
    for event in story_context.events:
        summary += f"- {event.title}\n"
    return summary

def agent_learning_phase(agent: Agent, story_summary: str) -> None:
    response = agent.send_message(f"Learn the following story summary:\n{story_summary}")
    print(f"{agent.name} has learned the story summary. Response: {response}")

def create_character_agent(character: CharacterProfile, story_context: StoryContext) -> Agent:
    other_characters = {name: char for name, char in story_context.characters.items() if name != character.name}
    
    instructions = f"""
    You are {character.name}, age {character.age}, occupation: {character.occupation}.
    Personality traits: {', '.join(character.personality)}
    Decision-making tendencies: {', '.join(character.decision_making_tendencies)}
    
    Your relationships:
    {json.dumps(character.relationships, indent=2)}
    
    Other characters in the story:
    {json.dumps({name: {"age": char.age, "occupation": char.occupation} for name, char in other_characters.items()}, indent=2)}
    
    Story context:
    Title: {story_context.title}
    
    Your goal is to interact with other characters and make decisions that progress the story.
    Always stay in character and make decisions based on your personality, relationships, and the current story context.
    Use the update_story_state function to add new events to the story when you've taken a significant action or made an important decision.
    """
    
    return Agent(
        name=character.name,
        instructions=instructions,
        functions=[update_story_state]
    )

def create_narrator_agent(story_context: StoryContext) -> Agent:
    instructions = f"""
    You are the narrator for the story "{story_context.title}".
    Your role is to provide an overview of the story's progress, summarize events, and offer insights into character development and plot progression.
    Use the information about characters and events to create engaging narrative summaries.
    """
    
    return Agent(
        name="Narrator",
        instructions=instructions,
        functions=[update_story_state]
    )

def update_story_state(context_variables: Dict[str, Any], new_event: str) -> Result:
    context_variables["story_context"].events.append(StoryEvent(
        section=len(context_variables["story_context"].events) + 1,
        title="New Event",
        details=[new_event]
    ))
    context_variables["story_context"].current_event_index += 1
    return Result(value="Story state updated", context_variables=context_variables)

def agent_decision_making(agent: Agent, story_context: StoryContext) -> str:
    current_event = story_context.events[story_context.current_event_index]
    options = generate_story_options(story_context, agent.name)
    
    prompt = f"""
    Current event: {current_event.title}
    Details: {', '.join(current_event.details)}
    
    What would you like to do? Choose from the following options or suggest your own:
    {options}
    """
    
    response = client.run(
        agent=agent,
        messages=[{"role": "system", "content": prompt}],
        context_variables={"story_context": story_context}
    )
    
    return response.messages[-1]['content']

def generate_story_options(story_context: StoryContext, character_name: str) -> str:
    current_event = story_context.events[story_context.current_event_index]
    character = story_context.characters[character_name]
    
    general_options = [
        "Talk to another character",
        "Take an action related to the current event",
        "Reflect on the situation"
    ]
    
    specific_options = []
    if "rental girlfriend" in character.occupation.lower():
        specific_options.append("Go on a rental date")
    if "student" in character.occupation.lower():
        specific_options.append("Attend a class or study")
    if any("shy" in trait.lower() for trait in character.personality):
        specific_options.append("Try to overcome shyness in a social situation")
    
    all_options = general_options + specific_options
    return "\n".join(f"{i+1}. {option}" for i, option in enumerate(all_options))

def communicate_decision(agent: Agent, decision: str, story_context: StoryContext) -> str:
    prompt = f"Describe how you carry out this decision: {decision}"
    response = client.run(
        agent=agent,
        messages=[{"role": "system", "content": prompt}],
        context_variables={"story_context": story_context}
    )
    return response.messages[-1]['content']

def check_decision_coherence(decision: str, story_context: StoryContext) -> bool:
    current_event = story_context.events[story_context.current_event_index]
    
    # Check if the decision is related to the current event
    if any(detail.lower() in decision.lower() for detail in current_event.details):
        return True
    
    # Check if the decision aligns with the character's personality and tendencies
    character_name = next(name for name, agent in story_context.characters.items() if decision.startswith(name))
    character = story_context.characters[character_name]
    
    if any(trait.lower() in decision.lower() for trait in character.personality + character.decision_making_tendencies):
        return True
    
    # If none of the above conditions are met, the decision might not be coherent
    return False

def resolve_conflicts(decisions: Dict[str, str], story_context: StoryContext) -> Dict[str, str]:
    resolved_decisions = decisions.copy()
    
    # Check for conflicting decisions
    for char1, decision1 in decisions.items():
        for char2, decision2 in decisions.items():
            if char1 != char2 and are_decisions_conflicting(decision1, decision2):
                # Resolve conflict based on character relationships and personalities
                winner = resolve_conflict(char1, char2, story_context)
                loser = char2 if winner == char1 else char1
                
                # Modify the losing character's decision
                resolved_decisions[loser] = generate_alternative_decision(loser, story_context)
    
    return resolved_decisions

def are_decisions_conflicting(decision1: str, decision2: str) -> bool:
    conflicting_keywords = ["argue", "fight", "disagree", "oppose"]
    return any(keyword in decision1.lower() and keyword in decision2.lower() for keyword in conflicting_keywords)

def resolve_conflict(char1: str, char2: str, story_context: StoryContext) -> str:
    char1_profile = story_context.characters[char1]
    char2_profile = story_context.characters[char2]
    
    # Calculate a 'strength' score based on personality traits and relationships
    char1_score = sum(len(trait) for trait in char1_profile.personality) + char1_profile.relationships.get(char2, 0)
    char2_score = sum(len(trait) for trait in char2_profile.personality) + char2_profile.relationships.get(char1, 0)
    
    return char1 if char1_score > char2_score else char2

def generate_alternative_decision(character: str, story_context: StoryContext) -> str:
    options = generate_story_options(story_context, character).split("\n")
    return f"{character} decides to " + random.choice(options).split(". ")[1]

def story_coherence_check(story_context: StoryContext) -> bool:
    current_event = story_context.events[story_context.current_event_index]
    previous_event = story_context.events[story_context.current_event_index - 1] if story_context.current_event_index > 0 else None
    
    # Check if current event logically follows from the previous event
    if previous_event:
        if not any(detail.lower() in current_event.title.lower() for detail in previous_event.details):
            return False
    
    # Check if all characters have made decisions relevant to the current event
    for character in story_context.characters.values():
        if not any(character.name in decision for decision in story_context.decisions.values()):
            return False
    
    return True

def character_relationship_update(story_context: StoryContext, event: str) -> None:
    for character_name, decision in story_context.decisions.items():
        character = story_context.characters[character_name]
        
        for other_character in story_context.characters.values():
            if other_character.name != character_name:
                # Update relationship based on decision
                if other_character.name in decision:
                    if any(positive_word in decision.lower() for positive_word in ["help", "support", "agree"]):
                        character.relationships[other_character.name] = min(10, character.relationships.get(other_character.name, 0) + 1)
                    elif any(negative_word in decision.lower() for negative_word in ["argue", "disagree", "oppose"]):
                        character.relationships[other_character.name] = max(-10, character.relationships.get(other_character.name, 0) - 1)

def format_story_output(story_context: StoryContext, decisions: Dict[str, str]) -> str:
    output = f"Current Event: {story_context.events[story_context.current_event_index].title}\n\n"
    for character, decision in decisions.items():
        output += f"{character}: {decision}\n\n"
    return output

def save_story_state(story_context: StoryContext, filename: str) -> None:
    with open(filename, 'w') as f:
        json.dump({
            'title': story_context.title,
            'current_event_index': story_context.current_event_index,
            'summary': story_context.summary,
            'characters': {name: vars(profile) for name, profile in story_context.characters.items()},
            'events': [vars(event) for event in story_context.events]
        }, f)

def run_story(story_context: StoryContext):
    story_context.summary = generate_story_summary(story_context)
    character_agents = [create_character_agent(char, story_context) for char in story_context.characters.values()]
    narrator_agent = create_narrator_agent(story_context)
    agents = character_agents + [narrator_agent]
    
    conversation_logger.info(f"Story Title: {story_context.title}")
    for char in story_context.characters.values():
        conversation_logger.info(f"\nCharacter Profile - {char.name}:")
        conversation_logger.info(f"  Age: {char.age}")
        conversation_logger.info(f"  Occupation: {char.occupation}")
        conversation_logger.info(f"  Personality: {', '.join(char.personality)}")
        conversation_logger.info(f"  Relationships: {json.dumps(char.relationships, indent=2)}")
    
    # Learning phase
    for agent in agents:
        agent_learning_phase(agent, story_context.summary)
    
    # Story progression
    turn_count = 0
    max_turns = 30  # Adjust as needed
    
    while turn_count < max_turns and story_context.current_event_index < len(story_context.events):
        decisions = {}
        for agent in agents:
            decision = agent_decision_making(agent, story_context)
            if check_decision_coherence(decision, story_context):
                decisions[agent.name] = communicate_decision(agent, decision, story_context)
            else:
                print(f"Decision by {agent.name} was not coherent. Generating a new decision.")
                decisions[agent.name] = generate_alternative_decision(agent.name, story_context)
        
        decisions = resolve_conflicts(decisions, story_context)
        
        story_context.decisions = decisions
        if story_coherence_check(story_context):
            print(format_story_output(story_context, decisions))
            character_relationship_update(story_context, str(decisions))
            update_story_state({"story_context": story_context}, "")
        else:
            print("Story coherence check failed. Regenerating decisions.")
            continue
        
        save_story_state(story_context, 'story_state.json')
def main():
    characters = load_character_profiles('character_profiles.json')
    events = load_story_events('story_events.json')
    story_context = StoryContext("Rent-A-Girlfriend", characters, events)
    run_story(story_context)

if __name__ == "__main__":
    main()      