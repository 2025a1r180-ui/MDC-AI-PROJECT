"""
Rate Limiting Module for Echo Journal (Milestone 6: Production Hardening).

Implements a thread-safe sliding window rate limiter to protect authentication
endpoints (login, registration) from brute force attacks and credential stuffing.
"""

import time
import threading
from typing import Dict, List, Tuple


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.
    Tracks timestamps of requests for each client key (e.g. IP address or username).
    """

    def __init__(self, max_requests: int = 5, window_seconds: int = 300):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def _cleanup(self, now: float, key: str) -> None:
        """Removes entries older than window_seconds."""
        cutoff = now - self.window_seconds
        self.history[key] = [t for t in self.history.get(key, []) if t > cutoff]
        if not self.history[key]:
            self.history.pop(key, None)

    def is_rate_limited(self, key: str) -> Tuple[bool, int]:
        """
        Checks whether the key is currently rate-limited.
        Returns (is_limited, retry_after_seconds).
        """
        with self.lock:
            now = time.time()
            self._cleanup(now, key)
            attempts = self.history.get(key, [])
            if len(attempts) >= self.max_requests:
                oldest = attempts[0]
                retry_after = max(1, int(oldest + self.window_seconds - now))
                return True, retry_after
            return False, 0

    def record_attempt(self, key: str) -> Tuple[bool, int]:
        """
        Records an attempt.
        If allowed, returns (True, 0).
        If rate limited, returns (False, retry_after_seconds).
        """
        with self.lock:
            now = time.time()
            self._cleanup(now, key)
            attempts = self.history.get(key, [])
            if len(attempts) >= self.max_requests:
                oldest = attempts[0]
                retry_after = max(1, int(oldest + self.window_seconds - now))
                return False, retry_after
            
            # Record current attempt
            if key not in self.history:
                self.history[key] = []
            self.history[key].append(now)
            return True, 0

    def reset(self, key: str) -> None:
        """Resets the history for a given key upon successful authentication."""
        with self.lock:
            self.history.pop(key, None)


# Default global instances for authentication endpoints
login_rate_limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=300)
registration_rate_limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=300)
