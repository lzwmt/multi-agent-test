"""Main CLI entry point for mdproc - Simple file-based mode."""
import click
import json
import os
import sys
from typing import Optional

from .core.project import Project, create_project, save_project, load_project
from .core.export import export_to_markdown, export_to_html, export_to_pdf
from .utils.repl_skin import ReplSkin


def _output_json(data: dict) -> None:
    """Output data as JSON."""
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


@click.group(invoke_without_command=True)
@click.option("--project", "-p", type=click.Path(), help="Project file path")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(ctx, project: Optional[str], json_mode: bool):
    """CLI-Anything Markdown Processor - A stateful CLI for Markdown documents."""
    ctx.ensure_object(dict)
    ctx.obj["json_mode"] = json_mode
    ctx.obj["project_path"] = project
    
    # Load project if specified
    if project and os.path.exists(project):
        ctx.obj["project"] = load_project(project)
    else:
        ctx.obj["project"] = None
    
    # If no subcommand given, enter REPL
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl, project_path=project)


def _get_project(ctx, json_mode: bool) -> Project:
    """Get current project or error."""
    proj = ctx.obj.get("project")
    if proj is None:
        if json_mode:
            _output_json({"success": False, "error": "No project is currently open. Use -p <path> or create new project."})
            sys.exit(1)
        else:
            click.echo("Error: No project is currently open. Use -p <path> or create new project.", err=True)
            sys.exit(1)
    return proj


def _get_path(ctx) -> str:
    """Get current project path."""
    return ctx.obj.get("project_path")


@click.command()
@click.option("--name", "-n", required=True, help="Project name")
@click.option("--title", "-t", default="", help="Document title")
@click.option("--author", "-a", default="", help="Document author")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output project file path")
@click.pass_context
def new(ctx, name: str, title: str, author: str, output: str):
    """Create a new Markdown project."""
    json_mode = ctx.obj.get("json_mode", False)
    """Create a new Markdown project."""
    try:
        project = create_project(name=name, title=title, author=author)
        save_project(project, output)
        
        if json_mode:
            _output_json({"success": True, "message": f"Created project: {name}", "project": project.to_dict(), "path": output})
        else:
            skin = ReplSkin("mdproc")
            skin.success(f"Created project: {name}")
    except Exception as e:
        if json_mode:
            _output_json({"success": False, "error": str(e)})
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("text")
@click.option("--level", "-l", default=1, type=click.IntRange(1, 6), help="Heading level (1-6)")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def heading(ctx, text: str, level: int, json_mode: bool):
    """Add a heading."""
    project = _get_project(ctx, json_mode)
    path = _get_path(ctx)
    
    result = project.add_element("heading", text, level=level)
    save_project(project, path)
    
    if json_mode:
        _output_json({"success": True, "message": f"Added heading: {text}", "element": result})
    else:
        skin = ReplSkin("mdproc")
        skin.success(f"Added heading: {text}")


@click.command()
@click.argument("text")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def paragraph(ctx, text: str, json_mode: bool):
    """Add a paragraph."""
    project = _get_project(ctx, json_mode)
    path = _get_path(ctx)
    
    result = project.add_element("paragraph", text)
    save_project(project, path)
    
    if json_mode:
        _output_json({"success": True, "message": "Added paragraph", "element": result})
    else:
        skin = ReplSkin("mdproc")
        skin.success("Added paragraph")


@click.command()
@click.argument("content")
@click.option("--language", "-l", default="", help="Code language")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def code(ctx, content: str, language: str, json_mode: bool):
    """Add a code block."""
    project = _get_project(ctx, json_mode)
    path = _get_path(ctx)
    
    result = project.add_element("code", content, language=language)
    save_project(project, path)
    
    if json_mode:
        _output_json({"success": True, "message": "Added code block", "element": result})
    else:
        skin = ReplSkin("mdproc")
        skin.success(f"Added code block ({language or 'plain'})")


@click.command()
@click.argument("items", nargs=-1, required=True)
@click.option("--ordered", is_flag=True, help="Create ordered list")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def list_items(ctx, items: tuple, ordered: bool, json_mode: bool):
    """Add a list."""
    project = _get_project(ctx, json_mode)
    path = _get_path(ctx)
    
    result = project.add_element("list", "", items=list(items), ordered=ordered)
    save_project(project, path)
    
    if json_mode:
        _output_json({"success": True, "message": f"Added list ({len(items)} items)", "element": result})
    else:
        skin = ReplSkin("mdproc")
        skin.success(f"Added list ({len(items)} items)")


@click.command()
@click.argument("content")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def quote(ctx, content: str, json_mode: bool):
    """Add a blockquote."""
    project = _get_project(ctx, json_mode)
    path = _get_path(ctx)
    
    result = project.add_element("quote", content)
    save_project(project, path)
    
    if json_mode:
        _output_json({"success": True, "message": "Added blockquote", "element": result})
    else:
        skin = ReplSkin("mdproc")
        skin.success("Added blockquote")


@click.command()
@click.argument("headers", nargs=-1, required=True)
@click.option("--rows", "-r", multiple=True, help="Table row (repeat for each row, comma-separated)")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def table(ctx, headers: tuple, rows: tuple, json_mode: bool):
    """Add a table."""
    project = _get_project(ctx, json_mode)
    path = _get_path(ctx)
    
    result = project.add_element("table", "", headers=list(headers), rows=[list(r.split(",")) for r in rows])
    save_project(project, path)
    
    if json_mode:
        _output_json({"success": True, "message": f"Added table", "element": result})
    else:
        skin = ReplSkin("mdproc")
        skin.success(f"Added table ({len(headers)} columns)")


