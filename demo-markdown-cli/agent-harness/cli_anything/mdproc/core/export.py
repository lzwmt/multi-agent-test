"""Export functionality for Markdown documents."""
import os
import markdown
from typing import Optional
from .project import Project


def export_to_markdown(project: Project, output_path: str) -> dict:
    """Export project to Markdown file."""
    content = project.to_markdown()
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return {
        "output": output_path,
        "format": "markdown",
        "size": os.path.getsize(output_path),
        "elements": len(project.elements)
    }


def export_to_html(project: Project, output_path: str, 
                   template: Optional[str] = None) -> dict:
    """Export project to HTML file."""
    md_content = project.to_markdown()
    
    # Convert Markdown to HTML
    html_content = markdown.markdown(md_content, extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.tables',
        'markdown.extensions.toc'
    ])
    
    # Wrap in basic HTML template if no custom template provided
    if template is None:
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{project.title or project.name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 16px; border-radius: 6px; overflow-x: auto; }}
        pre code {{ background: none; padding: 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f4f4f4; }}
        blockquote {{ border-left: 4px solid #ddd; margin: 0; padding-left: 16px; color: #666; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
    else:
        html = template.replace("{{content}}", html_content)
        html = html.replace("{{title}}", project.title or project.name)
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return {
        "output": output_path,
        "format": "html",
        "size": os.path.getsize(output_path),
        "elements": len(project.elements)
    }


def export_to_pdf(project: Project, output_path: str) -> dict:
    """Export project to PDF file using WeasyPrint."""
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        raise RuntimeError(
            "weasyprint is not installed. Install it with:\n"
            "  pip install weasyprint"
        )
    
    # First export to HTML string
    md_content = project.to_markdown()
    html_content = markdown.markdown(md_content, extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.tables',
        'markdown.extensions.toc'
    ])
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{project.title or project.name}</title>
</head>
<body>
{html_content}
</body>
</html>"""
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Convert HTML to PDF
    HTML(string=html).write_pdf(output_path)
    
    return {
        "output": output_path,
        "format": "pdf",
        "size": os.path.getsize(output_path),
        "elements": len(project.elements)
    }


def get_export_formats() -> list:
    """Get list of available export formats."""
    formats = [
        {"name": "markdown", "extension": ".md", "description": "Markdown source"},
        {"name": "html", "extension": ".html", "description": "HTML document"},
    ]
    
    # Check if PDF export is available
    try:
        import weasyprint
        formats.append({"name": "pdf", "extension": ".pdf", "description": "PDF document (requires weasyprint)"})
    except ImportError:
        pass
    
    return formats
