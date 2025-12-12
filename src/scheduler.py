"""
Scheduler module for periodic incremental synchronization.
"""
import threading
import time
from typing import Optional
from datetime import datetime
from src.sync_engine import SyncEngine


class Scheduler:
    """Scheduler for running periodic incremental sync operations."""
    
    def __init__(self, sync_engine: SyncEngine, interval_seconds: int):
        """
        Initialize the Scheduler.
        
        Args:
            sync_engine: SyncEngine instance to use for synchronization
            interval_seconds: Interval in seconds between sync executions
        """
        self.sync_engine = sync_engine
        self.interval_seconds = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the scheduler and wait for the thread to finish."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
    
    def is_running(self) -> bool:
        """Check if scheduler is currently running."""
        return self._running
    
    def _run(self):
        """Internal method that runs in the background thread."""
        while self._running and not self._stop_event.is_set():
            # Execute incremental sync
            self.sync_engine.incremental_sync()
            
            # Wait for the specified interval or until stop is requested
            self._stop_event.wait(timeout=self.interval_seconds)


class CronScheduler:
    """Scheduler that uses cron expressions to determine execution times."""
    
    def __init__(self, cron_expression: str):
        """
        Initialize the CronScheduler.
        
        Args:
            cron_expression: Cron expression (e.g., "*/5 * * * *" for every 5 minutes)
        """
        self.cron_expression = cron_expression
        self._parse_cron_expression()
    
    def _parse_cron_expression(self):
        """Parse the cron expression into its components."""
        parts = self.cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {self.cron_expression}")
        
        self.minute = parts[0]
        self.hour = parts[1]
        self.day = parts[2]
        self.month = parts[3]
        self.weekday = parts[4]
    
    def get_next_run_time(self) -> datetime:
        """
        Calculate the next execution time based on the cron expression.
        
        Returns:
            datetime: The next scheduled execution time
        """
        now = datetime.now()
        
        # Simple implementation for */N minute patterns
        if self.minute.startswith("*/"):
            interval = int(self.minute[2:])
            current_minute = now.minute
            next_minute = ((current_minute // interval) + 1) * interval
            
            if next_minute >= 60:
                # Move to next hour
                next_run = now.replace(minute=0, second=0, microsecond=0)
                next_run = next_run.replace(hour=now.hour + 1)
            else:
                next_run = now.replace(minute=next_minute, second=0, microsecond=0)
            
            return next_run
        
        # For other patterns, return next minute as a simple fallback
        next_run = now.replace(second=0, microsecond=0)
        next_run = next_run.replace(minute=now.minute + 1)
        return next_run
