"""
Status tracking system for monitoring progress and displaying current process information.
"""

import asyncio
import threading
import time
from typing import Dict, Any, Optional, List, Callable, Generator
from dataclasses import dataclass
from datetime import datetime
import json
import sys
from enum import Enum


class TaskStatus(Enum):
    """Status enumeration for tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Information about a task."""
    id: str
    name: str
    status: TaskStatus
    progress: float = 0.0
    message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


class StatusTracker:
    """
    Centralized status tracking system for monitoring progress and displaying information.
    """
    
    def __init__(self, enable_real_time: bool = True, update_interval: float = 1.0):
        self.enable_real_time = enable_real_time
        self.update_interval = update_interval
        self.tasks: Dict[str, TaskInfo] = {}
        self.output_lines: List[str] = []
        self.max_output_lines = 1000
        self.current_operation = None
        self.operation_start_time = None
        self.callbacks: List[Callable] = []
        self.running = False
        self.update_thread = None
        
        # Terminal display settings
        self.show_progress = True
        self.show_file_changes = True
        self.show_git_output = True
        self.display_width = 80
        
    def start(self):
        """Start the status tracking system."""
        if self.running:
            return
        
        self.running = True
        
        if self.enable_real_time:
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
        
        self._log("Status tracking system started")
    
    def stop(self):
        """Stop the status tracking system."""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
        
        self._log("Status tracking system stopped")
    
    def create_task(self, task_id: str, name: str, message: str = "") -> TaskInfo:
        """Create a new task for tracking."""
        task = TaskInfo(
            id=task_id,
            name=name,
            status=TaskStatus.PENDING,
            message=message
        )
        
        self.tasks[task_id] = task
        self._notify_callbacks("task_created", task)
        return task
    
    def start_task(self, task_id: str, message: str = "") -> bool:
        """Start a task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        task.message = message or task.message
        
        self._notify_callbacks("task_started", task)
        return True
    
    def update_task(self, task_id: str, progress: float = None, message: str = None) -> bool:
        """Update a task's progress and message."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if progress is not None:
            task.progress = max(0.0, min(100.0, progress))
        
        if message is not None:
            task.message = message
        
        self._notify_callbacks("task_updated", task)
        return True
    
    def complete_task(self, task_id: str, message: str = "Completed") -> bool:
        """Mark a task as completed."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.progress = 100.0
        task.completed_at = datetime.now()
        task.message = message
        
        self._notify_callbacks("task_completed", task)
        return True
    
    def fail_task(self, task_id: str, error: str, message: str = "Failed") -> bool:
        """Mark a task as failed."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now()
        task.error = error
        task.message = message
        
        self._notify_callbacks("task_failed", task)
        return True
    
    def cancel_task(self, task_id: str, message: str = "Cancelled") -> bool:
        """Cancel a task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        task.message = message
        
        self._notify_callbacks("task_cancelled", task)
        return True
    
    def set_current_operation(self, operation: str):
        """Set the current operation being performed."""
        self.current_operation = operation
        self.operation_start_time = datetime.now()
        self._log(f"Starting operation: {operation}")
    
    def clear_current_operation(self):
        """Clear the current operation."""
        if self.current_operation:
            duration = datetime.now() - self.operation_start_time
            self._log(f"Completed operation: {self.current_operation} (took {duration.total_seconds():.2f}s)")
        
        self.current_operation = None
        self.operation_start_time = None
    
    def add_output_line(self, line: str, source: str = "system"):
        """Add a line of output (simplified - no terminal streaming)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_line = f"[{timestamp}] [{source}] {line}"
        
        # Just log to console instead of storing for streaming
        print(formatted_line)
        
        self._notify_callbacks("output_added", {"line": formatted_line, "source": source})
    
    def stream_git_output(self, lines: Generator[str, None, None], source: str = "git"):
        """Stream git command output."""
        for line in lines:
            if self.show_git_output:
                self.add_output_line(line, source)
    
    def add_callback(self, callback: Callable):
        """Add a callback for status updates."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current status."""
        task_counts = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for task in self.tasks.values():
            task_counts[task.status.value] += 1
        
        return {
            "current_operation": self.current_operation,
            "operation_duration": (datetime.now() - self.operation_start_time).total_seconds() if self.operation_start_time else 0,
            "task_counts": task_counts,
            "total_tasks": len(self.tasks),
            "output_lines": len(self.output_lines)
        }
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks as dictionaries."""
        return [task.to_dict() for task in self.tasks.values()]
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get currently active (running) tasks."""
        return [task.to_dict() for task in self.tasks.values() if task.status == TaskStatus.RUNNING]
    
    def get_recent_output(self, lines: int = 50) -> List[str]:
        """Get recent output lines."""
        return self.output_lines[-lines:] if lines > 0 else self.output_lines
    
    def clear_completed_tasks(self):
        """Clear completed and failed tasks."""
        self.tasks = {
            task_id: task for task_id, task in self.tasks.items()
            if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        }
        
        self._notify_callbacks("tasks_cleared", {})
    
    def clear_output(self):
        """Clear output lines."""
        self.output_lines.clear()
        self._notify_callbacks("output_cleared", {})
    
    def generate_progress_bar(self, task_id: str, width: int = 40) -> str:
        """Generate a progress bar for a task."""
        if task_id not in self.tasks:
            return ""
        
        task = self.tasks[task_id]
        progress = task.progress / 100.0
        filled_width = int(progress * width)
        
        bar = "█" * filled_width + "░" * (width - filled_width)
        percentage = f"{task.progress:.1f}%"
        
        return f"[{bar}] {percentage}"
    
    def display_status(self, clear_screen: bool = True):
        """Display current status in the terminal."""
        if clear_screen:
            self._clear_screen()
        
        print("=" * self.display_width)
        print("CHAMELEON STATUS TRACKER")
        print("=" * self.display_width)
        
        # Current operation
        if self.current_operation:
            duration = datetime.now() - self.operation_start_time
            print(f"Current Operation: {self.current_operation}")
            print(f"Duration: {duration.total_seconds():.1f}s")
            print("-" * self.display_width)
        
        # Task status
        if self.tasks:
            print("TASKS:")
            for task in self.tasks.values():
                status_icon = self._get_status_icon(task.status)
                print(f"{status_icon} {task.name}")
                
                if task.status == TaskStatus.RUNNING and self.show_progress:
                    progress_bar = self.generate_progress_bar(task.id)
                    print(f"  {progress_bar}")
                
                if task.message:
                    print(f"  {task.message}")
                
                if task.error:
                    print(f"  ERROR: {task.error}")
                
                print()
        
        # Recent output
        if self.output_lines and self.show_git_output:
            print("-" * self.display_width)
            print("RECENT OUTPUT:")
            recent_lines = self.get_recent_output(10)
            for line in recent_lines:
                print(line)
        
        print("=" * self.display_width)
    
    def _update_loop(self):
        """Main update loop for real-time display."""
        while self.running:
            try:
                if self.enable_real_time:
                    self.display_status()
                
                time.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self._log(f"Error in update loop: {e}")
    
    def _notify_callbacks(self, event_type: str, data: Any):
        """Notify all callbacks about an event."""
        for callback in self.callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                self._log(f"Error in callback: {e}")
    
    def _log(self, message: str):
        """Internal logging method."""
        self.add_output_line(message, "system")
    
    def _clear_screen(self):
        """Clear the terminal screen."""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def _get_status_icon(self, status: TaskStatus) -> str:
        """Get an icon for task status."""
        icons = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.RUNNING: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.CANCELLED: "🚫"
        }
        return icons.get(status, "❓")
    
    def export_status(self, format: str = "json") -> str:
        """Export current status to a string format."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_status_summary(),
            "tasks": self.get_all_tasks(),
            "recent_output": self.get_recent_output(50)
        }
        
        if format == "json":
            return json.dumps(data, indent=2)
        else:
            return str(data)
    
    def import_status(self, data: str, format: str = "json") -> bool:
        """Import status from a string format."""
        try:
            if format == "json":
                parsed_data = json.loads(data)
                
                # Restore tasks
                for task_data in parsed_data.get("tasks", []):
                    task = TaskInfo(
                        id=task_data["id"],
                        name=task_data["name"],
                        status=TaskStatus(task_data["status"]),
                        progress=task_data.get("progress", 0.0),
                        message=task_data.get("message", ""),
                        error=task_data.get("error")
                    )
                    
                    if task_data.get("started_at"):
                        task.started_at = datetime.fromisoformat(task_data["started_at"])
                    
                    if task_data.get("completed_at"):
                        task.completed_at = datetime.fromisoformat(task_data["completed_at"])
                    
                    self.tasks[task.id] = task
                
                # Restore output
                self.output_lines = parsed_data.get("recent_output", [])
                
                return True
            
        except Exception as e:
            self._log(f"Error importing status: {e}")
            return False
        
        return False


# Global status tracker instance
_global_tracker: Optional[StatusTracker] = None


def get_global_tracker() -> StatusTracker:
    """Get the global status tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = StatusTracker()
    return _global_tracker


def initialize_status_tracking(enable_real_time: bool = True, update_interval: float = 1.0):
    """Initialize the global status tracking system."""
    global _global_tracker
    _global_tracker = StatusTracker(enable_real_time, update_interval)
    _global_tracker.start()
    return _global_tracker


def cleanup_status_tracking():
    """Cleanup the global status tracking system."""
    global _global_tracker
    if _global_tracker:
        _global_tracker.stop()
        _global_tracker = None 