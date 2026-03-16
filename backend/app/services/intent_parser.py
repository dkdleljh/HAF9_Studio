"""인텐트 입력 및 파싱 서비스."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class IntentType(str, Enum):
    """인텐트 유형"""

    EVACUATION_OPTIMIZATION = "evacuation_optimization"
    SAFETY_ENHANCEMENT = "safety_enhancement"
    FLOW_OPTIMIZATION = "flow_optimization"
    COMFORT_IMPROVEMENT = "comfort_improvement"
    STRUCTURAL_MODIFICATION = "structural_modification"
    ACCESSIBILITY_IMPROVEMENT = "accessibility_improvement"
    UNKNOWN = "unknown"


class AmbiguityLevel(str, Enum):
    """모호성 수준"""

    CLEAR = "clear"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class IntentWarning:
    """인턴트 관련 경고"""

    code: str
    message: str
    severity: str = "warning"


@dataclass
class ParsedIntent:
    """파싱된 인텐트"""

    intent_id: str
    raw_text: str
    intent_type: IntentType
    target_zone: str | None
    objective: str | None
    constraints: dict[str, float] = field(default_factory=dict)
    invariants: dict[str, bool] = field(default_factory=dict)
    ambiguity_score: float = 0.0
    ambiguity_level: AmbiguityLevel = AmbiguityLevel.CLEAR
    warnings: list[IntentWarning] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    requires_human_review: bool = False


@dataclass
class IntentInput:
    """인텐트 입력"""

    text: str | None = None
    structured: dict | None = None


class IntentParser:
    """자연어 인텐트를 구조화된 인텐트로 변환"""

    # 모호한 용어 매핑
    VAGUE_TERMS = {
        "safer": {"context": "safety", "default": 0.8},
        "better flow": {"context": "flow", "default": 0.7},
        "more comfortable": {"context": "comfort", "default": 0.6},
        "less crowded": {"context": "crowd_density", "default": 0.5},
        "improve": {"context": "general", "default": 0.5},
        "better": {"context": "general", "default": 0.5},
        "optimal": {"context": "general", "default": 0.4},
        "efficient": {"context": "efficiency", "default": 0.5},
    }

    # 패턴 정규식
    ZONE_PATTERN = re.compile(r"zone\s*(\d+)", re.IGNORECASE)
    TIME_PATTERN = re.compile(r"(\d+)\s*(?:seconds?|sec|s)", re.IGNORECASE)
    THRESHOLD_PATTERN = re.compile(
        r"(under|below|less than|above|over)\s*(\d+(?:\.\d+)?)", re.IGNORECASE
    )

    # 인텐트 유형 패턴
    INTENT_PATTERNS = {
        IntentType.EVACUATION_OPTIMIZATION: [
            r"evacuations?",
            r"evacuate",
            r"escape",
            r"exit",
            r"대피",
        ],
        IntentType.SAFETY_ENHANCEMENT: [
            r"safet",
            r"secure",
            r"protectin",
            r"안전",
        ],
        IntentType.FLOW_OPTIMIZATION: [
            r"flow",
            r"traffic",
            r"movement",
            r"흐름",
        ],
        IntentType.COMFORT_IMPROVEMENT: [
            r"comfort",
            r"convenient",
            r"comfortable",
            r"편의",
        ],
        IntentType.STRUCTURAL_MODIFICATION: [
            r"structural",
            r"reinforce",
            r"strengthen",
            r"구조",
        ],
        IntentType.ACCESSIBILITY_IMPROVEMENT: [
            r"accessib",
            r"accessible",
            r"접근",
        ],
    }

    def parse(self, intent_input: IntentInput) -> ParsedIntent:
        """인텐트를 파싱합니다."""
        if intent_input.text:
            return self._parse_natural_language(intent_input.text)
        elif intent_input.structured:
            return self._parse_structured(intent_input.structured)
        else:
            raise ValueError("인텍스트 또는 구조화된 입력이 필요합니다")

    def _parse_natural_language(self, text: str) -> ParsedIntent:
        """자연어를 파싱합니다."""
        intent_id = str(uuid.uuid4())
        warnings: list[IntentWarning] = []

        # 존 추출
        zone_match = self.ZONE_PATTERN.search(text)
        target_zone = f"zone{zone_match.group(1)}" if zone_match else None

        # 시간 임계값 추출
        time_match = self.TIME_PATTERN.search(text)
        time_threshold = float(time_match.group(1)) if time_match else None

        # 인텐트 유형 결정
        intent_type = IntentType.UNKNOWN
        for itype, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    intent_type = itype
                    break
            if intent_type != IntentType.UNKNOWN:
                break

        # 모호성 평가
        ambiguity_score = 0.0
        for vague_term, info in self.VAGUE_TERMS.items():
            if vague_term in text.lower():
                ambiguity_score += info["default"]
                warnings.append(
                    IntentWarning(
                        code="VAGUE_TERM",
                        message=f"모호한 용어 감지: '{vague_term}'. 더 구체적인 수치가 필요합니다.",
                        severity="warning",
                    )
                )

        # 임계값이 없으면 모호성 증가
        if time_threshold is None and "reduce" in text.lower():
            ambiguity_score += 0.3
            warnings.append(
                IntentWarning(
                    code="MISSING_THRESHOLD",
                    message="명시적인 임계값이 없습니다. 구체적인 수치가 권장됩니다.",
                    severity="warning",
                )
            )

        # 제약조건 추출
        constraints: dict[str, float] = {}
        if time_threshold:
            if intent_type == IntentType.EVACUATION_OPTIMIZATION:
                constraints["evacuation_time"] = time_threshold

        # 구조적 안전 관련 확인
        if "structural" in text.lower() or "안전" in text:
            constraints["structural_safety_factor"] = 1.8
            constraints["peak_stress"] = 0.7

        # 모호성 수준 결정
        if ambiguity_score >= 0.7:
            ambiguity_level = AmbiguityLevel.REQUIRES_REVIEW
            requires_human_review = True
        elif ambiguity_score >= 0.5:
            ambiguity_level = AmbiguityLevel.HIGH
            requires_human_review = False
        elif ambiguity_score >= 0.3:
            ambiguity_level = AmbiguityLevel.MEDIUM
            requires_human_review = False
        elif ambiguity_score >= 0.1:
            ambiguity_level = AmbiguityLevel.LOW
            requires_human_review = False
        else:
            ambiguity_level = AmbiguityLevel.CLEAR
            requires_human_review = False

        # 목적 추출
        objective = self._extract_objective(text, intent_type)

        return ParsedIntent(
            intent_id=intent_id,
            raw_text=text,
            intent_type=intent_type,
            target_zone=target_zone,
            objective=objective,
            constraints=constraints,
            ambiguity_score=min(ambiguity_score, 1.0),
            ambiguity_level=ambiguity_level,
            warnings=warnings,
            requires_human_review=requires_human_review,
        )

    def _extract_objective(self, text: str, intent_type: IntentType) -> str:
        """목적 추출"""
        if intent_type == IntentType.EVACUATION_OPTIMIZATION:
            return "evacuation_time"
        elif intent_type == IntentType.SAFETY_ENHANCEMENT:
            return "safety_score"
        elif intent_type == IntentType.FLOW_OPTIMIZATION:
            return "flow_efficiency"
        elif intent_type == IntentType.COMFORT_IMPROVEMENT:
            return "comfort_index"
        elif intent_type == IntentType.STRUCTURAL_MODIFICATION:
            return "structural_integrity"
        elif intent_type == IntentType.ACCESSIBILITY_IMPROVEMENT:
            return "accessibility_score"
        return "general_improvement"

    def _parse_structured(self, structured: dict) -> ParsedIntent:
        """구조화된 입력을 파싱합니다."""
        intent_id = structured.get("intent_id", str(uuid.uuid4()))

        return ParsedIntent(
            intent_id=intent_id,
            raw_text=structured.get("raw_text", ""),
            intent_type=IntentType(structured.get("intent_type", "unknown")),
            target_zone=structured.get("target_zone"),
            objective=structured.get("objective"),
            constraints=structured.get("constraints", {}),
            invariants=structured.get("invariants", {}),
            ambiguity_score=structured.get("ambiguity_score", 0.0),
            ambiguity_level=AmbiguityLevel(structured.get("ambiguity_level", "clear")),
            requires_human_review=structured.get("requires_human_review", False),
        )
