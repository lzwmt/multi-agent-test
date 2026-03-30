"""Session management with undo/redo support."""
from typing import List, Optional, Any, Callable
from dataclasses import dataclass
from copy import deepcopy


@dataclass
class Command:
    """Represents a command that can be executed and undone."""
    name: str
    execute: Callable[[], Any]
    undo: Callable[[], Any]
    description: str = ""


class Session:
    """Manages project state with undo/redo support."""
    
    def __init__(self, project: Any):
        self.project = project
        self._history: List[Command] = []
        self._history_index: int = -1
        self._max_history: int = 50
    
    def execute(self, command: Command) -> Any:
        """Execute a command and add it to history."""
        result = command.execute()
        
        # Remove any commands after current position (new branch)
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]
        
        # Add command to history
        self._history.append(command)
        self._history_index += 1
        
        # Trim history if too long
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
            self._history_index = self._max_history - 1
        
        return result
    
    def undo(self) -> bool:
        """Undo the last command. Returns True if successful."""
        if self._history_index < 0:
            return False
        
        command = self._history[self._history_index]
        command.undo()
        self._history_index -= 1
        return True
    
    def redo(self) -> bool:
        """Redo the next command. Returns True if successful."""
        if self._history_index >= len(self._history) - 1:
            return False
        
        self._history_index += 1
        command = self._history[self._history_index]
        command.execute()
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self._history_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self._history_index < len(self._history) - 1
    
    def get_history(self) -> List[dict]:
        """Get command history as list of dicts."""
        return [
            {
                "index": i,
                "name": cmd.name,
                "description": cmd.description,
                "active": i == self._history_index
            }
            for i, cmd in enumerate(self._history)
        ]
