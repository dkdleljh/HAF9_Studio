"""Domain models for the 2D spatial digital twin."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

GridCoordinate = tuple[int, int]


@dataclass(slots=True)
class Cell:
    """Represents a single grid cell state."""

    x: int
    y: int
    rigidity: float = 1.0
    occupancy_flow: float = 0.0
    temperature: float = 22.0
    strain: float = 0.0
    noise: float = 0.0
    fatigue_budget: float = 1.0
    status_flags: set[str] = field(default_factory=set)

    @property
    def key(self) -> GridCoordinate:
        """Returns the coordinate tuple used in maps."""
        return (self.x, self.y)


@dataclass(slots=True)
class Zone:
    """Represents a semantic zone composed of cells."""

    id: str
    name: str
    cells: list[GridCoordinate] = field(default_factory=list)
    evacuation_time_estimate: float = 0.0
    crowd_density: float = 0.0
    peak_stress: float = 0.0
    accessibility: float = 1.0
    noise_level: float = 0.0


@dataclass(slots=True)
class Corridor:
    """Represents a movement corridor across cells."""

    id: str
    cells: list[GridCoordinate] = field(default_factory=list)
    capacity: float = 0.0
    flow_rate: float = 0.0
    bottleneck_indicator: float = 0.0


@dataclass(slots=True)
class Exit:
    """Represents an egress point in the grid."""

    id: str
    location: GridCoordinate
    capacity: float
    is_emergency: bool = False


@dataclass(slots=True)
class Obstacle:
    """Represents a blocking object in the map."""

    id: str
    location: GridCoordinate
    type: str
    blocking_factor: float = 1.0


@dataclass(slots=True)
class SpatialState:
    """Captures a full snapshot of current spatial simulation state."""

    width: int
    height: int
    cells: dict[GridCoordinate, Cell] = field(default_factory=dict)
    zones: dict[str, Zone] = field(default_factory=dict)
    corridors: dict[str, Corridor] = field(default_factory=dict)
    exits: list[Exit] = field(default_factory=list)
    obstacles: list[Obstacle] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = field(default_factory=dict)

    def copy(self) -> SpatialState:
        """Returns a deep copy of the snapshot."""
        cells_copy = {
            coordinate: Cell(
                x=cell.x,
                y=cell.y,
                rigidity=cell.rigidity,
                occupancy_flow=cell.occupancy_flow,
                temperature=cell.temperature,
                strain=cell.strain,
                noise=cell.noise,
                fatigue_budget=cell.fatigue_budget,
                status_flags=set(cell.status_flags),
            )
            for coordinate, cell in self.cells.items()
        }

        zones_copy = {
            zone_id: Zone(
                id=zone.id,
                name=zone.name,
                cells=list(zone.cells),
                evacuation_time_estimate=zone.evacuation_time_estimate,
                crowd_density=zone.crowd_density,
                peak_stress=zone.peak_stress,
                accessibility=zone.accessibility,
                noise_level=zone.noise_level,
            )
            for zone_id, zone in self.zones.items()
        }

        corridors_copy = {
            corridor_id: Corridor(
                id=corridor.id,
                cells=list(corridor.cells),
                capacity=corridor.capacity,
                flow_rate=corridor.flow_rate,
                bottleneck_indicator=corridor.bottleneck_indicator,
            )
            for corridor_id, corridor in self.corridors.items()
        }

        exits_copy = [
            Exit(
                id=exit_obj.id,
                location=exit_obj.location,
                capacity=exit_obj.capacity,
                is_emergency=exit_obj.is_emergency,
            )
            for exit_obj in self.exits
        ]

        obstacles_copy = [
            Obstacle(
                id=obstacle.id,
                location=obstacle.location,
                type=obstacle.type,
                blocking_factor=obstacle.blocking_factor,
            )
            for obstacle in self.obstacles
        ]

        return SpatialState(
            width=self.width,
            height=self.height,
            cells=cells_copy,
            zones=zones_copy,
            corridors=corridors_copy,
            exits=exits_copy,
            obstacles=obstacles_copy,
            timestamp=self.timestamp,
            metadata=dict(self.metadata),
        )
