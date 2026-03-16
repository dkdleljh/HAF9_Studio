# HAF-9_Studio 아키텍처

## 개요

HAF-9_Studio는 프로그래밍 가능한 공간 운영 체제로, 건물 모델을 패치 가능하고 적응적이며 안전이 보장되는 계산 환경으로 모델링합니다.

## 설계 원칙

### 1. 계층형 아키텍처

시스템은 명확하게 분리된 계층으로 구성됩니다:

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│         (React Frontend)                │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│            API Layer                    │
│          (FastAPI)                      │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│          Service Layer                  │
│  Intent Parser → DSL/IR → Patch Planner │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│        Simulation Layer                 │
│      (Grid Simulation)                  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│          Domain Layer                   │
│   Cell, Zone, Corridor, Exit, etc.     │
└─────────────────────────────────────────┘
```

### 2. 단방향 데이터 흐름

데이터는 항상 한 방향으로 흐릅니다:
1. 사용자 입력 → 인텐트 파서
2. 파서 → DSL 컴파일러
3. DSL → IR 컴파일러
4. IR → 패치 플래너
5. 패치 → 안전성 검증기
6. 검증 → 시뮬레이션 적용

### 3. 불변조건 우선

모든 패치 적용 전에 안전성 검증이 필수입니다. 불변조건이 위반되면 패치가 거부됩니다.

## 핵심 모듈

### Domain Layer (`backend/app/domain/`)

도메인 모델을 포함합니다:
- **Cell**: 개별 그리드 셀의 상태
- **Zone**: 논리적 공간 영역
- **Corridor**: 이동 통로
- **Exit**: 긴급 출구
- **Obstacle**: 장애물
- **SpatialState**: 전체 공간 상태 스냅샷

### Simulation Layer (`backend/app/simulation/`)

시뮬레이션 엔진:
- **GridSimulation**: 2D 그리드 관리 및 메트릭 계산
- **Metrics**: 대피 시간, 인구 밀도, 스트레스 등 계산

### Service Layer (`backend/app/services/`)

핵심 비즈니스 로직:
- **IntentParser**: 자연어 파싱
- **DSLCompiler**: DSL 생성
- **IRCompiler**: IR 컴파일
- **PatchPlanner**: 패치 후보 생성
- **SafetyVerifier**: 안전성 검증

### Ledger Layer (`backend/app/ledger/`)

감사 및 추적:
- **ForensicLedger**: 이벤트 로깅
- **ReplayEngine**: 리플레이 기능

## API 설계

RESTful API로 설계되었습니다:

### 시뮬레이션 엔드포인트
- `POST /api/simulation/load-example` - 예시 로드
- `GET /api/simulation/state` - 상태 조회
- `GET /api/simulation/metrics` - 메트릭 조회

### 인텍스트 처리 엔드포인트
- `POST /api/intent/parse` - 인텍스트 파싱
- `POST /api/dsl/compile` - DSL 컴파일
- `POST /api/ir/compile` - IR 컴파일
- `POST /api/patches/generate` - 패치 생성
- `POST /api/patches/{id}/verify` - 검증
- `POST /api/patches/{id}/apply` - 적용

### 원장 엔드포인트
- `GET /api/ledger` - 원장 조회
- `GET /api/replay/timeline` - 타임라인

## 확장성

### 3D 확장

현재 2D 그리드로 구현되어 있으나, 3D로의 확장이 고려된 설계입니다:
- Cell → Voxel
- Grid → Volume
- z축 좌표 추가

### IoT 연동

iot_sensor 모듈을 통해 실제 센서 데이터 연동 가능

### CAD/BIM 통합

dxf atau IFC 파일 importer 추가 예정

## 기술 스택

- **백엔드**: Python 3.12+, FastAPI
- **프론트엔드**: React 18, TypeScript, TailwindCSS
- **시뮬레이션**: Python (numpy 기반)
- **API**: RESTful + JSON

## 보안

- 자연어 입력은 직접 세계 상태를 변이하지 않음
- 모든 변이는 안전성 검증을 통과해야 함
- 포렌식 원장을 통해 모든 작업이 추적됨
