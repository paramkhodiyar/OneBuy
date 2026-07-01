from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    query: str
    user_profile: Dict[str, Any]
    selected_tools: List[str]
    results: List[Dict[str, Any]]
    recommendation: Dict[str, Any]
    reasoning: List[str]
    steps: List[Dict[str, Any]]
    brand_options: List[Dict[str, Any]]
    brand_strategy: Dict[str, Any]
    progress_callback: Any
