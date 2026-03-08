"""Pomodoro timer screen."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center
from textual.widgets import Static, Button, Label, ProgressBar
from textual.reactive import reactive
from textual.timer import Timer
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pomodoro import start_pomodoro, _record_completion
from storage import load_json, save_json
from datetime import date


class PomodoroTimer:
    """Wrapper class for pomodoro functions."""
    
    def record_session(self, minutes: int) -> None:
        """Record a completed session."""
        stats = load_json("pomodoro_stats.json", {})
        today = date.today().isoformat()
        
        if today not in stats:
            stats[today] = {"count": 0, "total_minutes": 0, "sessions": []}
        
        from datetime import datetime
        session = {
            "start_time": datetime.now().isoformat(),
            "duration": minutes,
            "completed_at": datetime.now().isoformat()
        }
        
        stats[today]["count"] += 1
        stats[today]["total_minutes"] += minutes
        stats[today]["sessions"].append(session)
        
        save_json("pomodoro_stats.json", stats)
    
    def get_stats(self):
        """Get today's stats."""
        stats = load_json("pomodoro_stats.json", {})
        today = date.today().isoformat()
        
        today_stats = stats.get(today, {"count": 0, "total_minutes": 0})
        
        # Calculate streak
        streak = 0
        from datetime import datetime, timedelta
        check_date = date.today()
        while True:
            check_str = check_date.isoformat()
            if check_str in stats and stats[check_str].get("count", 0) > 0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        return {
            "today_completed": today_stats.get("count", 0),
            "today_minutes": today_stats.get("total_minutes", 0),
            "streak": streak
        }


