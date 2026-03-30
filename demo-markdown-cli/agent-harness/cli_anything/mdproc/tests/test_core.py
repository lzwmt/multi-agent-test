"""Unit tests for core modules."""
import pytest
import json
import os
import tempfile
from ..core.project import Project, create_project, save_project, load_project
from ..core.session import Session, Command


class TestProject:
    """Test Project class."""
    
    def test_create_project(self):
        """Test basic project creation."""
        proj = create_project(name="test", title="Test Doc", author="Author")
        assert proj.name == "test"
        assert proj.title == "Test Doc"
        assert proj.author == "Author"
        assert len(proj.elements) == 0
    
    def test_project_to_dict(self):
        """Test project serialization."""
        proj = create_project(name="test")
        data = proj.to_dict()
        assert data["name"] == "test"
        assert "created_at" in data
        assert "modified_at" in data
    
    def test_project_from_dict(self):
        """Test project deserialization."""
        data = {
            "name": "restored",
            "title": "Restored Doc",
            "author": "",
            "created_at": "2024-01-01T00:00:00",
            "modified_at": "2024-01-01T00:00:00",
            "elements": [],
            "metadata": {}
        }
        proj = Project.from_dict(data)
        assert proj.name == "restored"
        assert proj.title == "Restored Doc"
    
    def test_add_heading(self):
        """Test adding heading element."""
        proj = create_project(name="test")
        elem = proj.add_element("heading", "Title", level=1)
        assert len(proj.elements) == 1
        assert elem["type"] == "heading"
        assert elem["level"] == 1
    
    def test_add_paragraph(self):
        """Test adding paragraph element."""
        proj = create_project(name="test")
        elem = proj.add_element("paragraph", "Content here")
        assert len(proj.elements) == 1
        assert elem["content"] == "Content here"
    
    def test_add_code(self):
        """Test adding code block."""
        proj = create_project(name="test")
        elem = proj.add_element("code", "print('hi')", language="python")
        assert elem["type"] == "code"
        assert elem["language"] == "python"
    
    def test_add_list(self):
        """Test adding list."""
        proj = create_project(name="test")
        elem = proj.add_element("list", "", items=["a", "b", "c"], ordered=False)
        assert len(elem["items"]) == 3
    
    def test_to_markdown_simple(self):
        """Test Markdown rendering - simple doc."""
        proj = create_project(name="test", title="My Doc")
        proj.add_element("heading", "Intro", level=1)
        proj.add_element("paragraph", "Hello world")
        
        md = proj.to_markdown()
        assert "# My Doc" in md
        assert "# Intro" in md
        assert "Hello world" in md
    
    def test_to_markdown_code(self):
        """Test Markdown rendering - code block."""
        proj = create_project(name="test")
        proj.add_element("code", "x = 1", language="python")
        
        md = proj.to_markdown()
        assert "```python" in md
        assert "x = 1" in md
        assert "```" in md
    
    def test_to_markdown_list(self):
        """Test Markdown rendering - list."""
        proj = create_project(name="test")
        proj.add_element("list", "", items=["one", "two"], ordered=False)
        
        md = proj.to_markdown()
        assert "- one" in md
        assert "- two" in md
    
    def test_save_and_load(self):
        """Test project persistence."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name
        
        try:
            proj = create_project(name="persist", title="Persistent Doc")
            proj.add_element("heading", "Section", level=2)
            save_project(proj, path)
            
            loaded = load_project(path)
            assert loaded.name == "persist"
            assert loaded.title == "Persistent Doc"
            assert len(loaded.elements) == 1
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestSession:
    """Test Session class with undo/redo."""
    
    def test_session_undo(self):
        """Test undo functionality."""
        proj = create_project(name="test")
        session = Session(proj)
        
        def execute():
            return proj.add_element("paragraph", "First")
        
        def undo():
            if proj.elements:
                proj.elements.pop()
        
        cmd = Command("add", execute, undo)
        session.execute(cmd)
        assert len(proj.elements) == 1
        
        result = session.undo()
        assert result == True
        assert len(proj.elements) == 0
    
    def test_session_redo(self):
        """Test redo functionality."""
        proj = create_project(name="test")
        session = Session(proj)
        
        state = {"count": 0}
        
        def execute():
            state["count"] += 1
            return state["count"]
        
        def undo():
            state["count"] -= 1
        
        cmd = Command("inc", execute, undo)
        session.execute(cmd)
        assert state["count"] == 1
        
        session.undo()
        assert state["count"] == 0
        
        session.redo()
        assert state["count"] == 1
    
    def test_session_can_undo_redo(self):
        """Test can_undo and can_redo checks."""
        proj = create_project(name="test")
        session = Session(proj)
        
        assert session.can_undo() == False
        assert session.can_redo() == False
        
        def execute(): pass
        def undo(): pass
        
        session.execute(Command("test", execute, undo))
        assert session.can_undo() == True
        assert session.can_redo() == False
        
        session.undo()
        assert session.can_undo() == False
        assert session.can_redo() == True
    
    def test_session_history(self):
        """Test history tracking."""
        proj = create_project(name="test")
        session = Session(proj)
        
        def execute(): pass
        def undo(): pass
        
        session.execute(Command("first", execute, undo, "First command"))
        session.execute(Command("second", execute, undo, "Second command"))
        
        hist = session.get_history()
        assert len(hist) == 2
        assert hist[0]["name"] == "first"
        assert hist[1]["name"] == "second"
        assert hist[1]["active"] == True
