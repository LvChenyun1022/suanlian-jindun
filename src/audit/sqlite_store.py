"""SQLite append-only 审计日志（SPEC M9）。

- 触发器禁止 UPDATE/DELETE（append-only）；
- 每条记录含 prev_hash，record_hash = sha256(prev_hash + 规范序列化载荷)，防篡改链；
- 记录类型：stage（环节进出）、tool_call、llm_call（含 token 数）、guardrail（拦截）、manual_op；
- 支持按案件导出 JSONL。
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..errors import AuditChainError
from . import GENESIS_HASH, canonical, sha256_hex

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    case_id TEXT,
    stage TEXT NOT NULL,
    event_type TEXT NOT NULL,
    run_mode TEXT NOT NULL,
    input_digest TEXT,
    output_digest TEXT,
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    detail TEXT,
    prev_hash TEXT NOT NULL,
    record_hash TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
"""

_COLS = ("ts", "case_id", "stage", "event_type", "run_mode",
         "input_digest", "output_digest", "tokens_prompt", "tokens_completion", "detail")


class SqliteAuditStore:
    """SQLite 审计存储（append-only + 哈希链）。"""

    def __init__(self, path: str | Path, run_mode: str = "mock") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_mode = run_mode
        self._conn = sqlite3.connect(str(self.path))
        self._conn.executescript(_SCHEMA)
        self._prev = self._tail_hash()

    def _tail_hash(self) -> str:
        row = self._conn.execute(
            "SELECT record_hash FROM audit_log ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else GENESIS_HASH

    def log(
        self,
        stage: str,
        input_payload: object = None,
        output_payload: object = None,
        *,
        case_id: str | None = None,
        event_type: str = "stage",
        tokens_prompt: int | None = None,
        tokens_completion: int | None = None,
        detail: str = "",
    ) -> str:
        """追加一条审计记录，返回 record_hash。"""
        payload = {
            "case_id": case_id,
            "stage": stage,
            "event_type": event_type,
            "run_mode": self.run_mode,
            "input_digest": sha256_hex(canonical(input_payload)) if input_payload is not None else None,
            "output_digest": sha256_hex(canonical(output_payload)) if output_payload is not None else None,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "detail": detail,
        }
        record_hash = sha256_hex(self._prev + canonical(payload))
        self._conn.execute(
            f"INSERT INTO audit_log ({', '.join(_COLS)}, prev_hash, record_hash)"
            f" VALUES ({', '.join('?' * len(_COLS))}, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                case_id, stage, event_type, self.run_mode,
                payload["input_digest"], payload["output_digest"],
                tokens_prompt, tokens_completion, detail,
                self._prev, record_hash,
            ),
        )
        self._conn.commit()
        self._prev = record_hash
        return record_hash

    def verify_chain(self) -> bool:
        """整链校验：prev_hash 衔接 + record_hash 重算一致。"""
        prev = GENESIS_HASH
        rows = self._conn.execute(
            f"SELECT seq, {', '.join(_COLS[1:])}, prev_hash, record_hash"
            " FROM audit_log ORDER BY seq"
        )
        for row in rows:
            (seq, case_id, stage, event_type, run_mode, in_d, out_d,
             tok_p, tok_c, detail, prev_hash, record_hash) = row
            if prev_hash != prev:
                raise AuditChainError(f"链断裂于 seq={seq}", code="AUDIT_CHAIN_BROKEN",
                                      context={"seq": seq})
            payload = {
                "case_id": case_id, "stage": stage, "event_type": event_type,
                "run_mode": run_mode, "input_digest": in_d, "output_digest": out_d,
                "tokens_prompt": tok_p, "tokens_completion": tok_c, "detail": detail,
            }
            if sha256_hex(prev + canonical(payload)) != record_hash:
                raise AuditChainError(f"哈希不一致于 seq={seq}", code="AUDIT_HASH_MISMATCH",
                                      context={"seq": seq})
            prev = record_hash
        return True

    def export_case_jsonl(self, case_id: str, out_path: str | Path) -> int:
        """按案件导出 JSONL，返回记录数。"""
        rows = self._case_rows(case_id)
        cols = [d[0] for d in self._conn.execute("SELECT * FROM audit_log LIMIT 0").description]
        with open(out_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(dict(zip(cols, row)), ensure_ascii=False) + "\n")
        return len(rows)

    def _case_rows(self, case_id: str) -> list[tuple]:
        return self._conn.execute(
            "SELECT * FROM audit_log WHERE case_id = ? ORDER BY seq", (case_id,)
        ).fetchall()

    def list_case_events(self, case_id: str) -> list[dict]:
        """按案件读取审计事件（时间线展示用）。"""
        cols = [d[0] for d in self._conn.execute("SELECT * FROM audit_log LIMIT 0").description]
        return [dict(zip(cols, row)) for row in self._case_rows(case_id)]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    def close(self) -> None:
        self._conn.close()
