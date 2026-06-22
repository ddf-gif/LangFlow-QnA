"""会话管理服务。"""
from typing import Dict


class SessionManager:
    """简单的内存会话管理器。生产环境应使用 Redis 或数据库。"""

    def __init__(self):
        self._sessions: Dict[str, dict] = {}

    def get_or_create(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            self._sessions[session_id] = {"session_id": session_id, "message_count": 0}
        return self._sessions[session_id]

    def increment_count(self, session_id: str):
        session = self.get_or_create(session_id)
        session["message_count"] += 1

    def get_count(self, session_id: str) -> int:
        session = self.get_or_create(session_id)
        return session["message_count"]

    def total_count(self) -> int:
        """所有会话的消息总数（供数据看板统计使用）。"""
        return sum(s.get("message_count", 0) for s in self._sessions.values())

    def all_sessions(self) -> dict:
        """返回全部会话（调试 / 统计用）。"""
        return dict(self._sessions)


session_manager = SessionManager()
