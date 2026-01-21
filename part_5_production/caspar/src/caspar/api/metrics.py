# Save as: src/caspar/api/metrics.py

"""
Simple metrics tracking for CASPAR.

In production, you'd use Prometheus, DataDog, or similar.
This simple implementation demonstrates the concepts.
"""

from datetime import datetime, timezone
from collections import defaultdict
import threading


class SimpleMetrics:
    """
    Thread-safe metrics collector.
    
    Why thread-safe? FastAPI handles multiple requests at once.
    Without locks, concurrent updates could corrupt our data.
    """
    
    def __init__(self):
        # Lock prevents race conditions when multiple requests update metrics
        self._lock = threading.Lock()
        
        # Counters track "how many times did X happen?"
        # defaultdict(int) means missing keys default to 0
        self._counters = defaultdict(int)
        
        # Latencies track "how long did X take?"
        # We store lists of measurements for each operation
        self._latencies = defaultdict(list)
        
        # Track when we started (for uptime calculation)
        self._started_at = datetime.now(timezone.utc)
    
    def increment(self, name: str, value: int = 1):
        """
        Increment a counter.
        
        Usage:
            metrics.increment("conversations_started")
            metrics.increment("messages_processed")
            metrics.increment("errors", 1)
        """
        with self._lock:  # Acquire lock before modifying
            self._counters[name] += value
        # Lock automatically released when we exit 'with' block
    
    def record_latency(self, name: str, seconds: float):
        """
        Record how long an operation took.
        
        Usage:
            start = time.time()
            do_something()
            metrics.record_latency("llm_call", time.time() - start)
        """
        with self._lock:
            self._latencies[name].append(seconds)
            
            # Keep only last 1000 measurements to prevent memory bloat
            # Older measurements "fall off" as new ones come in
            if len(self._latencies[name]) > 1000:
                self._latencies[name] = self._latencies[name][-1000:]
    
    def get_stats(self) -> dict:
        """
        Get current statistics.
        
        Returns a dictionary that can be serialized to JSON.
        """
        with self._lock:
            stats = {
                # How long has the server been running?
                "uptime_seconds": (
                    datetime.now(timezone.utc) - self._started_at
                ).total_seconds(),
                
                # All counter values
                "counters": dict(self._counters),
                
                # Latency statistics (calculated below)
                "latencies": {},
            }
            
            # Calculate latency statistics for each tracked operation
            for name, values in self._latencies.items():
                if values:
                    stats["latencies"][name] = {
                        "count": len(values),
                        "avg_ms": sum(values) * 1000 / len(values),
                        "max_ms": max(values) * 1000,
                        "min_ms": min(values) * 1000,
                    }
            
            return stats


# Create a single global instance
# All parts of the app use this same instance
metrics = SimpleMetrics()


def track_latency(name: str):
    """
    Decorator to automatically track function execution time.
    
    Usage:
        @track_latency("llm_call")
        async def call_llm():
            ...
    
    This will:
    - Track how long the function takes
    - Increment {name}_success on success
    - Increment {name}_error on failure
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = datetime.now(timezone.utc)
            try:
                result = await func(*args, **kwargs)
                metrics.increment(f"{name}_success")
                return result
            except Exception as e:
                metrics.increment(f"{name}_error")
                raise  # Re-raise the exception
            finally:
                # 'finally' runs whether success or failure
                elapsed = (datetime.now(timezone.utc) - start).total_seconds()
                metrics.record_latency(name, elapsed)
        return wrapper
    return decorator
