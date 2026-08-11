"""审计日志（SPEC M9）：哈希链追加写入与整链校验。

每条记录含 prev_hash；record_hash = sha256(prev_hash + canonical_payload)。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ..errors import AuditChainError
from ..schemas import AuditLogRecord

GENESIS_HASH = "0" * 64


def sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical(obj: object) -> str:
    """规范序列化（用于 digest）。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)


class AuditLogger:
    """向 audit_log.jsonl 追加哈希链记录（线程不保证，单进程顺序写）。"""

    def __init__(self, path: str | Path, run_mode: str = "mock") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_mode = run_mode
        self._seq, self._prev = self._load_tail()

    def _load_tail(self) -> tuple[int, str]:
        if not self.path.exists():
            return 0, GENESIS_HASH
        last = None
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = json.loads(line)
        if last is None:
            return 0, GENESIS_HASH
        return int(last["seq"]) + 1, last["record_hash"]

    def log(self, stage: str, input_payload: object, output_payload: object) -> AuditLogRecord:
        payload = {
            "seq": self._seq,
            "stage": stage,
            "run_mode": self.run_mode,
            "input_digest": sha256_hex(canonical(input_payload)),
            "output_digest": sha256_hex(canonical(output_payload)),
        }
        record = AuditLogRecord(
            seq=self._seq,
            timestamp=datetime.now(timezone.utc),
            stage=stage,
            run_mode=self.run_mode,  # type: ignore[arg-type]
            input_digest=payload["input_digest"],
            output_digest=payload["output_digest"],
            prev_hash=self._prev,
            record_hash=AuditLogRecord.compute_hash(self._prev, canonical(payload)),
        )
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")
        self._seq += 1
        self._prev = record.record_hash
        return record


def verify_chain(path: str | Path) -> bool:
    """校验整链：prev_hash 衔接与 record_hash 重算一致。"""
    prev = GENESIS_HASH
    p = Path(path)
    if not p.exists():
        return False
    with open(p, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["prev_hash"] != prev:
                raise AuditChainError(
                    f"链断裂于 seq={rec['seq']}", code="AUDIT_CHAIN_BROKEN", context={"seq": rec["seq"]}
                )
            payload = {
                "seq": rec["seq"],
                "stage": rec["stage"],
                "run_mode": rec["run_mode"],
                "input_digest": rec["input_digest"],
                "output_digest": rec["output_digest"],
            }
            if AuditLogRecord.compute_hash(prev, canonical(payload)) != rec["record_hash"]:
                raise AuditChainError(
                    f"哈希不一致于 seq={rec['seq']}", code="AUDIT_HASH_MISMATCH", context={"seq": rec["seq"]}
                )
            prev = rec["record_hash"]
    return True
