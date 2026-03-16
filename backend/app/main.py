"""FastAPI 백엔드 메인 애플리케이션."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.domain.spatial import (
    Cell,
    Corridor,
    Exit,
    Obstacle,
    SpatialState,
    Zone,
)
from app.ledger.ledger import EventType, ForensicLedger, ReplayEngine
from app.services.dsl_compiler import DSLCompiler, IRCompiler
from app.services.intent_parser import IntentInput, IntentParser
from app.services.patch_planner import PatchPlanner, SafetyVerifier
from app.simulation.grid import GridSimulation


# ============ Pydantic Models ============


class IntentRequest(BaseModel):
    """인텐트 요청"""

    text: str | None = None
    structured: dict | None = None


class PatchApplyRequest(BaseModel):
    """패치 적용 요청"""

    patch_id: str


class GridConfig(BaseModel):
    """그리드 구성"""

    width: int
    height: int
    zones: list[dict]
    exits: list[dict]
    obstacles: list[dict]


# ============ Application State ============


class AppState:
    """애플리케이션 상태"""

    def __init__(self):
        self.simulation = GridSimulation()
        self.ledger = ForensicLedger()
        self.replay_engine = ReplayEngine(self.ledger)
        self.intent_parser = IntentParser()
        self.dsl_compiler = DSLCompiler()
        self.ir_compiler = IRCompiler()
        self.patch_planner: PatchPlanner | None = None
        self.safety_verifier = SafetyVerifier()
        self.current_dsl: Any = None
        self.current_ir: Any = None
        self.current_candidates: list[Any] = []
        self.baseline_metrics: dict = {}


# ============ FastAPI App ============

# Global state instance
_state = AppState()


def get_app_state() -> AppState:
    """Get application state."""
    return _state


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 수명 주기"""
    # 기본 시나리오 로드
    _state.simulation.load_example_scenario()
    _state.baseline_metrics = _state.simulation.calculate_baseline_metrics()

    # 초기 상태 로깅
    _state.ledger.log(
        event_type=EventType.STATE_SNAPSHOT,
        explanation="초기 상태 스냅샷",
        payload=asdict(_state.simulation.get_state_snapshot()),
    )

    yield


