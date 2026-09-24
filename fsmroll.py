"""fsmroll.py：状态机（基线：内存字典，无版本无法回滚）。"""
from __future__ import annotations


class Machine:
    def __init__(self, version: int = 1):
        self.version = version
        self.state = "init"
        self.history = []
        self.migrations = 0
        self.rollbacks = 0
        self.pending = []

    def fire(self, event: str) -> dict:
        """基线：状态直接改，没版本也没迁移。"""
        self.state = event
        self.history.append(event)
        return {"state": self.state, "version": self.version}

    def migrate(self, target: int, fail: bool = False) -> dict:
        raise NotImplementedError("状态迁移还没实现")

    def rollback(self) -> dict:
        raise NotImplementedError("迁移回滚还没实现")

    def persist(self) -> bytes:
        raise NotImplementedError("快照还没实现")

    def restore(self, blob: bytes = None) -> dict:
        raise NotImplementedError("重启恢复还没实现")

    def stats(self) -> dict:
        return {"version": self.version, "state": self.state, "migrations": self.migrations,
                "rollbacks": self.rollbacks, "history": list(self.history),
                "pending": len(self.pending)}
