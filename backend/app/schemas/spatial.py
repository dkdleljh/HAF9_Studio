"""Pydantic-style schemas for spatial API payloads and snapshots."""

from __future__ import annotations

from datetime import datetime


class BaseModel:
    """Lightweight BaseModel-compatible schema base."""

    model_config: dict[str, object] = {}

    def __init__(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def model_dump(self) -> dict[str, object]:
        """Returns shallow dictionary representation."""
        return dict(self.__dict__)


def ConfigDict(**kwargs: object) -> dict[str, object]:
    """Returns schema config dictionary."""
    return dict(kwargs)


GridCoordinate = tuple[int, int]


class CellSchema(BaseModel):
    """Schema for a single cell payload."""

    model_config: dict[str, object] = ConfigDict(extra="forbid")

    x: int = 0
    y: int = 0
    rigidity: float = 1.0
    occupancy_flow: float = 0.0
    temperature: float = 22.0
    strain: float = 0.0
    noise: float = 0.0
    fatigue_budget: float = 1.0
    status_flags: set[str] = set()


class ZoneSchema(BaseModel):
    """Schema for a logical zone."""

    model_config: dict[str, object] = ConfigDict(extra="forbid")

    id: str = ""
    name: str = ""
    cells: list[GridCoordinate] = []
    evacuation_time_estimate: float = 0.0
    crowd_density: float = 0.0
    peak_stress: float = 0.0
    accessibility: float = 1.0
    noise_level: float = 0.0


class CorridorSchema(BaseModel):
    """Schema for transit corridor definitions."""

    model_config: dict[str, object] = ConfigDict(extra="forbid")

    id: str = ""
    cells: list[GridCoordinate] = []
    capacity: float = 0.0
    flow_rate: float = 0.0
    bottleneck_indicator: float = 0.0


class ExitSchema(BaseModel):
    """Schema for egress points."""

    model_config: dict[str, object] = ConfigDict(extra="forbid")

    id: str = ""
    location: GridCoordinate = (0, 0)
    capacity: float = 0.0
    is_emergency: bool = False


class ObstacleSchema(BaseModel):
    """Schema for static obstacles."""

    model_config: dict[str, object] = ConfigDict(extra="forbid")

    id: str = ""
    location: GridCoordinate = (0, 0)
    type: str = ""
    blocking_factor: float = 1.0


class SpatialStateSchema(BaseModel):
    """Schema for complete spatial snapshot payloads."""

    model_config: dict[str, object] = ConfigDict(extra="forbid")

    width: int = 0
    height: int = 0
    cells: dict[str, CellSchema] = {}
    zones: dict[str, ZoneSchema] = {}
    corridors: dict[str, CorridorSchema] = {}
    exits: list[ExitSchema] = []
    obstacles: list[ObstacleSchema] = []
    timestamp: datetime = datetime.fromtimestamp(0)
    metadata: dict[str, object] = {}


class GridConfigSchema(BaseModel):
    """Schema for grid simulation configuration requests."""

    model_config: dict[str, object] = ConfigDict(extra="forbid")

    size: tuple[int, int] = (0, 0)
    zones: list[ZoneSchema] = []
    corridors: list[CorridorSchema] = []
    exits: list[ExitSchema] = []
    obstacles: list[ObstacleSchema] = []