@click.command()
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def hr(ctx, json_mode: bool):
    """Add a horizontal rule."""
    project = _get_project(ctx, json_mode)
    path = _get_path(ctx)
    
    result = project.add_element("horizontal_rule", "")
    save_project(project, path)
    
    if json_mode:
        _output_json({"success": True, "message": "Added horizontal rule", "element": result})
    else:
        skin = ReplSkin("mdproc")
        skin.success("Added horizontal rule")


@click.command()
@click.argument("output_path", type=click.Path())
@click.option("--format", "-f", "fmt", type=click.Choice(["markdown", "html", "pdf"]), default="markdown", help="Export format")
@click.option("--overwrite", is_flag=True, help="Overwrite existing file")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def export(ctx, output_path: str, fmt: str, overwrite: bool, json_mode: bool):
    """Export project to a file."""
    project = _get_project(ctx, json_mode)
    
    if os.path.exists(output_path) and not overwrite:
        if json_mode:
            _output_json({"success": False, "error": f"File exists: {output_path} (use --overwrite)"})
        else:
            click.echo(f"Error: File exists: {output_path} (use --overwrite)", err=True)
        sys.exit(1)
    
    try:
        if fmt == "markdown":
            result = export_to_markdown(project, output_path)
        elif fmt == "html":
            result = export_to_html(project, output_path)
        elif fmt == "pdf":
            result = export_to_pdf(project, output_path)
        
        if json_mode:
            _output_json({"success": True, "message": f"Exported: {output_path}", **result})
        else:
            skin = ReplSkin("mdproc")
            skin.success(f"Exported: {output_path} ({result['size']:,} bytes)")
    except Exception as e:
        if json_mode:
            _output_json({"success": False, "error": str(e)})
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def info(ctx, json_mode: bool):
    """Show project info."""
    project = _get_project(ctx, json_mode)
    path = _get_path(ctx)
    
    data = {
        "name": project.name,
        "title": project.title,
        "author": project.author,
        "elements": len(project.elements),
        "created_at": project.created_at,
        "modified_at": project.modified_at,
        "path": path,
    }
    
    if json_mode:
        _output_json(data)
    else:
        skin = ReplSkin("mdproc")
        skin.print_banner()
        for key, value in data.items():
            skin.status(key.replace("_", " ").title(), str(value))


@click.command()
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_context
def preview(ctx, json_mode: bool):
    """Preview Markdown content."""
    project = _get_project(ctx, json_mode)
    
    md = project.to_markdown()
    
    if json_mode:
        _output_json({"markdown": md})
    else:
        click.echo("\n" + md + "\n")


@click.command()
@click.option("--project_path", type=click.Path(), help="Project file path")
def repl(project_path: Optional[str]):
    """Enter interactive REPL mode."""
    from .core.session import Session
    
    skin = ReplSkin("mdproc", version="1.0.0")
    skin.print_banner()
    
    project = None
    path = None
    
    # Load project if path provided
    if project_path and os.path.exists(project_path):
        project = load_project(project_path)
        path = project_path
        skin.success(f"Loaded project: {project.name}")
    
    while True:
        try:
            line = input(f"{project.name if project else 'mdproc'}> ").strip()
            if not line:
                continue
            
            if line in ("exit", "quit", "q"):
                skin.print_goodbye()
                break
            
            if line in ("help", "?"):
                click.echo("""
Commands:
  new <name> -t "Title" -o <path>  Create new project
  heading <text>                   Add heading
  paragraph <text>                 Add paragraph
  code <content> -l <lang>         Add code block
  list <items...>                  Add list
  quote <text>                     Add blockquote
  export <path>                    Export to file
  info                             Show project info
  preview                          Preview Markdown
  save                             Save project
  exit                             Exit REPL
""")
                continue
            
            # Simple command parsing
            if line.startswith("new "):
                click.echo("Use: cli-anything-mdproc new -n name -t 'Title' -o path.json")
            elif line.startswith("heading "):
                if project:
                    text = line[8:]
                    project.add_element("heading", text, level=1)
                    if path:
                        save_project(project, path)
                    skin.success(f"Added heading: {text}")
                else:
                    skin.error("No project open")
            elif line.startswith("paragraph "):
                if project:
                    text = line[10:]
                    project.add_element("paragraph", text)
                    if path:
                        save_project(project, path)
                    skin.success("Added paragraph")
                else:
                    skin.error("No project open")
            elif line == "info":
                if project:
                    skin.status("Name", project.name)
                    skin.status("Elements", str(len(project.elements)))
            elif line == "preview":
                if project:
                    click.echo("\n" + project.to_markdown() + "\n")
            elif line == "save":
                if project and path:
                    save_project(project, path)
                    skin.success("Saved")
                else:
                    skin.error("No project or path")
            else:
                skin.warning(f"Unknown command: {line}")
        
        except KeyboardInterrupt:
            click.echo()
            continue
        except EOFError:
            break


# Register commands
cli.add_command(new)
cli.add_command(heading)
cli.add_command(paragraph)
cli.add_command(code)
cli.add_command(list_items)
cli.add_command(quote)
cli.add_command(table)
cli.add_command(hr)
cli.add_command(export)
cli.add_command(info)
cli.add_command(preview)
cli.add_command(repl)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
