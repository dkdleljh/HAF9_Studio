"""패치 플래너 및 안전성 검증기."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import random

from ..domain.spatial import Cell, SpatialState, Zone
from ..simulation.grid import GridSimulation
from .dsl_compiler import ConstraintIR, IntentDSL


class PatchType(str, Enum):
    """패치 유형"""

    MODIFY_RIGIDITY = "modify_rigidity"
    MODIFY_FLOW = "modify_flow"
    MODIFY_PASSABILITY = "modify_passability"
    ADD_CORRIDOR = "add_corridor"
    REMOVE_OBSTACLE = "remove_obstacle"
    REINFORCE_CELL = "reinforce_cell"
    RELIEVE_CONGESTION = "relieve_congestion"


class SafetyDecision(str, Enum):
    """안전성 결정"""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"
    SANDBOX_ONLY = "SANDBOX_ONLY"


@dataclass
class PatchCandidate:
    """패치 후보"""

    patch_id: str
    patch_type: PatchType
    target_cells: list[tuple[int, int]]
    actions: list[dict]
    rationale: str
    expected_effects: dict
    estimated_risks: list[str]
    rollback_plan: dict
    scoring_metadata: dict = field(default_factory=dict)


@dataclass
class SafetyVerificationResult:
    """안전성 검증 결과"""

    decision: SafetyDecision
    checked_invariants: list[dict]
    checked_constraints: list[dict]
    violations: list[dict]
    warnings: list[dict]
    explanation: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PatchPlanner:
    """패치 후보 생성"""

    def __init__(self, simulation: GridSimulation):
        self.simulation = simulation

    def generate_candidates(
        self,
        ir: ConstraintIR,
        current_state: SpatialState,
        num_candidates: int = 5,
    ) -> list[PatchCandidate]:
        """패치 후보를 생성합니다."""
        candidates: list[PatchCandidate] = []

        # 목표 존 결정
        target_zones = []
        for obj in ir.objectives:
            if zone_id := obj.get("target_zone"):
                target_zones.append(zone_id)

        if not target_zones:
            target_zones = list(current_state.zones.keys())

        # 각 존에 대해 패치 후보 생성
        for zone_id in target_zones:
            zone = current_state.zones.get(zone_id)
            if not zone:
                continue

            # 여러类型的 패치 생성
            candidates.extend(
                self._generate_flow_optimization_patch(zone, current_state)
            )
            candidates.extend(
                self._generate_obstacle_removal_patch(zone, current_state)
            )
            candidates.extend(
                self._generate_corridor_addition_patch(zone, current_state)
            )
            candidates.extend(self._generate_reinforcement_patch(zone, current_state))

            if len(candidates) >= num_candidates:
                break

        # 최소 수 보장
        while len(candidates) < num_candidates:
            candidates.extend(self._generate_generic_patch(current_state))

        return candidates[:num_candidates]

    def _generate_flow_optimization_patch(
        self, zone: Zone, state: SpatialState
    ) -> list[PatchCandidate]:
        """유동 최적화 패치 생성"""
        patches = []

        # 존 내 셀 중 유동이 높은 셀 찾기
        high_flow_cells = [
            coord
            for coord in zone.cells
            if coord in state.cells and state.cells[coord].occupancy_flow > 0.5
        ]

        if high_flow_cells:
            target_cells = high_flow_cells[:3]  # 상위 3개만
            patch_id = str(uuid.uuid4())

            actions = []
            for coord in target_cells:
                actions.append(
                    {
                        "action": "modify_flow",
                        "coordinate": coord,
                        "property": "occupancy_flow",
                        "value": max(0.1, state.cells[coord].occupancy_flow * 0.7),
                    }
                )

            patches.append(
                PatchCandidate(
                    patch_id=patch_id,
                    patch_type=PatchType.MODIFY_FLOW,
                    target_cells=target_cells,
                    actions=actions,
                    rationale=f"zone {zone.id}의 유동 병목 구간 완화",
                    expected_effects={
                        "evacuation_time_reduction": 0.15,
                        "crowd_density_reduction": 0.2,
                    },
                    estimated_risks=["일부 경로 변경 필요"],
                    rollback_plan={
                        "action": "restore_original_flow",
                        "backup_required": True,
                    },
                    scoring_metadata={"priority": 0.85, "risk_level": "low"},
                )
            )

        return patches

    def _generate_obstacle_removal_patch(
        self, zone: Zone, state: SpatialState
    ) -> list[PatchCandidate]:
        """장애물 제거 패치 생성"""
        patches = []

        # 존 내 장애물 찾기
        zone_obstacles = [obs for obs in state.obstacles if obs.location in zone.cells]

        if zone_obstacles:
            target_obs = zone_obstacles[0]
            patch_id = str(uuid.uuid4())

            actions = [
                {
                    "action": "remove_obstacle",
                    "obstacle_id": target_obs.id,
                }
            ]

            patches.append(
                PatchCandidate(
                    patch_id=patch_id,
                    patch_type=PatchType.REMOVE_OBSTACLE,
                    target_cells=[target_obs.location],
                    actions=actions,
                    rationale=f"{target_obs.id} 제거로 접근성 개선",
                    expected_effects={
                        "accessibility_improvement": 0.25,
                        "evacuation_time_reduction": 0.1,
                    },
                    estimated_risks=["구조적 영향 최소화"],
                    rollback_plan={
                        "action": "restore_obstacle",
                        "backup_required": True,
                    },
                    scoring_metadata={"priority": 0.75, "risk_level": "medium"},
                )
            )

        return patches

    def _generate_corridor_addition_patch(
        self, zone: Zone, state: SpatialState
    ) -> list[PatchCandidate]:
        """새 복도 추가 패치 생성"""
        patches = []

        # 출구까지의 경로에 새 셀 추가
        if state.exits and zone.cells:
            exit_cell = state.exits[0].location
            zone_cells_near_exit = [
                c
                for c in zone.cells
                if abs(c[0] - exit_cell[0]) + abs(c[1] - exit_cell[1]) < 5
            ]

            if zone_cells_near_exit:
                target_cells = zone_cells_near_exit[:2]
                patch_id = str(uuid.uuid4())

                actions = []
                for coord in target_cells:
                    actions.append(
                        {
                            "action": "enhance_passability",
                            "coordinate": coord,
                            "property": "rigidity",
                            "value": 0.5,  # 더 통과하기 쉽게
                        }
                    )

                patches.append(
                    PatchCandidate(
                        patch_id=patch_id,
                        patch_type=PatchType.ADD_CORRIDOR,
                        target_cells=target_cells,
                        actions=actions,
                        rationale="새 긴급 경로 생성으로 대피 효율 향상",
                        expected_effects={
                            "evacuation_time_reduction": 0.2,
                            "flow_capacity_increase": 0.3,
                        },
                        estimated_risks=["구조적 검증 필요"],
                        rollback_plan={
                            "action": "restore_rigidity",
                            "backup_required": True,
                        },
                        scoring_metadata={"priority": 0.9, "risk_level": "medium"},
                    )
                )

        return patches

    def _generate_reinforcement_patch(
        self, zone: Zone, state: SpatialState
    ) -> list[PatchCandidate]:
        """보강 패치 생성"""
        patches = []

        # 스트레스가 높은 셀 찾기
        stress_cells = [
            coord
            for coord in zone.cells
            if coord in state.cells and state.cells[coord].strain > 0.5
        ]

        if stress_cells:
            target_cells = stress_cells[:2]
            patch_id = str(uuid.uuid4())

            actions = []
            for coord in target_cells:
                actions.append(
                    {
                        "action": "reinforce",
                        "coordinate": coord,
                        "property": "rigidity",
                        "value": min(2.0, state.cells[coord].rigidity * 1.5),
                    }
                )

            patches.append(
                PatchCandidate(
                    patch_id=patch_id,
                    patch_type=PatchType.REINFORCE_CELL,
                    target_cells=target_cells,
                    actions=actions,
                    rationale="높은 스트레스 구간 보강으로 안전성 향상",
                    expected_effects={
                        "stress_reduction": 0.3,
                        "structural_safety_improvement": 0.15,
                    },
                    estimated_risks=["비용 증가"],
                    rollback_plan={
                        "action": "restore_original_rigidity",
                        "backup_required": True,
                    },
                    scoring_metadata={"priority": 0.7, "risk_level": "low"},
                )
            )

        return patches

    def _generate_generic_patch(self, state: SpatialState) -> list[PatchCandidate]:
        """범용 패치 생성"""
        patches = []

        # 무작위 셀 선택
        if state.cells:
            random.seed(42)  # 재현성
            sample_cells = random.sample(
                list(state.cells.keys()), min(3, len(state.cells))
            )
            patch_id = str(uuid.uuid4())

            actions = [
                {
                    "action": "optimize",
                    "coordinate": sample_cells[0],
                    "property": "occupancy_flow",
                    "value": 0.8,
                }
            ]

            patches.append(
                PatchCandidate(
                    patch_id=patch_id,
                    patch_type=PatchType.MODIFY_FLOW,
                    target_cells=sample_cells,
                    actions=actions,
                    rationale="범용 최적화",
                    expected_effects={"efficiency_improvement": 0.1},
                    estimated_risks=["최소"],
                    rollback_plan={"action": "restore", "backup_required": True},
                    scoring_metadata={"priority": 0.5, "risk_level": "low"},
                )
            )

        return patches


class SafetyVerifier:
    """안전성 검증기"""

    def __init__(self):
        self.min_safety_factor = 1.8
        self.max_peak_stress = 0.7
        self.min_accessibility = 0.5

    def verify(
        self,
        patch: PatchCandidate,
        before_state: SpatialState,
        after_state: SpatialState,
        ir: ConstraintIR,
    ) -> SafetyVerificationResult:
        """패치의 안전성을 검증합니다."""
        checked_invariants: list[dict] = []
        checked_constraints: list[dict] = []
        violations: list[dict] = []
        warnings: list[dict] = []

        # 불변조건 검증
        for invariant in ir.invariants:
            name = invariant["name"]
            expected = invariant["expected_value"]
            result = self._check_invariant(name, expected, after_state)
            checked_invariants.append(
                {
                    "name": name,
                    "expected": expected,
                    "actual": result["actual"],
                    "satisfied": result["satisfied"],
                }
            )

            if not result["satisfied"]:
                violations.append(
                    {
                        "type": "invariant",
                        "name": name,
                        "message": f"불변조건 위반: {name}",
                    }
                )

        # 제약조건 검증
        for constraint in ir.constraints:
            result = self._check_constraint(constraint, after_state)
            checked_constraints.append(
                {
                    "name": constraint.get("name"),
                    "type": constraint.get("type"),
                    "satisfied": result["satisfied"],
                }
            )

            if not result["satisfied"]:
                violations.append(
                    {
                        "type": "constraint",
                        "name": constraint.get("name"),
                        "message": f"제약조건 위반: {constraint.get('name')}",
                    }
                )

        # 경고 확인
        if patch.estimated_risks:
            for risk in patch.estimated_risks:
                warnings.append(
                    {
                        "type": "risk",
                        "message": f"예상 리스크: {risk}",
                    }
                )

        # 결정 내리기
        decision = self._make_decision(violations, warnings, ir)

        explanation = self._build_explanation(decision, violations, warnings)

        return SafetyVerificationResult(
            decision=decision,
            checked_invariants=checked_invariants,
            checked_constraints=checked_constraints,
            violations=violations,
            warnings=warnings,
            explanation=explanation,
        )

    def _check_invariant(
        self, name: str, expected: bool | float, state: SpatialState
    ) -> dict:
        """불변조건 확인"""
        if name == "all_exits_accessible":
            # 출구 접근성 확인
            for exit_obj in state.exits:
                if exit_obj.location not in state.cells:
                    return {"satisfied": False, "actual": False}
                cell = state.cells[exit_obj.location]
                if "obstacle" in cell.status_flags:
                    return {"satisfied": False, "actual": False}
            return {"satisfied": True, "actual": True}

        elif name == "structural_safety_factor":
            # 평균 강성 확인 (단순화)
            if not state.cells:
                return {"satisfied": True, "actual": 2.0}
            avg_rigidity = sum(c.rigidity for c in state.cells.values()) / len(
                state.cells
            )
            actual = avg_rigidity
            return {"satisfied": actual >= 1.5, "actual": actual}

        elif name == "max_peak_stress":
            # 최대 스트레스 확인
            max_stress = max((c.strain for c in state.cells.values()), default=0.0)
            return {"satisfied": max_stress <= expected, "actual": max_stress}

        elif name == "min_accessibility":
            # 최소 접근성 확인
            min_access = min(
                (zone.accessibility for zone in state.zones.values()), default=1.0
            )
            return {"satisfied": min_access >= expected, "actual": min_access}

        return {"satisfied": True, "actual": expected}

    def _check_constraint(self, constraint: dict, state: SpatialState) -> dict:
        """제약조건 확인"""
        name = constraint.get("name", "")
        operator = constraint.get("operator", "<=")
        value = constraint.get("value")

        if name == "evacuation_time":
            # 대피 시간 확인
            if not state.zones or not state.exits:
                return {"satisfied": True}

            max_evac = max(z.evacuation_time_estimate for z in state.zones.values())

            if operator == "<=":
                return {"satisfied": max_evac <= value, "actual": max_evac}
            elif operator == ">=":
                return {"satisfied": max_evac >= value, "actual": max_evac}

        elif name == "peak_stress":
            max_stress = max((c.strain for c in state.cells.values()), default=0.0)
            if operator == "<=":
                return {"satisfied": max_stress <= value, "actual": max_stress}

        elif name == "structural_safety_factor":
            avg_rigidity = sum(c.rigidity for c in state.cells.values()) / max(
                len(state.cells), 1
            )
            if operator == ">=":
                return {"satisfied": avg_rigidity >= value, "actual": avg_rigidity}

        return {"satisfied": True}

    def _make_decision(
        self,
        violations: list[dict],
        warnings: list[dict],
        ir: ConstraintIR,
    ) -> SafetyDecision:
        """결정 내리기"""
        # 위반이 있으면 거부
        if violations:
            return SafetyDecision.REJECTED

        # 필수 승인 요구사항 확인
        for req in ir.approval_requirements:
            if req == "human_review_required":
                return SafetyDecision.REQUIRES_HUMAN_REVIEW

        # 경고가 많으면 리뷰 필요
        if len(warnings) >= 3:
            return SafetyDecision.REQUIRES_HUMAN_REVIEW

        return SafetyDecision.APPROVED

    def _build_explanation(
        self,
        decision: SafetyDecision,
        violations: list[dict],
        warnings: list[dict],
    ) -> str:
        """설명 생성"""
        if decision == SafetyDecision.APPROVED:
            return (
                "모든 불변조건과 제약조건이 충족되었습니다. 패치 적용이 승인되었습니다."
            )

        elif decision == SafetyDecision.REJECTED:
            reason = "; ".join(v["message"] for v in violations)
            return f"안전성 검증 실패: {reason}"

        elif decision == SafetyDecision.REQUIRES_HUMAN_REVIEW:
            return "인수 인계 검토가 필요합니다. 경고 또는 추가 검증이 요청되었습니다."

        else:
            return "샌드박스 모드에서만 적용 가능합니다."
