"""Project management for Markdown documents."""
import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Project:
    """Represents a Markdown document project."""
    name: str
    title: str = ""
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    elements: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        return cls(**data)
    
    def add_element(self, elem_type: str, content: str, **kwargs) -> Dict[str, Any]:
        """Add an element to the document."""
        element = {
            "type": elem_type,
            "content": content,
            "id": f"elem_{len(self.elements)}",
            **kwargs
        }
        self.elements.append(element)
        self.modified_at = datetime.now().isoformat()
        return element
    
    def to_markdown(self) -> str:
        """Convert project to Markdown string."""
        lines = []
        
        if self.title:
            lines.append(f"# {self.title}")
            lines.append("")
        
        if self.author:
            lines.append(f"*Author: {self.author}*")
            lines.append("")
        
        for elem in self.elements:
            lines.extend(self._render_element(elem))
            lines.append("")
        
        return "\n".join(lines)
    
    def _render_element(self, elem: Dict[str, Any]) -> List[str]:
        """Render a single element to Markdown lines."""
        elem_type = elem.get("type", "paragraph")
        content = elem.get("content", "")
        
        if elem_type == "heading":
            level = elem.get("level", 1)
            return [f"{'#' * level} {content}"]
        
        elif elem_type == "paragraph":
            return [content]
        
        elif elem_type == "code":
            lang = elem.get("language", "")
            return [f"```{lang}", content, "```"]
        
        elif elem_type == "list":
            items = elem.get("items", [content] if content else [])
            ordered = elem.get("ordered", False)
            lines = []
            for i, item in enumerate(items, 1):
                prefix = f"{i}." if ordered else "-"
                lines.append(f"{prefix} {item}")
            return lines
        
        elif elem_type == "quote":
            return [f"> {line}" for line in content.split("\n")]
        
        elif elem_type == "horizontal_rule":
            return ["---"]
        
        elif elem_type == "table":
            headers = elem.get("headers", [])
            rows = elem.get("rows", [])
            lines = []
            if headers:
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for row in rows:
                lines.append("| " + " | ".join(row) + " |")
            return lines
        
        return [content]


def create_project(name: str, title: str = "", author: str = "") -> Project:
    """Create a new project."""
    return Project(name=name, title=title, author=author)


def save_project(project: Project, path: str) -> None:
    """Save project to JSON file with file locking."""
    data = project.to_dict()
    _locked_save_json(path, data, indent=2)


def load_project(path: str) -> Project:
    """Load project from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Project.from_dict(data)


def _locked_save_json(path: str, data: Any, **dump_kwargs) -> None:
    """Atomically write JSON with exclusive file locking."""
    try:
        f = open(path, "r+")
    except FileNotFoundError:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        f = open(path, "w")
    
    with f:
        _locked = False
        try:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            _locked = True
        except (ImportError, OSError):
            pass
        
        try:
            f.seek(0)
            f.truncate()
            json.dump(data, f, **dump_kwargs)
            f.flush()
        finally:
            if _locked:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
