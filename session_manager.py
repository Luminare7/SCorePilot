# session_manager.py

from datetime import datetime, timedelta
import threading
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)

class AnalysisSession:
    def __init__(self, analyzer, created_at=None):
        self.analyzer = analyzer
        self.created_at = created_at or datetime.now()
        self.last_accessed = self.created_at

    def touch(self):
        """Update last accessed time"""
        self.last_accessed = datetime.now()

class SessionManager:
    def __init__(self, max_sessions=100, session_timeout_minutes=30):
        self.sessions = OrderedDict()
        self.max_sessions = max_sessions
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.lock = threading.Lock()

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def create_session(self, analyzer):
        """Create a new session for an analyzer"""
        with self.lock:
            # Generate session ID
            session_id = self._generate_session_id()

            # Create session
            session = AnalysisSession(analyzer)

            # Remove oldest session if we're at capacity
            if len(self.sessions) >= self.max_sessions:
                oldest_key = next(iter(self.sessions))
                del self.sessions[oldest_key]

            # Store new session
            self.sessions[session_id] = session
            return session_id

    def get_analyzer(self, session_id):
        """Get analyzer for a session"""
        with self.lock:
            session = self.sessions.get(session_id)
            if session:
                session.touch()
                return session.analyzer
            return None

    def remove_session(self, session_id):
        """Remove a session"""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]

    def _cleanup_loop(self):
        """Periodically clean up expired sessions"""
        while True:
            self._cleanup_expired_sessions()
            threading.Event().wait(300)  # Run every 5 minutes

    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        with self.lock:
            current_time = datetime.now()
            expired = [
                sid for sid, session in self.sessions.items()
                if (current_time - session.last_accessed) > self.session_timeout
            ]
            for sid in expired:
                del self.sessions[sid]

    def _generate_session_id(self):
        """Generate a unique session ID"""
        import uuid
        return str(uuid.uuid4())