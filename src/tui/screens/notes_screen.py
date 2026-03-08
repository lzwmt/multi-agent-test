"""Notes management screen."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Grid
from textual.widgets import (
    Static, Button, Input, TextArea, Label, DataTable, ListView, ListItem
)
from textual.reactive import reactive
from textual.screen import ModalScreen

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notes import add_note, list_notes, show_note, delete_note, search_notes
from storage import load_json, save_json


class NoteManager:
    """Wrapper class for note functions."""
    
    def add_note(self, title: str, content: str, tags: list = None) -> bool:
        """Add a new note with title."""
        # Combine title and content
        full_content = f"# {title}\n\n{content}" if title else content
        return add_note(full_content, tags)
    
    def list_notes(self) -> list:
        return list_notes()
    
    def get_note(self, note_id: int) -> dict:
        return show_note(note_id)
    
    def delete_note(self, note_id: int) -> bool:
        return delete_note(note_id)
    
    def update_note(self, note_id: int, title: str = None, content: str = None, tags: list = None) -> bool:
        """Update an existing note."""
        notes = load_json("notes.json", [])
        for note in notes:
            if note.get("id") == note_id:
                if title or content:
                    full_content = f"# {title}\n\n{content}" if title else content
                    note["content"] = full_content
                if tags is not None:
                    note["tags"] = tags
                from datetime import datetime
                note["updated_at"] = datetime.now().isoformat()
                return save_json("notes.json", notes)
        return False
    
    def search_notes(self, keyword: str) -> list:
        return search_notes(keyword)


class AddNoteModal(ModalScreen):
    """Modal for adding/editing notes."""
    
    DEFAULT_CSS = """
    AddNoteModal {
        align: center middle;
    }
    
    AddNoteModal .modal-container {
        width: 80%;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: solid $primary;
        padding: 1 2;
    }
    
    AddNoteModal .modal-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        height: 3;
    }
    
    AddNoteModal .input-row {
        height: auto;
        margin: 1 0;
    }
    
    AddNoteModal .content-area {
        height: 15;
        margin: 1 0;
    }
    
    AddNoteModal .button-row {
        height: auto;
        content-align: center middle;
        margin: 1 0;
    }
    """
    
    def __init__(self, note_id: int = None, title: str = "", content: str = "", tags: str = ""):
        super().__init__()
        self.note_id = note_id
        self.note_title = title
        self.note_content = content
        self.note_tags = tags
    
    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-container"):
            title_text = "编辑笔记" if self.note_id else "新建笔记"
            yield Label(f"📝 {title_text}", classes="modal-title")
            
            with Horizontal(classes="input-row"):
                yield Input(value=self.note_title, placeholder="标题", id="note-title")
            
            with Horizontal(classes="input-row"):
                yield Input(value=self.note_tags, placeholder="标签 (用逗号分隔)", id="note-tags")
            
            yield TextArea(text=self.note_content, id="note-content", classes="content-area")
            
            with Horizontal(classes="button-row"):
                yield Button("💾 保存", id="save-btn", variant="success")
                yield Button("❌ 取消", id="cancel-btn", variant="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "save-btn":
            title = self.query_one("#note-title", Input).value.strip()
            content = self.query_one("#note-content", TextArea).text.strip()
            tags = self.query_one("#note-tags", Input).value.strip()
            
            if not title:
                self.notify("请输入标题", severity="error")
                return
            
            self.dismiss({
                "id": self.note_id,
                "title": title,
                "content": content,
                "tags": tags
            })
        elif button_id == "cancel-btn":
            self.dismiss(None)


class NotesScreen(Static):
    """Notes management screen."""
    
    DEFAULT_CSS = """
    NotesScreen {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    NotesScreen .header {
        height: 3;
        content-align: center middle;
        text-style: bold;
        color: $primary;
    }
    
    NotesScreen .toolbar {
        height: auto;
        margin: 1 0;
    }
    
    NotesScreen .search-input {
        width: 70%;
    }
    
    NotesScreen .add-btn {
        width: 25%;
    }
    
    NotesScreen .tags-container {
        height: auto;
        margin: 1 0;
    }
    
    NotesScreen .tag-btn {
        margin: 0 1;
    }
    
    NotesScreen .notes-grid {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        height: 1fr;
        overflow-y: auto;
    }
    
    NotesScreen .note-card {
        height: auto;
        border: solid $surface-darken-1;
        padding: 1;
        background: $surface-darken-1;
    }
    
    NotesScreen .note-card:hover {
        border: solid $primary;
    }
    
    NotesScreen .note-title {
        text-style: bold;
        color: $primary;
        height: auto;
    }
    
    NotesScreen .note-content {
        color: $text;
        height: 4;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    NotesScreen .note-tags {
        color: $text-muted;
        height: auto;
        margin-top: 1;
    }
    
    NotesScreen .note-date {
        color: $text-muted;
        text-align: right;
        height: auto;
    }
    
    NotesScreen .note-actions {
        height: auto;
        content-align: right middle;
        margin-top: 1;
    }
    
    NotesScreen .stats {
        height: 3;
        content-align: center middle;
        color: $text-muted;
    }
    """
    
    notes = reactive([])
    all_tags = reactive([])
    selected_tag = reactive(None)
    search_query = reactive("")
    
    def __init__(self):
        super().__init__()
        self.note_manager = NoteManager()
    
    def compose(self) -> ComposeResult:
        yield Label("📒 笔记管理", classes="header")
        
        with Horizontal(classes="toolbar"):
            yield Input(placeholder="搜索笔记...", id="search-input", classes="search-input")
            yield Button("➕ 新建笔记", id="add-btn", classes="add-btn", variant="primary")
        
        with Horizontal(classes="tags-container"):
            yield Button("全部", id="tag-all", classes="tag-btn", variant="primary")
        
        with Grid(classes="notes-grid"):
            pass  # Notes will be added dynamically
        
        yield Label("加载中...", id="stats", classes="stats")
    
    def on_mount(self) -> None:
        """Initialize on mount."""
        self.load_notes()
    
    def load_notes(self) -> None:
        """Load and display notes."""
        self.notes = self.note_manager.list_notes()
        self.update_tags()
        self.update_notes_display()
        self.update_stats()
    
    def update_tags(self) -> None:
        """Update tag buttons."""
        # Collect all unique tags
        tags = set()
        for note in self.notes:
            tags.update(note.get("tags", []))
        self.all_tags = sorted(list(tags))
        
        # Update tag buttons
        container = self.query_one(".tags-container", Horizontal)
        # Remove old tag buttons (keep "全部")
        for child in list(container.children):
            if child.id != "tag-all":
                child.remove()
        
        for tag in self.all_tags:
            btn = Button(f"🏷️ {tag}", id=f"tag-{tag}", classes="tag-btn")
            container.mount(btn)
    
    def update_notes_display(self) -> None:
        """Update the notes grid."""
        grid = self.query_one(".notes-grid", Grid)
        grid.remove_children()
        
        filtered_notes = self.get_filtered_notes()
        
        for note in filtered_notes:
            note_id = note.get("id", 0)
            title = note.get("title", "")
            content = note.get("content", "")
            tags = note.get("tags", [])
            created = note.get("created_at", "")[:10]
            
            tags_display = " ".join([f"#{t}" for t in tags]) if tags else ""
            content_preview = content[:100] + "..." if len(content) > 100 else content
            
            card = Vertical(classes="note-card")
            card.mount(Label(title, classes="note-title"))
            card.mount(Label(content_preview, classes="note-content"))
            card.mount(Label(tags_display, classes="note-tags"))
            card.mount(Label(created, classes="note-date"))
            
            with Horizontal(classes="note-actions"):
                edit_btn = Button("✏️ 编辑", id=f"edit-{note_id}")
                delete_btn = Button("🗑️ 删除", id=f"delete-{note_id}", variant="error")
                card.mount(edit_btn)
                card.mount(delete_btn)
            
            grid.mount(card)
    
    def get_filtered_notes(self) -> list:
        """Get notes filtered by tag and search query."""
        filtered = self.notes
        
        # Filter by tag
        if self.selected_tag:
            filtered = [n for n in filtered if self.selected_tag in n.get("tags", [])]
        
        # Filter by search query
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                n for n in filtered
                if query in n.get("title", "").lower()
                or query in n.get("content", "").lower()
            ]
        
        return filtered
    
    def update_stats(self) -> None:
        """Update statistics display."""
        total = len(self.notes)
        filtered = len(self.get_filtered_notes())
        
        stats_label = self.query_one("#stats", Label)
        if self.search_query or self.selected_tag:
            stats_label.update(f"总计: {total} | 当前显示: {filtered}")
        else:
            stats_label.update(f"共 {total} 条笔记")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "add-btn":
            self.push_screen(AddNoteModal(), self.on_note_modal_result)
        elif button_id == "tag-all":
            self.selected_tag = None
            self.update_tag_buttons()
            self.update_notes_display()
            self.update_stats()
        elif button_id and button_id.startswith("tag-"):
            tag = button_id.replace("tag-", "")
            self.selected_tag = tag
            self.update_tag_buttons()
            self.update_notes_display()
            self.update_stats()
        elif button_id and button_id.startswith("edit-"):
            note_id = int(button_id.replace("edit-", ""))
            self.edit_note(note_id)
        elif button_id and button_id.startswith("delete-"):
            note_id = int(button_id.replace("delete-", ""))
            self.delete_note(note_id)
    
    def update_tag_buttons(self) -> None:
        """Update tag button styles."""
        # Update "全部" button
        all_btn = self.query_one("#tag-all", Button)
        if self.selected_tag is None:
            all_btn.variant = "primary"
        else:
            all_btn.variant = "default"
        
        # Update tag buttons
        for tag in self.all_tags:
            btn = self.query_one(f"#tag-{tag}", Button)
            if btn:
                if self.selected_tag == tag:
                    btn.variant = "primary"
                else:
                    btn.variant = "default"
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_query = event.value.strip()
            self.update_notes_display()
            self.update_stats()
    
    def edit_note(self, note_id: int) -> None:
        """Edit a note."""
        note = self.note_manager.get_note(note_id)
        if note:
            tags_str = ", ".join(note.get("tags", []))
            self.push_screen(
                AddNoteModal(
                    note_id=note_id,
                    title=note.get("title", ""),
                    content=note.get("content", ""),
                    tags=tags_str
                ),
                self.on_note_modal_result
            )
    
    def delete_note(self, note_id: int) -> None:
        """Delete a note."""
        self.note_manager.delete_note(note_id)
        self.notify(f"笔记 #{note_id} 已删除", severity="information")
        self.load_notes()
    
    def on_note_modal_result(self, result) -> None:
        """Handle note modal result."""
        if result:
            note_id = result.get("id")
            title = result.get("title")
            content = result.get("content")
            tags_str = result.get("tags", "")
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
            
            if note_id:
                # Update existing note
                self.note_manager.update_note(note_id, title=title, content=content, tags=tags)
                self.notify(f"笔记 #{note_id} 已更新", severity="success")
            else:
                # Create new note
                self.note_manager.add_note(title, content, tags)
                self.notify(f"笔记已创建: {title}", severity="success")
            
            self.load_notes()
