from typing import List, Dict, Any

class ConversationMemory:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.recent_commands: Dict[str, List[str]] = {}
        self.recent_recommendations: Dict[str, List[str]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Return message list for a given session."""
        return self.sessions.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        """Append message to session history and enforce sliding window limit."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({"role": role, "content": content})
        
        # Enforce sliding window
        if len(self.sessions[session_id]) > self.max_history * 2:
            self.sessions[session_id] = self.sessions[session_id][-self.max_history * 2:]

    def add_command(self, session_id: str, command: str):
        if session_id not in self.recent_commands:
            self.recent_commands[session_id] = []
        self.recent_commands[session_id].append(command)
        if len(self.recent_commands[session_id]) > 5:
            self.recent_commands[session_id].pop(0)

    def get_recent_commands(self, session_id: str) -> List[str]:
        return self.recent_commands.get(session_id, [])

    def clear(self, session_id: str):
        """Clear memory for a given session."""
        if session_id in self.sessions:
            self.sessions[session_id] = []
        if session_id in self.recent_commands:
            self.recent_commands[session_id] = []
        if session_id in self.recent_recommendations:
            self.recent_recommendations[session_id] = []
