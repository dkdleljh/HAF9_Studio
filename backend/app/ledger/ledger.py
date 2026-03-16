"""포렌식 원장 및 리플레이 엔진."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import uuid


class EventType(str, Enum):
    """이벤트 유형"""

    INTENT_RECEIVED = "INTENT_RECEIVED"
    INTENT_PARSED = "INTENT_PARSED"
    DSL_GENERATED = "DSL_GENERATED"
    IR_COMPILED = "IR_COMPILED"
    PATCHES_GENERATED = "PATCHES_GENERATED"
    SAFETY_DECISION = "SAFETY_DECISION"
    PATCH_APPLIED = "PATCH_APPLIED"
    PATCH_REJECTED = "PATCH_REJECTED"
    METRICS_BEFORE = "METRICS_BEFORE"
    METRICS_AFTER = "METRICS_AFTER"
    ROLLBACK_EXECUTED = "ROLLBACK_EXECUTED"
    STATE_SNAPSHOT = "STATE_SNAPSHOT"


@dataclass
class LedgerEntry:
    """원장 항목"""

    event_id: str
    timestamp: datetime
    event_type: EventType
    related_entity_ids: list[str] = field(default_factory=list)
    explanation: str = ""
    version_metadata: dict = field(default_factory=dict)
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """사전으로 변환"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "related_entity_ids": self.related_entity_ids,
            "explanation": self.explanation,
            "version_metadata": self.version_metadata,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict) -> LedgerEntry:
        """사전에서 생성"""
        return cls(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=EventType(data["event_type"]),
            related_entity_ids=data.get("related_entity_ids", []),
            explanation=data.get("explanation", ""),
            version_metadata=data.get("version_metadata", {}),
            payload=data.get("payload", {}),
        )


