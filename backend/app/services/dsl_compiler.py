"""DSL 및 IR 컴파일러."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

from .intent_parser import IntentType, ParsedIntent


class DecisionState(str, Enum):
    """결정 상태"""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"
    SANDBOX_ONLY = "SANDBOX_ONLY"


@dataclass
class IntentDSL:
    """인텐트 DSL 표현"""

    dsl_id: str
    intent_type: IntentType
    target: str | None
    objective: dict
    constraints: list[dict]
    invariants: dict[str, bool]
    risk_budget: dict
    audit_hooks: list[str] = field(default_factory=list)
    human_review_required: bool = False
    version: str = "1.0"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ConstraintIR:
    """제약 IR (Intermediate Representation)"""

    ir_id: str
    dsl_id: str
    objectives: list[dict]
    constraints: list[dict]
    invariants: list[dict]
    approval_requirements: list[str]
    scoring_weights: dict[str, float]
    rollback_requirements: list[str]
    version: str = "1.0"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DSLCompiler:
    """인텐트를 DSL로 변환"""

    DEFAULT_INVARIANTS = {
        "all_exits_accessible": True,
        "structural_safety_factor": 1.8,
        "max_peak_stress": 0.7,
        "min_accessibility": 0.5,
    }

    DEFAULT_RISK_BUDGET = {
        "max_failure_probability": 1e-9,
        "max_cost": 100000,
        "max_rollback_time": 300,
    }

    def compile(self, parsed_intent: ParsedIntent) -> IntentDSL:
        """파싱된 인텐트를 DSL로 컴파일합니다."""
        dsl_id = str(uuid.uuid4())

        # 목적 구성
        objective = self._build_objective(parsed_intent)

        # 제약조건 구성
        constraints = self._build_constraints(parsed_intent)

        # 불변조건 구성
        invariants = self._build_invariants(parsed_intent)

        # 리스크 예산 구성
        risk_budget = self._build_risk_budget(parsed_intent)

        # 감사 후크 구성
        audit_hooks = [
            "intent_received",
            "intent_parsed",
            "dsl_generated",
            "ir_compiled",
            "patches_generated",
            "safety_verified",
            "patch_applied",
        ]

        return IntentDSL(
            dsl_id=dsl_id,
            intent_type=parsed_intent.intent_type,
            target=parsed_intent.target_zone,
            objective=objective,
            constraints=constraints,
            invariants=invariants,
            risk_budget=risk_budget,
            audit_hooks=audit_hooks,
            human_review_required=parsed_intent.requires_human_review,
        )

    def _build_objective(self, parsed_intent: ParsedIntent) -> dict:
        """목적 구성"""
        if parsed_intent.intent_type == IntentType.EVACUATION_OPTIMIZATION:
            return {
                "minimize": parsed_intent.objective or "evacuation_time",
                "target_zone": parsed_intent.target_zone,
                "threshold": parsed_intent.constraints.get("evacuation_time"),
            }
        elif parsed_intent.intent_type == IntentType.SAFETY_ENHANCEMENT:
            return {
                "maximize": parsed_intent.objective or "safety_score",
                "target_zone": parsed_intent.target_zone,
            }
        elif parsed_intent.intent_type == IntentType.FLOW_OPTIMIZATION:
            return {
                "maximize": parsed_intent.objective or "flow_efficiency",
                "target_zone": parsed_intent.target_zone,
            }
        else:
            return {
                "optimize": parsed_intent.objective or "general",
                "target_zone": parsed_intent.target_zone,
            }

    def _build_constraints(self, parsed_intent: ParsedIntent) -> list[dict]:
        """제약조건 구성"""
        constraints = []

        # 명시적 제약조건
        for key, value in parsed_intent.constraints.items():
            constraints.append(
                {
                    "type": "explicit",
                    "name": key,
                    "operator": "<=",
                    "value": value,
                }
            )

        # 인텐트 유형별 기본 제약조건
        if parsed_intent.intent_type == IntentType.EVACUATION_OPTIMIZATION:
            constraints.extend(
                [
                    {
                        "type": "implicit",
                        "name": "peak_stress",
                        "operator": "<=",
                        "value": 0.7,
                    },
                    {
                        "type": "implicit",
                        "name": "noise_db",
                        "operator": "<=",
                        "value": 55.0,
                    },
                ]
            )
        elif parsed_intent.intent_type == IntentType.SAFETY_ENHANCEMENT:
            constraints.extend(
                [
                    {
                        "type": "implicit",
                        "name": "structural_safety_factor",
                        "operator": ">=",
                        "value": 1.8,
                    },
                    {
                        "type": "implicit",
                        "name": "accessibility",
                        "operator": ">=",
                        "value": 0.5,
                    },
                ]
            )

        return constraints

    def _build_invariants(self, parsed_intent: ParsedIntent) -> dict[str, bool]:
        """불변조건 구성"""
        invariants = dict(self.DEFAULT_INVARIANTS)

        # 명시적 불변조건 병합
        for key, value in parsed_intent.invariants.items():
            invariants[key] = value

        return invariants

    def _build_risk_budget(self, parsed_intent: ParsedIntent) -> dict:
        """리스크 예산 구성"""
        risk_budget = dict(self.DEFAULT_RISK_BUDGET)

        # 모호성에 따른 조정이 필요한 경우
        if parsed_intent.ambiguity_score > 0.5:
            risk_budget["max_failure_probability"] = 1e-6
            risk_budget["requires_extra_validation"] = True

        return risk_budget


class IRCompiler:
    """DSL을 IR로 컴파일"""

    def compile(self, dsl: IntentDSL) -> ConstraintIR:
        """DSL을 IR로 컴파일합니다."""
        ir_id = str(uuid.uuid4())

        # 목표 함수 변환
        objectives = self._convert_objectives(dsl.objective)

        # 제약조건 변환
        constraints = self._convert_constraints(dsl.constraints)

        # 불변조건 변환
        invariants = self._convert_invariants(dsl.invariants)

        # 승인 요구사항
        approval_requirements = self._build_approval_requirements(dsl)

        # 점수 가중치
        scoring_weights = self._build_scoring_weights(dsl)

        # 롤백 요구사항
        rollback_requirements = [
            "backup_state_before_apply",
            "verify_invariants_after_apply",
            "auto_rollback_on_failure",
            "log_rollback_event",
        ]

        return ConstraintIR(
            ir_id=ir_id,
            dsl_id=dsl.dsl_id,
            objectives=objectives,
            constraints=constraints,
            invariants=invariants,
            approval_requirements=approval_requirements,
            scoring_weights=scoring_weights,
            rollback_requirements=rollback_requirements,
        )

    def _convert_objectives(self, objective: dict) -> list[dict]:
        """목적 함수 변환"""
        objectives = []

        if "minimize" in objective:
            objectives.append(
                {
                    "type": "minimize",
                    "metric": objective["minimize"],
                    "target_zone": objective.get("target_zone"),
                    "threshold": objective.get("threshold"),
                }
            )
        elif "maximize" in objective:
            objectives.append(
                {
                    "type": "maximize",
                    "metric": objective["maximize"],
                    "target_zone": objective.get("target_zone"),
                }
            )
        elif "optimize" in objective:
            objectives.append(
                {
                    "type": "optimize",
                    "metric": objective["optimize"],
                    "target_zone": objective.get("target_zone"),
                }
            )

        return objectives

    def _convert_constraints(self, constraints: list[dict]) -> list[dict]:
        """제약조건 변환"""
        ir_constraints = []

        for constraint in constraints:
            ir_constraints.append(
                {
                    "name": constraint.get("name", "unnamed"),
                    "type": constraint.get("type", "explicit"),
                    "operator": constraint.get("operator", "<="),
                    "value": constraint.get("value"),
                    "severity": "hard"
                    if constraint.get("type") == "implicit"
                    else "soft",
                }
            )

        return ir_constraints

    def _convert_invariants(self, invariants: dict[str, bool]) -> list[dict]:
        """불변조건 변환"""
        ir_invariants = []

        for name, value in invariants.items():
            ir_invariants.append(
                {
                    "name": name,
                    "expected_value": value,
                    "severity": "critical",
                }
            )

        return ir_invariants

    def _build_approval_requirements(self, dsl: IntentDSL) -> list[str]:
        """승인 요구사항 구성"""
        requirements = []

        if dsl.human_review_required:
            requirements.append("human_review_approval")

        if dsl.risk_budget.get("requires_extra_validation"):
            requirements.append("extra_validation_required")

        requirements.extend(
            [
                "all_invariants_satisfied",
                "safety_checks_passed",
                "rollback_plan_available",
            ]
        )

        return requirements

    def _build_scoring_weights(self, dsl: IntentDSL) -> dict[str, float]:
        """점수 가중치 구성"""
        return {
            "safety": 0.35,
            "efficiency": 0.30,
            "cost": 0.20,
            "risk": 0.15,
        }
