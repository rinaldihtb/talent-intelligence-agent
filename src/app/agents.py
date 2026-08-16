from langchain.agents import create_agent

from src.app.config import CHAT_MODEL, SEARCH_AGENT_PROMPT, ANALYSIS_AGENT_PROMPT, COMPARISON_AGENT_PROMPT
from src.app.tools import search_candidates,extract_candidate_profile, extract_candidate_profiles

#Candidate Search Agent
search_agent = create_agent(
    model=CHAT_MODEL,
    tools=[search_candidates],
    system_prompt=SEARCH_AGENT_PROMPT,
    name="search_agent"
)

#Candidate Analysis Agent
analysis_agent = create_agent(
    model=CHAT_MODEL,
    tools=[extract_candidate_profile],
    system_prompt=ANALYSIS_AGENT_PROMPT,
    name="analysis_agent"
)

#Candidate Comparison Agent
comparison_agent = create_agent(
    model=CHAT_MODEL,
    tools=[extract_candidate_profiles],
    system_prompt=COMPARISON_AGENT_PROMPT,
    name="comparison_agent"
)