class ForensicLedger:
    """추가 전용 이벤트 원장"""

    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path
        self.entries: list[LedgerEntry] = []
        self._session_id = str(uuid.uuid4())

    def log(
        self,
        event_type: EventType,
        explanation: str,
        related_entity_ids: list[str] | None = None,
        payload: dict | None = None,
        version_metadata: dict | None = None,
    ) -> LedgerEntry:
        """이벤트를 로깅합니다."""
        entry = LedgerEntry(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            related_entity_ids=related_entity_ids or [],
            explanation=explanation,
            version_metadata=version_metadata or {"version": "1.0"},
            payload=payload or {},
        )

        self.entries.append(entry)

        # 파일에 저장
        if self.storage_path:
            self._save_to_file(entry)

        return entry

    def log_intent_received(self, raw_text: str) -> LedgerEntry:
        """인텐트 수신 로깅"""
        return self.log(
            event_type=EventType.INTENT_RECEIVED,
            explanation=f"인텐트 수신: {raw_text[:100]}...",
            payload={"raw_text": raw_text},
        )

    def log_intent_parsed(self, intent_id: str, parsed_data: dict) -> LedgerEntry:
        """인텐트 파싱 로깅"""
        return self.log(
            event_type=EventType.INTENT_PARSED,
            explanation=f"인텐트 파싱 완료: {intent_id}",
            related_entity_ids=[intent_id],
            payload=parsed_data,
        )

    def log_dsl_generated(self, dsl_id: str, dsl_data: dict) -> LedgerEntry:
        """DSL 생성 로깅"""
        return self.log(
            event_type=EventType.DSL_GENERATED,
            explanation=f"DSL 생성 완료: {dsl_id}",
            related_entity_ids=[dsl_id],
            payload=dsl_data,
        )

    def log_ir_compiled(self, ir_id: str, ir_data: dict) -> LedgerEntry:
        """IR 컴파일 로깅"""
        return self.log(
            event_type=EventType.IR_COMPILED,
            explanation=f"IR 컴파일 완료: {ir_id}",
            related_entity_ids=[ir_id],
            payload=ir_data,
        )

    def log_patches_generated(
        self, patch_ids: list[str], patches_data: list[dict]
    ) -> LedgerEntry:
        """패치 생성 로깅"""
        return self.log(
            event_type=EventType.PATCHES_GENERATED,
            explanation=f"{len(patch_ids)}개의 패치 후보 생성",
            related_entity_ids=patch_ids,
            payload={"patches": patches_data},
        )

    def log_safety_decision(
        self, patch_id: str, decision: str, explanation: str
    ) -> LedgerEntry:
        """안전성 결정 로깅"""
        return self.log(
            event_type=EventType.SAFETY_DECISION,
            explanation=f"안전성 결정: {decision} - {explanation}",
            related_entity_ids=[patch_id],
            payload={"decision": decision, "explanation": explanation},
        )

    def log_patch_applied(
        self, patch_id: str, metrics_before: dict, metrics_after: dict
    ) -> LedgerEntry:
        """패치 적용 로깅"""
        return self.log(
            event_type=EventType.PATCH_APPLIED,
            explanation=f"패치 적용 완료: {patch_id}",
            related_entity_ids=[patch_id],
            payload={
                "metrics_before": metrics_before,
                "metrics_after": metrics_after,
            },
        )

    def log_metrics(self, metrics: dict, before_or_after: str) -> LedgerEntry:
        """메트릭 로깅"""
        event_type = (
            EventType.METRICS_BEFORE
            if before_or_after == "before"
            else EventType.METRICS_AFTER
        )
        return self.log(
            event_type=event_type,
            explanation=f"메트릭 ({before_or_after})",
            payload=metrics,
        )

    def log_rollback(self, patch_id: str, reason: str) -> LedgerEntry:
        """롤백 로깅"""
        return self.log(
            event_type=EventType.ROLLBACK_EXECUTED,
            explanation=f"롤백 실행: {patch_id} - {reason}",
            related_entity_ids=[patch_id],
            payload={"reason": reason},
        )

    def _save_to_file(self, entry: LedgerEntry) -> None:
        """파일에 저장"""
        if not self.storage_path:
            return

        path = Path(self.storage_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def get_entries(
        self,
        event_type: EventType | None = None,
        entity_id: str | None = None,
    ) -> list[LedgerEntry]:
        """항목 조회"""
        results = self.entries

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if entity_id:
            results = [e for e in results if entity_id in e.related_entity_ids]

        return results

    def export_to_json(self) -> str:
        """JSON으로 내보내기"""
        return json.dumps(
            [e.to_dict() for e in self.entries],
            ensure_ascii=False,
            indent=2,
        )

    def get_session_id(self) -> str:
        """세션 ID 반환"""
        return self._session_id

    def clear(self) -> None:
        """원장 초기화"""
        self.entries.clear()
        self._session_id = str(uuid.uuid4())


class ReplayEngine:
    """리플레이 엔진"""

    def __init__(self, ledger: ForensicLedger):
        self.ledger = ledger

    def get_timeline(self) -> list[dict]:
        """타임라인 조회"""
        timeline = []
        for entry in self.ledger.entries:
            timeline.append(
                {
                    "event_id": entry.event_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "event_type": entry.event_type.value,
                    "explanation": entry.explanation,
                    "related_entities": entry.related_entity_ids,
                }
            )
        return timeline

    def get_event_by_id(self, event_id: str) -> LedgerEntry | None:
        """이벤트 조회"""
        for entry in self.ledger.entries:
            if entry.event_id == event_id:
                return entry
        return None

    def get_events_by_type(self, event_type: EventType) -> list[LedgerEntry]:
        """유형별 이벤트 조회"""
        return self.ledger.get_entries(event_type=event_type)

    def get_state_at_event(self, event_id: str) -> dict | None:
        """이벤트 시점의 상태 조회"""
        event = self.get_event_by_id(event_id)
        if not event:
            return None

        # 관련 상태 스냅샷 찾기
        for entry in self.ledger.entries:
            if entry.event_type == EventType.STATE_SNAPSHOT:
                if entry.timestamp <= event.timestamp:
                    return entry.payload

        return None

    def replay_from_event(self, start_event_id: str) -> list[LedgerEntry]:
        """시작점부터 리플레이"""
        start_idx = None
        for i, entry in enumerate(self.ledger.entries):
            if entry.event_id == start_event_id:
                start_idx = i
                break

        if start_idx is None:
            return []

        return self.ledger.entries[start_idx:]

    def get_patch_history(self, patch_id: str) -> list[LedgerEntry]:
        """패치 히스토리 조회"""
        return self.ledger.get_entries(entity_id=patch_id)

    def get_metrics_progression(self) -> list[dict]:
        """메트릭 변화 추이"""
        progression = []

        for entry in self.ledger.entries:
            if entry.event_type in (EventType.METRICS_BEFORE, EventType.METRICS_AFTER):
                progression.append(
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "type": entry.event_type.value,
                        "metrics": entry.payload,
                    }
                )

        return progression
