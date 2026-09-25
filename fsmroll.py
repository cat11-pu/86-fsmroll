"""fsmroll.py：状态机（版本化迁移、存档回滚、事件缓存、快照恢复）。"""
from __future__ import annotations

import json
import os


class Machine:
    def __init__(self, version: int = 1, snapshot_path: str = "fsmroll.snapshot.json"):
        self.version = version
        self.state = "init"
        self.history = []
        self.migrations = 0
        self.rollbacks = 0
        self.pending = []
        self.archives = []
        self.migrating = False
        self.snapshot_path = snapshot_path

    def fire(self, event: str) -> dict:
        """迁移期间事件进 pending 缓存，否则直接改状态并记历史。"""
        if self.migrating:
            self.pending.append(event)
        else:
            self.state = event
            self.history.append(event)
        return {"state": self.state, "version": self.version}

    def migrate(self, target: int, fail: bool = False) -> dict:
        """迁移前存档；fail 为真时迁移失败，状态与版本保持原样。"""
        self._archive()
        self.migrations += 1
        if fail:
            self.migrating = True
        else:
            self.version = max(self.version, int(target))
            self.migrating = False
            self._flush_pending()
        return {"state": self.state, "version": self.version, "rolled_back": False}

    def rollback(self) -> dict:
        """回滚到最近一次存档（版本、状态、历史），并补齐缓存事件。"""
        rolled_back = False
        if self.archives:
            archive = self.archives.pop()
            self.version = archive["version"]
            self.state = archive["state"]
            tail = self.history[len(archive["history"]):]
            self.history = list(archive["history"]) + tail
            self.rollbacks += 1
            rolled_back = True
        self.migrating = False
        self._flush_pending()
        return {"state": self.state, "version": self.version, "rolled_back": rolled_back}

    def persist(self) -> bytes:
        """快照落盘，返回快照字节。"""
        blob = json.dumps({
            "version": self.version,
            "state": self.state,
            "history": self.history,
            "migrations": self.migrations,
            "rollbacks": self.rollbacks,
            "pending": self.pending,
            "archives": self.archives,
            "migrating": self.migrating,
        }).encode()
        with open(self.snapshot_path, "wb") as handle:
            handle.write(blob)
        return blob

    def restore(self, blob: bytes = None) -> dict:
        """从快照恢复；blob 为空时读落盘文件。"""
        if blob is None:
            with open(self.snapshot_path, "rb") as handle:
                blob = handle.read()
        data = json.loads(blob.decode() if isinstance(blob, bytes) else blob)
        self.version = data["version"]
        self.state = data["state"]
        self.history = list(data["history"])
        self.migrations = data["migrations"]
        self.rollbacks = data["rollbacks"]
        self.pending = list(data["pending"])
        self.archives = [dict(item, history=list(item["history"])) for item in data["archives"]]
        self.migrating = data["migrating"]
        return self.stats()

    def recover(self) -> dict:
        """模拟重启恢复：有落盘快照则恢复，否则保持现状。"""
        if os.path.exists(self.snapshot_path):
            return self.restore()
        return self.stats()

    def stats(self) -> dict:
        return {"version": self.version, "state": self.state, "migrations": self.migrations,
                "rollbacks": self.rollbacks, "history": list(self.history),
                "pending": len(self.pending)}

    def _archive(self) -> None:
        self.archives.append({"version": self.version, "state": self.state,
                              "history": list(self.history)})

    def _flush_pending(self) -> None:
        for event in self.pending:
            self.state = event
            self.history.append(event)
        self.pending = []
