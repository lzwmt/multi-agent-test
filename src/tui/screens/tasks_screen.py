"""Tasks management screen."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import (
    Static, Button, Input, DataTable, Label, Checkbox
)
from textual.reactive import reactive

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks import add_task, list_tasks, complete_task, delete_task, get_task_stats


class TaskManager:
    """Wrapper class for task functions."""
    
    def add_task(self, title: str, priority: str = "medium") -> bool:
        return add_task(title, priority)
    
    def list_tasks(self, show_all: bool = False):
        return list_tasks(show_all)
    
    def complete_task(self, task_id: int) -> bool:
        return complete_task(task_id)
    
    def uncomplete_task(self, task_id: int) -> bool:
        # Load and modify directly
        from storage import load_json, save_json
        tasks = load_json("tasks.json", [])
        for task in tasks:
            if task.get("id") == task_id:
                task["completed"] = False
                task["completed_at"] = None
                return save_json("tasks.json", tasks)
        return False
    
    def delete_task(self, task_id: int) -> bool:
        return delete_task(task_id)
    
    def get_task(self, task_id: int):
        from storage import load_json
        tasks = load_json("tasks.json", [])
        for task in tasks:
            if task.get("id") == task_id:
                return task
        return None


class TasksScreen(Static):
    """Tasks management screen."""
    
    DEFAULT_CSS = """
    TasksScreen {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    TasksScreen .header {
        height: 3;
        content-align: center middle;
        text-style: bold;
        color: $primary;
    }
    
    TasksScreen .toolbar {
        height: auto;
        margin: 1 0;
    }
    
    TasksScreen .task-input {
        width: 60%;
    }
    
    TasksScreen .priority-select {
        width: 20%;
    }
    
    TasksScreen .add-btn {
        width: 15%;
    }
    
    TasksScreen .filter-bar {
        height: auto;
        margin: 1 0;
    }
    
    TasksScreen .task-table {
        width: 100%;
        height: 1fr;
        border: solid $primary-darken-2;
    }
    
    TasksScreen .stats {
        height: 3;
        content-align: center middle;
        color: $text-muted;
    }
    
    TasksScreen .completed {
        text-style: strike;
        color: $text-muted;
    }
    
    TasksScreen .priority-high {
        color: $error;
    }
    
    TasksScreen .priority-medium {
        color: $warning;
    }
    
    TasksScreen .priority-low {
        color: $success;
    }
    """
    
    tasks = reactive([])
    filter_status = reactive("all")  # all, active, completed
    
    def __init__(self):
        super().__init__()
        self.task_manager = TaskManager()
    
    def compose(self) -> ComposeResult:
        yield Label("📝 任务管理", classes="header")
        
        with Horizontal(classes="toolbar"):
            yield Input(placeholder="输入新任务...", id="task-input", classes="task-input")
            yield Input(placeholder="优先级 (high/medium/low)", id="priority-input", classes="priority-select")
            yield Button("➕ 添加", id="add-btn", classes="add-btn", variant="primary")
        
        with Horizontal(classes="filter-bar"):
            yield Button("全部", id="filter-all", variant="primary")
            yield Button("未完成", id="filter-active")
            yield Button("已完成", id="filter-completed")
        
        yield DataTable(id="task-table", classes="task-table")
        
        yield Label("加载中...", id="stats", classes="stats")
    
    def on_mount(self) -> None:
        """Initialize on mount."""
        table = self.query_one("#task-table", DataTable)
        table.add_columns("完成", "ID", "任务", "优先级", "创建时间", "操作")
        table.cursor_type = "row"
        self.load_tasks()
    
    def load_tasks(self) -> None:
        """Load and display tasks."""
        self.tasks = self.task_manager.list_tasks(show_all=True)
        self.update_table()
        self.update_stats()
    
    def update_table(self) -> None:
        """Update the task table."""
        table = self.query_one("#task-table", DataTable)
        table.clear()
        
        for task in self.tasks:
            # Filter
            if self.filter_status == "active" and task.get("completed"):
                continue
            if self.filter_status == "completed" and not task.get("completed"):
                continue
            
            task_id = str(task.get("id", ""))
            title = task.get("title", "")
            priority = task.get("priority", "medium")
            created = task.get("created_at", "")[:10]
            completed = task.get("completed", False)
            
            # Style based on priority
            priority_class = f"priority-{priority}"
            priority_display = {"high": "🔴 高", "medium": "🟡 中", "low": "🟢 低"}.get(priority, priority)
            
            # Checkbox for completion
            checkbox = "✅" if completed else "⬜"
            
            # Style completed tasks
            if completed:
                title_display = f"[strike]{title}[/strike]"
            else:
                title_display = title
            
            table.add_row(
                checkbox,
                task_id,
                title_display,
                f"[{priority_class}]{priority_display}[/{priority_class}]",
                created,
                "🗑️ 删除",
                key=task_id
            )
    
    def update_stats(self) -> None:
        """Update statistics display."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.get("completed"))
        active = total - completed
        
        stats_label = self.query_one("#stats", Label)
        stats_label.update(f"总计: {total} | 未完成: {active} | 已完成: {completed}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "add-btn":
            self.add_task()
        elif button_id == "filter-all":
            self.filter_status = "all"
            self.update_filter_buttons()
            self.update_table()
        elif button_id == "filter-active":
            self.filter_status = "active"
            self.update_filter_buttons()
            self.update_table()
        elif button_id == "filter-completed":
            self.filter_status = "completed"
            self.update_filter_buttons()
            self.update_table()
    
    def update_filter_buttons(self) -> None:
        """Update filter button styles."""
        for btn_id in ["filter-all", "filter-active", "filter-completed"]:
            btn = self.query_one(f"#{btn_id}", Button)
            if btn_id == f"filter-{self.filter_status}":
                btn.variant = "primary"
            else:
                btn.variant = "default"
    
    def add_task(self) -> None:
        """Add a new task."""
        input_widget = self.query_one("#task-input", Input)
        priority_input = self.query_one("#priority-input", Input)
        
        title = input_widget.value.strip()
        priority = priority_input.value.strip().lower() or "medium"
        
        if not title:
            self.notify("请输入任务内容", severity="error")
            return
        
        if priority not in ["high", "medium", "low"]:
            priority = "medium"
        
        self.task_manager.add_task(title, priority)
        input_widget.value = ""
        priority_input.value = ""
        
        self.notify(f"任务已添加: {title}", severity="information")
        self.load_tasks()
    
    def on_data_table_cell_selected(self, event) -> None:
        """Handle table cell selection."""
        table = self.query_one("#task-table", DataTable)
        row_key = event.cell_key.row_key
        
        if row_key:
            task_id = int(row_key.value)
            self.toggle_task(task_id)
    
    def toggle_task(self, task_id: int) -> None:
        """Toggle task completion status."""
        task = self.task_manager.get_task(task_id)
        if task:
            if task.get("completed"):
                self.task_manager.uncomplete_task(task_id)
                self.notify(f"任务 #{task_id} 标记为未完成", severity="information")
            else:
                self.task_manager.complete_task(task_id)
                self.notify(f"任务 #{task_id} 已完成！", severity="success")
            self.load_tasks()
