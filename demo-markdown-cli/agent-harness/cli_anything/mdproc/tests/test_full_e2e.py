"""End-to-end tests for mdproc."""
import pytest
import json
import os
import tempfile
import subprocess
import sys
from ..core.project import create_project, save_project, load_project
from ..core.export import export_to_markdown, export_to_html


class TestE2EWorkflow:
    """Test complete document creation workflows."""
    
    def test_full_document_creation(self):
        """Test complete document creation workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            proj_path = os.path.join(tmpdir, "doc.json")
            md_path = os.path.join(tmpdir, "doc.md")
            
            # Create project
            proj = create_project(name="tutorial", title="Tutorial", author="Test")
            proj.add_element("heading", "Introduction", level=1)
            proj.add_element("paragraph", "Welcome to this tutorial.")
            proj.add_element("heading", "Getting Started", level=2)
            proj.add_element("code", "pip install package", language="bash")
            proj.add_element("list", "", items=["Step 1", "Step 2", "Step 3"])
            
            # Save
            save_project(proj, proj_path)
            assert os.path.exists(proj_path)
            
            # Load and verify
            loaded = load_project(proj_path)
            assert loaded.name == "tutorial"
            assert len(loaded.elements) == 5
            
            # Export
            result = export_to_markdown(loaded, md_path)
            assert os.path.exists(md_path)
            assert result["size"] > 0
            
            # Verify content
            with open(md_path, "r") as f:
                content = f.read()
            assert "# Tutorial" in content
            assert "# Introduction" in content
            assert "```bash" in content
    
    def test_markdown_export_format(self):
        """Test Markdown export produces valid format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            proj = create_project(name="test", title="Export Test")
            proj.add_element("heading", "Section", level=1)
            proj.add_element("paragraph", "Test paragraph")
            proj.add_element("quote", "This is a quote")
            proj.add_element("horizontal_rule", "")
            
            md_path = os.path.join(tmpdir, "export.md")
            result = export_to_markdown(proj, md_path)
            
            with open(md_path, "r") as f:
                content = f.read()
            
            assert "# Export Test" in content
            assert "# Section" in content
            assert "> This is a quote" in content
            assert "---" in content
            print(f"\n  Markdown: {md_path} ({result['size']:,} bytes)")
    
    def test_html_export_format(self):
        """Test HTML export produces valid structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            proj = create_project(name="test", title="HTML Test")
            proj.add_element("heading", "Content", level=1)
            proj.add_element("paragraph", "HTML content")
            
            html_path = os.path.join(tmpdir, "export.html")
            result = export_to_html(proj, html_path)
            
            with open(html_path, "r") as f:
                content = f.read()
            
            assert "<!DOCTYPE html>" in content
            assert "<title>HTML Test</title>" in content
            assert "<h1" in content and "Content" in content
            assert "<p>HTML content</p>" in content
            print(f"\n  HTML: {html_path} ({result['size']:,} bytes)")
    
    def test_multi_element_document(self):
        """Test document with many different element types."""
        proj = create_project(name="complex", title="Complex Document")
        
        # Add various elements
        proj.add_element("heading", "Overview", level=1)
        proj.add_element("paragraph", "This is a complex document.")
        proj.add_element("heading", "Code Example", level=2)
        proj.add_element("code", "def hello():\n    return 'world'", language="python")
        proj.add_element("heading", "Features", level=2)
        proj.add_element("list", "", items=["Fast", "Simple", "Powerful"], ordered=False)
        proj.add_element("quote", "Simplicity is the ultimate sophistication.")
        proj.add_element("table", "", headers=["Name", "Value"], rows=[["A", "1"], ["B", "2"]])
        proj.add_element("horizontal_rule", "")
        proj.add_element("paragraph", "End of document.")
        
        md = proj.to_markdown()
        
        # Verify all element types rendered
        assert "# Complex Document" in md
        assert "## Code Example" in md
        assert "```python" in md
        assert "- Fast" in md
        assert "> Simplicity" in md
        assert "| Name | Value |" in md
        assert "---" in md


class TestCLISubprocess:
    """Test installed CLI command via subprocess."""
    
    CLI_BASE = ["cli-anything-mdproc"]
    
    def _run(self, args, check=True):
        """Run CLI command."""
        result = subprocess.run(self.CLI_BASE + args, capture_output=True, text=True, check=check)
        return result
    
    def test_help_output(self):
        """Test --help works."""
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "Markdown Processor" in result.stdout
    
    def test_new_project(self, tmp_path):
        """Test creating project."""
        proj_path = tmp_path / "test.json"
        
        result = self._run([
            "new", "-n", "test", "-t", "Test Doc", "-o", str(proj_path)
        ])
        
        assert result.returncode == 0
        assert "Created project" in result.stdout
        assert os.path.exists(proj_path)
    
    def test_info_command(self, tmp_path):
        """Test info command via CLI."""
        proj_path = tmp_path / "info-test.json"
        
        # Create project first
        self._run(["new", "-n", "info-test", "-o", str(proj_path)])
        
        # Get info
        result = self._run(["-p", str(proj_path), "info"])
        
        assert result.returncode == 0
        assert "info-test" in result.stdout
    
    def test_add_heading(self, tmp_path):
        """Test adding heading via CLI."""
        proj_path = tmp_path / "heading-test.json"
        
        # Create and add heading
        self._run(["new", "-n", "heading-test", "-o", str(proj_path)])
        result = self._run(["-p", str(proj_path), "heading", "My Heading"])
        
        assert result.returncode == 0
        assert "Added heading" in result.stdout
        
        # Verify file was updated
        with open(proj_path, "r") as f:
            data = json.load(f)
        assert len(data["elements"]) == 1
    
    def test_add_paragraph(self, tmp_path):
        """Test adding paragraph via CLI."""
        proj_path = tmp_path / "para-test.json"
        
        self._run(["new", "-n", "para-test", "-o", str(proj_path)])
        result = self._run(["-p", str(proj_path), "paragraph", "Some text here"])
        
        assert result.returncode == 0
        assert "Added paragraph" in result.stdout
    
    def test_export_markdown(self, tmp_path):
        """Test export to Markdown via CLI."""
        proj_path = tmp_path / "export-test.json"
        md_path = tmp_path / "output.md"
        
        # Create with content
        self._run(["new", "-n", "export-test", "-o", str(proj_path)])
        self._run(["-p", str(proj_path), "heading", "Title"])
        self._run(["-p", str(proj_path), "paragraph", "Content"])
        
        # Export
        result = self._run(["-p", str(proj_path), "export", str(md_path)])
        
        assert result.returncode == 0
        assert "Exported" in result.stdout
        assert os.path.exists(md_path)
        
        with open(md_path, "r") as f:
            content = f.read()
        assert "# Title" in content
    
    def test_preview(self, tmp_path):
        """Test preview command."""
        proj_path = tmp_path / "preview-test.json"
        
        self._run(["new", "-n", "preview-test", "-o", str(proj_path)])
        self._run(["-p", str(proj_path), "heading", "Preview Test"])
        
        result = self._run(["-p", str(proj_path), "preview"])
        
        assert result.returncode == 0
        assert "# Preview Test" in result.stdout
