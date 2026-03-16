"""2D grid simulation core for spatial digital twins."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import cast

from ..domain.spatial import Cell, Corridor, Exit, Obstacle, SpatialState, Zone
from .metrics import (
    calculate_accessibility,
    calculate_crowd_density,
    calculate_evacuation_time,
    calculate_noise_level,
    calculate_peak_stress,
)


class GridSimulation:
    """Manages 2D grid configuration, updates, and metric snapshots."""

    def __init__(self) -> None:
        """Initializes an empty simulation state."""
        self._state: SpatialState = SpatialState(width=0, height=0)

    def configure_map(
        self,
        size: tuple[int, int],
        zones: list[Zone],
        exits: list[Exit],
        obstacles: list[Obstacle],
        corridors: list[Corridor] | None = None,
    ) -> SpatialState:
        """Configures a map with zones, exits, obstacles, and optional corridors."""
        width, height = size
        cells: dict[tuple[int, int], Cell] = {
            (x, y): Cell(x=x, y=y) for x in range(width) for y in range(height)
        }

        zone_map: dict[str, Zone] = {zone.id: zone for zone in zones}
        corridor_map: dict[str, Corridor] = {
            corridor.id: corridor for corridor in (corridors or [])
        }

        for zone in zones:
            for coordinate in zone.cells:
                if coordinate in cells:
                    cells[coordinate].status_flags.add(f"zone:{zone.id}")

        self._state = SpatialState(
            width=width,
            height=height,
            cells=cells,
            zones=zone_map,
            corridors=corridor_map,
            exits=list(exits),
            obstacles=list(obstacles),
            timestamp=datetime.now(timezone.utc),
            metadata={"configured": True},
        )
        self._reconcile_static_markers()
        _ = self.calculate_baseline_metrics()
        return self.get_state_snapshot()

    def calculate_baseline_metrics(self) -> dict[str, dict[str, float]]:
        """Calculates baseline evacuation and stress metrics for all zones."""
        zone_metrics: dict[str, dict[str, float]] = {}
        for zone in self._state.zones.values():
            zone.crowd_density = calculate_crowd_density(zone)
            zone.accessibility = calculate_accessibility(zone)
            zone.noise_level = calculate_noise_level(zone)
            zone.peak_stress = calculate_peak_stress(zone)
            zone.evacuation_time_estimate = calculate_evacuation_time(
                zone, self._state.exits
            )
            zone_metrics[zone.id] = {
                "evacuation_time_estimate": zone.evacuation_time_estimate,
                "crowd_density": zone.crowd_density,
                "peak_stress": zone.peak_stress,
                "accessibility": zone.accessibility,
                "noise_level": zone.noise_level,
            }

        zone_density_by_cell: dict[tuple[int, int], float] = {}
        for zone in self._state.zones.values():
            for coordinate in zone.cells:
                zone_density_by_cell[coordinate] = zone.crowd_density

        for corridor in self._state.corridors.values():
            corridor.capacity = float(max(len(corridor.cells), 1) * 2.0)
            corridor.flow_rate = sum(
                zone_density_by_cell.get(cell, 0.0) for cell in corridor.cells
            )
            if corridor.capacity <= 0:
                corridor.bottleneck_indicator = 0.0
            else:
                corridor.bottleneck_indicator = round(
                    min(corridor.flow_rate / corridor.capacity, 1.0), 4
                )

        self._state.timestamp = datetime.now(timezone.utc)
        return zone_metrics

    def apply_patch(self, patch: dict[str, object]) -> SpatialState:
        """Applies targeted updates and recomputes baseline metrics."""
        cell_updates = patch.get("cell_updates")
        if isinstance(cell_updates, list):
            cell_updates_list = cast(list[object], cell_updates)
            for cell_patch_raw in cell_updates_list:
                if not isinstance(cell_patch_raw, dict):
                    continue
                cell_patch = cast(dict[str, object], cell_patch_raw)
                x = cell_patch.get("x")
                y = cell_patch.get("y")
                if not isinstance(x, int) or not isinstance(y, int):
                    continue

                coordinate = (x, y)
                cell = self._state.cells.get(coordinate)
                if cell is None:
                    continue

                for field_name in (
                    "rigidity",
                    "occupancy_flow",
                    "temperature",
                    "strain",
                    "noise",
                    "fatigue_budget",
                ):
                    value = cell_patch.get(field_name)
                    if isinstance(value, (int, float)):
                        setattr(cell, field_name, float(value))

                add_flags = cell_patch.get("add_flags")
                remove_flags = cell_patch.get("remove_flags")
                if isinstance(add_flags, list):
                    for flag_raw in cast(list[object], add_flags):
                        if isinstance(flag_raw, str):
                            cell.status_flags.add(flag_raw)
                if isinstance(remove_flags, list):
                    for flag_raw in cast(list[object], remove_flags):
                        if isinstance(flag_raw, str):
                            cell.status_flags.discard(flag_raw)

        zone_updates = patch.get("zone_updates")
        if isinstance(zone_updates, dict):
            zone_updates_map = cast(dict[object, object], zone_updates)
            for zone_id, zone_patch_raw in zone_updates_map.items():
                if not isinstance(zone_id, str) or not isinstance(zone_patch_raw, dict):
                    continue
                zone_patch = cast(dict[str, object], zone_patch_raw)
                zone = self._state.zones.get(zone_id)
                if zone is None:
                    continue

                name = zone_patch.get("name")
                if isinstance(name, str):
                    zone.name = name

                cells = zone_patch.get("cells")
                if isinstance(cells, list):
                    parsed_cells: list[tuple[int, int]] = []
                    for coordinate in cast(list[object], cells):
                        if isinstance(coordinate, tuple):
                            coordinate_seq = cast(tuple[object, ...], coordinate)
                            if len(coordinate_seq) != 2:
                                continue
                            x_coord = coordinate_seq[0]
                            y_coord = coordinate_seq[1]
                            if isinstance(x_coord, int) and isinstance(y_coord, int):
                                parsed_cells.append((x_coord, y_coord))
                    zone.cells = parsed_cells

                noise_level = zone_patch.get("noise_level")
                if isinstance(noise_level, (int, float)):
                    zone.noise_level = float(noise_level)

        metadata_patch = patch.get("metadata")
        if isinstance(metadata_patch, dict):
            metadata_map = cast(dict[object, object], metadata_patch)
            self._state.metadata.update(
                {
                    key: value
                    for key, value in metadata_map.items()
                    if isinstance(key, str)
                }
            )

        obstacle_patch = patch.get("obstacles")
        if isinstance(obstacle_patch, list):
            obstacle_list = cast(list[object], obstacle_patch)
            self._state.obstacles = [
                obstacle for obstacle in obstacle_list if isinstance(obstacle, Obstacle)
            ]

        exit_patch = patch.get("exits")
        if isinstance(exit_patch, list):
            exit_list = cast(list[object], exit_patch)
            self._state.exits = [
                exit_obj for exit_obj in exit_list if isinstance(exit_obj, Exit)
            ]

        self._reconcile_static_markers()
        _ = self.calculate_baseline_metrics()
        return self.get_state_snapshot()

    def _reconcile_static_markers(self) -> None:
        """Syncs obstacle and exit markers back into cells."""
        for cell in self._state.cells.values():
            cell.status_flags.discard("obstacle")
            cell.status_flags.discard("exit")
            cell.rigidity = max(cell.rigidity, 0.05)

        for obstacle in self._state.obstacles:
            if obstacle.location in self._state.cells:
                cell = self._state.cells[obstacle.location]
                cell.status_flags.add("obstacle")
                cell.rigidity *= max(0.05, 1.0 - obstacle.blocking_factor * 0.25)

        for exit_obj in self._state.exits:
            if exit_obj.location in self._state.cells:
                self._state.cells[exit_obj.location].status_flags.add("exit")

    def load_example_scenario(self) -> SpatialState:
        """Loads a 20x20 scenario with 3 zones, exits, and obstacles."""
        zones = [
            Zone(
                id="zone1",
                name="Operations",
                cells=[(x, y) for x in range(2, 8) for y in range(2, 8)],
            ),
            Zone(
                id="zone2",
                name="Assembly",
                cells=[(x, y) for x in range(10, 16) for y in range(3, 10)],
            ),
            Zone(
                id="zone3",
                name="Laboratory",
                cells=[(x, y) for x in range(13, 20) for y in range(13, 20)],
            ),
        ]
        exits = [
            Exit(id="exit_main", location=(0, 10), capacity=24.0, is_emergency=False),
            Exit(
                id="exit_emergency", location=(19, 19), capacity=30.0, is_emergency=True
            ),
        ]
        obstacles = [
            Obstacle(
                id="pillar_01", location=(6, 6), type="pillar", blocking_factor=0.6
            ),
            Obstacle(
                id="storage_01", location=(14, 8), type="storage", blocking_factor=0.7
            ),
            Obstacle(
                id="machine_01", location=(16, 16), type="machine", blocking_factor=0.8
            ),
        ]
        return self.configure_map(
            size=(20, 20), zones=zones, exits=exits, obstacles=obstacles
        )

    def get_state_snapshot(self) -> SpatialState:
        """Returns an immutable-style copy of the current state."""
        return self._state.copy()

    @staticmethod
    def diff_states(before: SpatialState, after: SpatialState) -> dict[str, object]:
        """Produces a compact diff between two simulation states."""
        changed_cells: list[dict[str, object]] = []
        for coordinate, before_cell in before.cells.items():
            after_cell = after.cells.get(coordinate)
            if after_cell is None:
                continue
            if asdict(before_cell) != asdict(after_cell):
                changed_cells.append(
                    {
                        "coordinate": coordinate,
                        "before": asdict(before_cell),
                        "after": asdict(after_cell),
                    }
                )

        changed_zones: dict[str, dict[str, object]] = {}
        for zone_id, before_zone in before.zones.items():
            after_zone = after.zones.get(zone_id)
            if after_zone is None:
                continue
            if asdict(before_zone) != asdict(after_zone):
                changed_zones[zone_id] = {
                    "before": asdict(before_zone),
                    "after": asdict(after_zone),
                }

        zone3_target: bool | None = None
        zone3_after = after.zones.get("zone3")
        if zone3_after is not None:
            zone3_target = zone3_after.evacuation_time_estimate <= 12.0

        return {
            "grid_size_before": (before.width, before.height),
            "grid_size_after": (after.width, after.height),
            "changed_cells_count": len(changed_cells),
            "changed_zones_count": len(changed_zones),
            "changed_cells": changed_cells,
            "changed_zones": changed_zones,
            "scenario_checks": {
                "zone3_evacuation_time_leq_12": zone3_target,
            },
            "timestamp_before": before.timestamp.isoformat(),
            "timestamp_after": after.timestamp.isoformat(),
        }