app = FastAPI(
    title="HAF-9_Studio API",
    description="HAF-9 공간 운영 체제 백엔드 API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Routes ============


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": "HAF-9_Studio API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/api/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy"}


@app.post("/api/simulation/configure")
async def configure_simulation(config: GridConfig):
    """시뮬레이션 구성"""
    state: AppState = app.state.state

    # 도메인 객체 변환
    zones = [
        Zone(
            id=z["id"],
            name=z["name"],
            cells=[tuple(c) for c in z["cells"]],
        )
        for z in config.zones
    ]

    exits = [
        Exit(
            id=e["id"],
            location=tuple(e["location"]),
            capacity=e["capacity"],
            is_emergency=e.get("is_emergency", False),
        )
        for e in config.exits
    ]

    obstacles = [
        Obstacle(
            id=o["id"],
            location=tuple(o["location"]),
            type=o["type"],
            blocking_factor=o.get("blocking_factor", 1.0),
        )
        for o in config.obstacles
    ]

    # 시뮬레이션 구성
    snapshot = state.simulation.configure_map(
        size=(config.width, config.height),
        zones=zones,
        exits=exits,
        obstacles=obstacles,
    )

    state.baseline_metrics = state.simulation.calculate_baseline_metrics()

    # 상태 스냅샷 로깅
    state.ledger.log(
        event_type=EventType.STATE_SNAPSHOT,
        explanation=f"시뮬레이션 구성 완료: {config.width}x{config.height}",
        payload=asdict(snapshot),
    )

    return {
        "status": "configured",
        "snapshot": asdict(snapshot),
        "metrics": state.baseline_metrics,
    }


@app.post("/api/simulation/load-example")
async def load_example_scenario():
    """예시 시나리오 로드"""
    state = _state

    snapshot = state.simulation.load_example_scenario()
    state.baseline_metrics = state.simulation.calculate_baseline_metrics()

    state.ledger.log(
        event_type=EventType.STATE_SNAPSHOT,
        explanation="예시 시나리오 로드 완료",
        payload={"zones": list(snapshot.zones.keys())},
    )

    # Convert snapshot to JSON-serializable dict
    from dataclasses import asdict

    snapshot_dict = {
        "width": snapshot.width,
        "height": snapshot.height,
        "cells": {f"{k[0]},{k[1]}": asdict(v) for k, v in snapshot.cells.items()},
        "zones": {k: asdict(v) for k, v in snapshot.zones.items()},
        "corridors": {k: asdict(v) for k, v in snapshot.corridors.items()},
        "exits": [asdict(e) for e in snapshot.exits],
        "obstacles": [asdict(o) for o in snapshot.obstacles],
        "timestamp": snapshot.timestamp.isoformat(),
    }

    return {
        "status": "loaded",
        "snapshot": snapshot_dict,
        "metrics": state.baseline_metrics,
    }


@app.get("/api/simulation/state")
async def get_state_endpoint():
    """현재 상태 조회"""
    state = _state
    snapshot = state.simulation.get_state_snapshot()

    from dataclasses import asdict

    snapshot_dict = {
        "width": snapshot.width,
        "height": snapshot.height,
        "cells": {f"{k[0]},{k[1]}": asdict(v) for k, v in snapshot.cells.items()},
        "zones": {k: asdict(v) for k, v in snapshot.zones.items()},
        "corridors": {k: asdict(v) for k, v in snapshot.corridors.items()},
        "exits": [asdict(e) for e in snapshot.exits],
        "obstacles": [asdict(o) for o in snapshot.obstacles],
        "timestamp": snapshot.timestamp.isoformat(),
    }
    return snapshot_dict


@app.get("/api/simulation/metrics")
async def get_metrics():
    """메트릭 조회"""
    state = _state
    return state.baseline_metrics


@app.post("/api/intent/parse")
async def parse_intent(request: IntentRequest):
    """인텐트 파싱"""
    state = _state

    snapshot = state.simulation.load_example_scenario()
    state.baseline_metrics = state.simulation.calculate_baseline_metrics()

    state.ledger.log(
        event_type=EventType.STATE_SNAPSHOT,
        explanation="예시 시나리오 로드 완료",
        payload=asdict(snapshot),
    )

    return {
        "status": "loaded",
        "snapshot": asdict(snapshot),
        "metrics": state.baseline_metrics,
    }


@app.get("/api/simulation/state")
async def get_app_state():
    """현재 상태 조회"""
    state: AppState = app.state.state
    return asdict(state.simulation.get_state_snapshot())


@app.get("/api/simulation/metrics")
async def get_metrics():
    """메트릭 조회"""
    state: AppState = app.state.state
    return state.baseline_metrics


@app.post("/api/intent/parse")
async def parse_intent(request: IntentRequest):
    """인텐트 파싱"""
    state: AppState = app.state.state

    # 인텐트 입력 생성
    intent_input = IntentInput(text=request.text, structured=request.structured)

    # 인텐트 수신 로깅
    state.ledger.log_intent_received(request.text or str(request.structured))

    # 파싱
    parsed = state.intent_parser.parse(intent_input)

    # 파싱 결과 로깅
    state.ledger.log_intent_parsed(
        parsed.intent_id,
        {
            "intent_type": parsed.intent_type.value,
            "target_zone": parsed.target_zone,
            "objective": parsed.objective,
            "constraints": parsed.constraints,
            "ambiguity_score": parsed.ambiguity_score,
        },
    )

    return {
        "intent_id": parsed.intent_id,
        "intent_type": parsed.intent_type.value,
        "target_zone": parsed.target_zone,
        "objective": parsed.objective,
        "constraints": parsed.constraints,
        "invariants": parsed.invariants,
        "ambiguity_score": parsed.ambiguity_score,
        "ambiguity_level": parsed.ambiguity_level.value,
        "warnings": [{"code": w.code, "message": w.message} for w in parsed.warnings],
        "requires_human_review": parsed.requires_human_review,
    }


@app.post("/api/dsl/compile")
async def compile_dsl(intent_data: dict):
    """DSL 컴파일"""
    state: AppState = app.state.state

    # 파싱된 인텐트 데이터로 DSL 생성
    from app.services.intent_parser import ParsedIntent, IntentType, AmbiguityLevel

    parsed_intent = ParsedIntent(
        intent_id=str(uuid.uuid4()),
        raw_text=intent_data.get("raw_text", ""),
        intent_type=IntentType(intent_data.get("intent_type", "unknown")),
        target_zone=intent_data.get("target_zone"),
        objective=intent_data.get("objective"),
        constraints=intent_data.get("constraints", {}),
        invariants=intent_data.get("invariants", {}),
        ambiguity_score=intent_data.get("ambiguity_score", 0.0),
        ambiguity_level=AmbiguityLevel(intent_data.get("ambiguity_level", "clear")),
        requires_human_review=intent_data.get("requires_human_review", False),
    )

    dsl = state.dsl_compiler.compile(parsed_intent)
    state.current_dsl = dsl

    # DSL 생성 로깅
    state.ledger.log_dsl_generated(
        dsl.dsl_id,
        {
            "intent_type": dsl.intent_type.value,
            "target": dsl.target,
            "objective": dsl.objective,
            "constraints": dsl.constraints,
        },
    )

    return {
        "dsl_id": dsl.dsl_id,
        "intent_type": dsl.intent_type.value,
        "target": dsl.target,
        "objective": dsl.objective,
        "constraints": dsl.constraints,
        "invariants": dsl.invariants,
        "risk_budget": dsl.risk_budget,
        "human_review_required": dsl.human_review_required,
    }


@app.post("/api/ir/compile")
async def compile_ir(dsl_data: dict):
    """IR 컴파일"""
    state: AppState = app.state.state

    from app.services.dsl_compiler import IntentDSL, IntentType

    dsl = IntentDSL(
        dsl_id=dsl_data.get("dsl_id", str(uuid.uuid4())),
        intent_type=IntentType(dsl_data.get("intent_type", "unknown")),
        target=dsl_data.get("target"),
        objective=dsl_data.get("objective", {}),
        constraints=dsl_data.get("constraints", []),
        invariants=dsl_data.get("invariants", {}),
        risk_budget=dsl_data.get("risk_budget", {}),
        human_review_required=dsl_data.get("human_review_required", False),
    )

    ir = state.ir_compiler.compile(dsl)
    state.current_ir = ir

    # IR 컴파일 로깅
    state.ledger.log_ir_compiled(
        ir.ir_id,
        {
            "objectives": ir.objectives,
            "constraints": ir.constraints,
            "invariants": ir.invariants,
        },
    )

    return {
        "ir_id": ir.ir_id,
        "dsl_id": ir.dsl_id,
        "objectives": ir.objectives,
        "constraints": ir.constraints,
        "invariants": ir.invariants,
        "approval_requirements": ir.approval_requirements,
        "scoring_weights": ir.scoring_weights,
    }


@app.post("/api/patches/generate")
async def generate_patches(ir_data: dict):
    """패치 후보 생성"""
    state: AppState = app.state.state

    # 패치 플래너 초기화
    state.patch_planner = PatchPlanner(state.simulation)

    # IR 객체 재구성
    from app.services.dsl_compiler import ConstraintIR

    ir = ConstraintIR(
        ir_id=ir_data.get("ir_id", str(uuid.uuid4())),
        dsl_id=ir_data.get("dsl_id", ""),
        objectives=ir_data.get("objectives", []),
        constraints=ir_data.get("constraints", []),
        invariants=ir_data.get("invariants", []),
        approval_requirements=ir_data.get("approval_requirements", []),
        scoring_weights=ir_data.get("scoring_weights", {}),
    )

    current_state = state.simulation.get_state_snapshot()

    # 候选人 생성
    candidates = state.patch_planner.generate_candidates(
        ir=ir,
        current_state=current_state,
        num_candidates=5,
    )

    state.current_candidates = candidates

    # 패치 생성 로깅
    state.ledger.log_patches_generated(
        [c.patch_id for c in candidates],
        [
            {
                "patch_id": c.patch_id,
                "patch_type": c.patch_type.value,
                "target_cells": c.target_cells,
                "rationale": c.rationale,
            }
            for c in candidates
        ],
    )

    return {
        "candidates": [
            {
                "patch_id": c.patch_id,
                "patch_type": c.patch_type.value,
                "target_cells": c.target_cells,
                "rationale": c.rationale,
                "expected_effects": c.expected_effects,
                "estimated_risks": c.estimated_risks,
                "scoring_metadata": c.scoring_metadata,
            }
            for c in candidates
        ]
    }


@app.post("/api/patches/{patch_id}/verify")
async def verify_patch(patch_id: str):
    """패치 안전성 검증"""
    state: AppState = app.state.state

    # 패치 찾기
    patch = None
    for c in state.current_candidates:
        if c.patch_id == patch_id:
            patch = c
            break

    if not patch:
        raise HTTPException(status_code=404, detail="패치를 찾을 수 없습니다")

    before_state = state.simulation.get_state_snapshot()

    # 패치 적용 (dry-run)
    patch_dict = {
        "cell_updates": [
            {"x": tc[0], "y": tc[1], **action}
            for tc, action in zip(patch.target_cells, patch.actions)
            if "coordinate" not in action
        ]
    }

    after_state = state.simulation.apply_patch(patch_dict)

    # 안전성 검증
    if state.current_ir:
        result = state.safety_verifier.verify(
            patch=patch,
            before_state=before_state,
            after_state=after_state,
            ir=state.current_ir,
        )

        # 결정 로깅
        state.ledger.log_safety_decision(
            patch_id,
            result.decision.value,
            result.explanation,
        )

        return {
            "decision": result.decision.value,
            "checked_invariants": result.checked_invariants,
            "checked_constraints": result.checked_constraints,
            "violations": result.violations,
            "warnings": result.warnings,
            "explanation": result.explanation,
        }

    return {"decision": "NO_IR", "message": "IR이 없습니다"}


@app.post("/api/patches/{patch_id}/apply")
async def apply_patch(patch_id: str):
    """패치 적용"""
    state: AppState = app.state.state

    # 패치 찾기
    patch = None
    for c in state.current_candidates:
        if c.patch_id == patch_id:
            patch = c
            break

    if not patch:
        raise HTTPException(status_code=404, detail="패치를 찾을 수 없습니다")

    # 적용 전 메트릭
    before_state = state.simulation.get_state_snapshot()
    metrics_before = state.simulation.calculate_baseline_metrics()

    state.ledger.log_metrics(metrics_before, "before")

    # 패치 적용
    patch_dict = {
        "cell_updates": [
            {"x": tc[0], "y": tc[1], **action}
            for tc, action in zip(patch.target_cells, patch.actions)
            if "coordinate" not in action
        ]
    }

    after_state = state.simulation.apply_patch(patch_dict)

    # 적용 후 메트릭
    metrics_after = state.simulation.calculate_baseline_metrics()

    state.ledger.log_metrics(metrics_after, "after")

    # 패치 적용 로깅
    state.ledger.log_patch_applied(patch_id, metrics_before, metrics_after)

    # 차이점 계산
    diff = GridSimulation.diff_states(before_state, after_state)

    return {
        "status": "applied",
        "patch_id": patch_id,
        "metrics_before": metrics_before,
        "metrics_after": metrics_after,
        "diff": diff,
    }


@app.get("/api/ledger")
async def get_ledger():
    """원장 조회"""
    state: AppState = app.state.state
    return {
        "session_id": state.ledger.get_session_id(),
        "entries": [e.to_dict() for e in state.ledger.entries],
    }


@app.get("/api/replay/timeline")
async def get_replay_timeline():
    """리플레이 타임라인"""
    state: AppState = app.state.state
    return {
        "timeline": state.replay_engine.get_timeline(),
    }


@app.get("/api/replay/events/{event_id}")
async def get_replay_event(event_id: str):
    """리플레이 이벤트 조회"""
    state: AppState = app.state.state
    event = state.replay_engine.get_event_by_id(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="이벤트를 찾을 수 없습니다")

    return event.to_dict()


@app.post("/api/replay/replay-from/{event_id}")
async def replay_from_event(event_id: str):
    """이벤트부터 리플레이"""
    state: AppState = app.state.state
    events = state.replay_engine.replay_from_event(event_id)

    return {
        "events": [e.to_dict() for e in events],
    }


@app.get("/api/replay/metrics-progression")
async def get_metrics_progression():
    """메트릭 변화 추이"""
    state: AppState = app.state.state
    return {
        "progression": state.replay_engine.get_metrics_progression(),
    }


# ============ Run ============

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
