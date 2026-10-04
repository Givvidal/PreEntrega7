import operator
from typing import Annotated, Optional, List, Dict
from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """Hereda 'messages' (con su propio reducer add_messages) y suma campos propios."""
    next_agent: Optional[str]
    contribuciones: Annotated[List[Dict[str, str]], operator.add]
    pasos: int
    task_completed: bool
    requires_approval: bool