class PomodoroScreen(Static):
    """Pomodoro timer screen."""
    
    DEFAULT_CSS = """
    PomodoroScreen {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    PomodoroScreen .header {
        height: 3;
        content-align: center middle;
        text-style: bold;
        color: $primary;
    }
    
    PomodoroScreen .timer-container {
        height: 40%;
        content-align: center middle;
    }
    
    PomodoroScreen .timer-display {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding: 2 0;
    }
    
    PomodoroScreen .timer-display.running {
        color: $success;
    }
    
    PomodoroScreen .timer-display.paused {
        color: $warning;
    }
    
    PomodoroScreen .controls {
        height: auto;
        content-align: center middle;
        margin: 1 0;
    }
    
    PomodoroScreen .control-btn {
        margin: 0 1;
        min-width: 12;
    }
    
    PomodoroScreen .progress-container {
        height: auto;
        padding: 0 10;
        margin: 1 0;
    }
    
    PomodoroScreen .stats-container {
        height: 30%;
        border: solid $primary-darken-2;
        padding: 1;
    }
    
    PomodoroScreen .stats-header {
        text-style: bold;
        color: $primary;
        text-align: center;
    }
    
    PomodoroScreen .stats-grid {
        layout: grid;
        grid-size: 3;
        grid-gutter: 1;
        margin-top: 1;
    }
    
    PomodoroScreen .stat-item {
        text-align: center;
        padding: 1;
        border: solid $surface-darken-1;
    }
    
    PomodoroScreen .stat-value {
        text-style: bold;
        color: $success;
        text-align: center;
    }
    
    PomodoroScreen .stat-label {
        color: $text-muted;
        text-align: center;
    }
    
    PomodoroScreen .duration-selector {
        height: auto;
        content-align: center middle;
        margin: 1 0;
    }
    
    PomodoroScreen .duration-btn {
        margin: 0 1;
    }
    """
    
    time_remaining = reactive(25 * 60)  # seconds
    is_running = reactive(False)
    total_time = reactive(25 * 60)
    
    def __init__(self):
        super().__init__()
        self.pomodoro = PomodoroTimer()
        self.timer: Timer | None = None
        self.selected_duration = 25
    
    def compose(self) -> ComposeResult:
        yield Label("🍅 番茄钟", classes="header")
        
        with Horizontal(classes="duration-selector"):
            yield Button("15分钟", id="dur-15", classes="duration-btn")
            yield Button("25分钟", id="dur-25", classes="duration-btn", variant="primary")
            yield Button("45分钟", id="dur-45", classes="duration-btn")
            yield Button("60分钟", id="dur-60", classes="duration-btn")
        
        with Center(classes="timer-container"):
            yield Label("25:00", id="timer-display", classes="timer-display")
        
        with Horizontal(classes="progress-container"):
            yield ProgressBar(total=100, id="progress-bar", show_percentage=False)
        
        with Horizontal(classes="controls"):
            yield Button("▶️ 开始", id="start-btn", classes="control-btn", variant="success")
            yield Button("⏸️ 暂停", id="pause-btn", classes="control-btn", variant="warning")
            yield Button("⏹️ 重置", id="reset-btn", classes="control-btn", variant="error")
        
        with Vertical(classes="stats-container"):
            yield Label("📊 今日统计", classes="stats-header")
            with Horizontal(classes="stats-grid"):
                with Vertical(classes="stat-item"):
                    yield Label("0", id="stat-completed", classes="stat-value")
                    yield Label("完成次数", classes="stat-label")
                with Vertical(classes="stat-item"):
                    yield Label("0", id="stat-minutes", classes="stat-value")
                    yield Label("专注分钟", classes="stat-label")
                with Vertical(classes="stat-item"):
                    yield Label("0", id="stat-streak", classes="stat-value")
                    yield Label("连续天数", classes="stat-label")
    
    def on_mount(self) -> None:
        """Initialize on mount."""
        self.update_timer_display()
        self.update_stats()
    
    def watch_time_remaining(self, time_remaining: int) -> None:
        """Update display when time changes."""
        self.update_timer_display()
        self.update_progress()
    
    def watch_is_running(self, is_running: bool) -> None:
        """Update display when running state changes."""
        display = self.query_one("#timer-display", Label)
        if is_running:
            display.add_class("running")
            display.remove_class("paused")
        else:
            display.remove_class("running")
            if self.time_remaining < self.total_time:
                display.add_class("paused")
    
    def update_timer_display(self) -> None:
        """Update the timer display."""
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        display = self.query_one("#timer-display", Label)
        display.update(f"{minutes:02d}:{seconds:02d}")
    
    def update_progress(self) -> None:
        """Update progress bar."""
        progress = self.query_one("#progress-bar", ProgressBar)
        percentage = (self.total_time - self.time_remaining) / self.total_time * 100
        progress.update(progress=percentage)
    
    def update_stats(self) -> None:
        """Update statistics display."""
        stats = self.pomodoro.get_stats()
        
        self.query_one("#stat-completed", Label).update(str(stats.get("today_completed", 0)))
        self.query_one("#stat-minutes", Label).update(str(stats.get("today_minutes", 0)))
        self.query_one("#stat-streak", Label).update(str(stats.get("streak", 0)))
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "start-btn":
            self.start_timer()
        elif button_id == "pause-btn":
            self.pause_timer()
        elif button_id == "reset-btn":
            self.reset_timer()
        elif button_id == "dur-15":
            self.set_duration(15)
        elif button_id == "dur-25":
            self.set_duration(25)
        elif button_id == "dur-45":
            self.set_duration(45)
        elif button_id == "dur-60":
            self.set_duration(60)
    
    def set_duration(self, minutes: int) -> None:
        """Set timer duration."""
        if self.is_running:
            self.notify("请先暂停或重置当前计时", severity="warning")
            return
        
        self.selected_duration = minutes
        self.total_time = minutes * 60
        self.time_remaining = self.total_time
        
        # Update button styles
        for dur in [15, 25, 45, 60]:
            btn = self.query_one(f"#dur-{dur}", Button)
            if dur == minutes:
                btn.variant = "primary"
            else:
                btn.variant = "default"
    
    def start_timer(self) -> None:
        """Start the timer."""
        if self.is_running:
            return
        
        self.is_running = True
        self.timer = self.set_interval(1, self.tick)
        self.notify("番茄钟开始！专注时间到 🍅", severity="success")
    
    def pause_timer(self) -> None:
        """Pause the timer."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.timer:
            self.timer.stop()
        self.notify("番茄钟已暂停", severity="warning")
    
    def reset_timer(self) -> None:
        """Reset the timer."""
        self.is_running = False
        if self.timer:
            self.timer.stop()
        self.time_remaining = self.total_time
        self.notify("番茄钟已重置", severity="information")
    
    def tick(self) -> None:
        """Timer tick handler."""
        if self.time_remaining > 0:
            self.time_remaining -= 1
        else:
            self.timer_complete()
    
    def timer_complete(self) -> None:
        """Handle timer completion."""
        self.is_running = False
        if self.timer:
            self.timer.stop()
        
        # Record completion
        self.pomodoro.record_session(self.selected_duration)
        self.update_stats()
        
        self.notify(
            f"🎉 番茄钟完成！专注了 {self.selected_duration} 分钟",
            severity="success",
            timeout=10
        )
