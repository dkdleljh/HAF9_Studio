# 도메인 모델 문서

HAF-9_Studio의 핵심 도메인 모델을 설명합니다.

## 공간 엔티티

### Cell (셀)

2D 그리드의最小的 단위입니다.

```python
@dataclass
class Cell:
    x: int                    # X 좌표
    y: int                    # Y 좌표
    rigidity: float = 1.0     # 강성 (0.05 - 2.0)
    occupancy_flow: float = 0.0  # 점유 흐름
    temperature: float = 22.0 # 온도 (Celcius)
    strain: float = 0.0        # 변형률 (0 - 1)
    noise: float = 0.0         # 소음 수준
    fatigue_budget: float = 1.0  # 피로 예산
    status_flags: set[str] = set()  # 상태 플래그
```

### Zone (존)

논리적으로 그룹화된 셀의集合입니다.

```python
@dataclass
class Zone:
    id: str                        # 존 ID
    name: str                      # 존 이름
    cells: list[GridCoordinate]    # 구성 셀 좌표
    evacuation_time_estimate: float = 0.0  # 대피 시간 추정치
    crowd_density: float = 0.0    # 인구 밀도
    peak_stress: float = 0.0      # 피크 스트레스
    accessibility: float = 1.0    # 접근성 (0 - 1)
    noise_level: float = 0.0      # 소음 수준
```

### Corridor (복도)

셀들을 연결하는 이동 통로입니다.

```python
@dataclass
class Corridor:
    id: str
    cells: list[GridCoordinate]    # 통과하는 셀
    capacity: float = 0.0          # 용량
    flow_rate: float = 0.0         # 유동율
    bottleneck_indicator: float = 0.0  # 병목 지표
```

### Exit (출구)

건물 egress 점입니다.

```python
@dataclass
class Exit:
    id: str
    location: GridCoordinate       # 위치 (x, y)
    capacity: float                # 처리 용량
    is_emergency: bool = False     # 긴급 출구 여부
```

### Obstacle (장애물)

이동을 방해하는 개체입니다.

```python
@dataclass
class Obstacle:
    id: str
    location: GridCoordinate
    type: str                       # 장애물 유형 (pillar, storage, machine)
    blocking_factor: float = 1.0   # 차단 계수 (0 - 1)
```

## 상태 표현

### SpatialState

전체 시뮬레이션 상태를 나타냅니다.

```python
@dataclass
class SpatialState:
    width: int                              # 그리드 너비
    height: int                             # 그리드 높이
    cells: dict[GridCoordinate, Cell]      # 모든 셀
    zones: dict[str, Zone]                  # 모든 존
    corridors: dict[str, Corridor]          # 모든 복도
    exits: list[Exit]                       # 모든 출구
    obstacles: list[Obstacle]               # 모든 장애물
    timestamp: datetime                     # 타임스탬프
    metadata: dict                          # 추가 메타데이터
```

## 그리드 좌표

```python
GridCoordinate = tuple[int, int]  # (x, y)
```

## 메트릭

### 계산되는 메트릭

각 존에 대해 다음이 계산됩니다:

1. **evacuation_time_estimate**: 대피 시간 추정치 (초)
2. **crowd_density**: 인구 밀도 (0 - 1)
3. **peak_stress**: 피크 스트레스 (0 - 1)
4. **accessibility**: 접근성 (0 - 1)
5. **noise_level**: 소음 수준 (dB)

### 계산 공식

```python
# 대피 시간
evacuation_time = (distance * 0.85 + throughput_penalty * 5.0) * density_factor

# 인구 밀도
crowd_density = min(len(cells) / 64.0, 1.0)

# 피크 스트레스
peak_stress = density * 0.6 + (1 - accessibility) * 0.25 + (noise / 100) * 0.15

# 접근성
accessibility = 1.0 - min(spread / 180.0, 0.65)

# 소음
noise = base_noise + crowd_density * 45.0
```
