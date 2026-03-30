"""Unified REPL skin for CLI-Anything tools."""
from typing import Optional, List, Dict, Any
import os
import sys


class ReplSkin:
    """Provides consistent REPL interface across all CLI-Anything tools."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._skill_path: Optional[str] = None
    
    def _detect_skill_path(self) -> Optional[str]:
        """Auto-detect skills/SKILL.md path."""
        # Look for skills/SKILL.md relative to the package
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skill_path = os.path.join(package_dir, "skills", "SKILL.md")
        if os.path.exists(skill_path):
            return skill_path
        return None
    
    def print_banner(self) -> None:
        """Print branded startup banner."""
        width = 44
        title = f"cli-anything-{self.name}"
        subtitle = f"v{self.version}"
        
        print("╔" + "═" * width + "╗")
        print("║" + title.center(width) + "║")
        print("║" + subtitle.center(width) + "║")
        print("╚" + "═" * width + "╝")
        
        # Show skill path if available
        skill_path = self._detect_skill_path()
        if skill_path:
            print(f"◇ Skill: {skill_path}")
            print()
    
    def create_prompt_session(self):
        """Create prompt_toolkit session with history and styling."""
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.styles import Style
            
            history_file = os.path.expanduser(f"~/.cli_anything_{self.name}_history")
            
            style = Style.from_dict({
                'prompt': '#00aa00 bold',
                'project': '#0088ff',
                'modified': '#ff8800',
            })
            
            return PromptSession(
                history=FileHistory(history_file),
                style=style
            )
        except ImportError:
            return None
    
    def get_input(self, session, project_name: Optional[str] = None, 
                  modified: bool = False) -> str:
        """Get user input with styled prompt."""
        prompt_parts = [self.name]
        
        if project_name:
            prompt_parts.append(f"[{project_name}]")
        
        if modified:
            prompt_parts.append("*")
        
        prompt = "> ".join(prompt_parts) + "> "
        
        if session:
            try:
                from prompt_toolkit.formatted_text import HTML
                return session.prompt(HTML(f'<prompt>{prompt}</prompt>'))
            except:
                pass
        
        return input(prompt)
    
    def success(self, message: str) -> None:
        """Print success message."""
        print(f"✓ {message}")
    
    def error(self, message: str) -> None:
        """Print error message."""
        print(f"✗ {message}", file=sys.stderr)
    
    def warning(self, message: str) -> None:
        """Print warning message."""
        print(f"⚠ {message}")
    
    def info(self, message: str) -> None:
        """Print info message."""
        print(f"● {message}")
    
    def status(self, key: str, value: str) -> None:
        """Print key-value status line."""
        print(f"  {key}: {value}")
    
    def table(self, headers: List[str], rows: List[List[str]]) -> None:
        """Print formatted table."""
        if not rows:
            print("  (empty)")
            return
        
        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))
        
        # Print header
        header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
        print(f"  {header_line}")
        print(f"  {'-' * len(header_line)}")
        
        # Print rows
        for row in rows:
            row_str = " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
            print(f"  {row_str}")
    
    def progress(self, current: int, total: int, message: str = "") -> None:
        """Print progress bar."""
        width = 30
        filled = int(width * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (width - filled)
        percent = int(100 * current / total) if total > 0 else 0
        print(f"  [{bar}] {percent}% {message}")
    
    def print_goodbye(self) -> None:
        """Print styled exit message."""
        print("\nGoodbye! 👋")
    
    def help(self, commands: Dict[str, str]) -> None:
        """Print formatted help listing."""
        print("\nAvailable commands:")
        max_len = max(len(cmd) for cmd in commands.keys()) if commands else 0
        for cmd, desc in sorted(commands.items()):
            print(f"  {cmd.ljust(max_len + 2)} {desc}")
        print()
