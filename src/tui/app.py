"""Main TUI Application."""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label
from textual.binding import Binding

from .screens.tasks_screen import TasksScreen
from .screens.pomodoro_screen import PomodoroScreen
from .screens.notes_screen import NotesScreen


class Sidebar(Static):
    """Navigation sidebar."""
    
    DEFAULT_CSS = """
    Sidebar {
        width: 20;
        height: 100%;
        background: $surface-darken-1;
        border-right: solid $primary;
    }
    
    Sidebar .nav-title {
        text-align: center;
        padding: 1 0;
        text-style: bold;
        color: $primary;
    }
    
    Sidebar .nav-button {
        margin: 0 1;
        width: 100%;
    }
    
    Sidebar .nav-button:focus {
        background: $primary;
        color: $text;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Label("📋 效率工具", classes="nav-title")
        yield Button("📝 任务", id="nav-tasks", classes="nav-button")
        yield Button("🍅 番茄钟", id="nav-pomodoro", classes="nav-button")
        yield Button("📒 笔记", id="nav-notes", classes="nav-button")


class ProductivityApp(App):
    """Main productivity TUI application."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    .main-content {
        width: 100%;
        height: 100%;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("1", "show_tasks", "任务"),
        Binding("2", "show_pomodoro", "番茄钟"),
        Binding("3", "show_notes", "笔记"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield Sidebar()
            with Vertical(classes="main-content"):
                yield TasksScreen()
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle navigation button presses."""
        button_id = event.button.id
        if button_id == "nav-tasks":
            self.action_show_tasks()
        elif button_id == "nav-pomodoro":
            self.action_show_pomodoro()
        elif button_id == "nav-notes":
            self.action_show_notes()
    
    def action_show_tasks(self) -> None:
        """Switch to tasks screen."""
        self._switch_screen(TasksScreen())
    
    def action_show_pomodoro(self) -> None:
        """Switch to pomodoro screen."""
        self._switch_screen(PomodoroScreen())
    
    def action_show_notes(self) -> None:
        """Switch to notes screen."""
        self._switch_screen(NotesScreen())
    
    def _switch_screen(self, new_screen) -> None:
        """Replace current main content with new screen."""
        main_content = self.query_one(".main-content", Vertical)
        main_content.remove_children()
        main_content.mount(new_screen)


def main():
    """Run the TUI application."""
    app = ProductivityApp()
    app.run()


if __name__ == "__main__":
    main()
