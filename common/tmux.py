from threading import Lock

import libtmux
import streamlit as st


class TmuxServer:
    """A singleton class to manage a tmux server instance."""

    _instance: libtmux.Server | None = None
    _lock: Lock = Lock()

    @classmethod
    @st.cache_resource
    def get_instance(cls) -> libtmux.Server:
        """Retrieve the singleton tmux server instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = libtmux.Server()
            return cls._instance

    def clear_all(self) -> None:
        """Kill all tmux sessions associated with the server instance."""
        if self._instance:
            for session in self._instance.sessions:
                session.kill()


class TmuxSessionManager:
    """Handles tmux session lifecycle management."""

    def __init__(self) -> None:
        self.server = TmuxServer.get_instance()

    def get_session(self, session_name: str) -> libtmux.Session | None:
        """Retrieve a tmux session by name."""
        return next(
            (s for s in self.server.list_sessions() if s.name == session_name),
            None,
        )

    def create_session(self, session_name: str) -> libtmux.Session:
        """Create a new tmux session."""
        return self.server.new_session(
            session_name=session_name,
            detach=True,
            kill_session=True,
            history_limit=10000,
        )

    def close_session(self, session_name: str) -> None:
        """Close an existing tmux session."""
        session = self.get_session(session_name)
        if session:
            session.kill_session()

    def capture_output(self, session_name: str) -> str | None:
        """Capture pane output from a tmux session."""
        try:
            session = self.get_session(session_name)
            if not session:
                return None
            # Captures both stdout and stderr
            return "\n".join(session.active_pane.capture_pane(start=-10000))
        except libtmux.exc.LibTmuxException as e:
            st.error(f"Failed to capture tmux output: {e.__str__}")
            return None
