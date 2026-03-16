# HAF-9_Studio

![HAF-9_Studio](https://img.shields.io/badge/HAF--9-Studio-v0.1.0-06b6d4)
![Python](https://img.shields.io/badge/Python-3.12+-blue)
![React](https://img.shields.io/badge/React-18.2-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)

## 프로젝트 개요

HAF-9_Studio (Holozyme Architecture Fabric)는 프로그래밍 가능한 공간 운영 체제입니다. 건물을 패치 가능하고 적응적이며 안전이 보장되는 계산 환경으로 모델링합니다.

이 소프트웨어는 현재 물리적으로 존재하지 않는 mágica 재료를 가정하지 않습니다. 대신, 프로그래밍 가능한 건축 물질과 적응형 인프라가 어떻게 동작할 것인지를 시뮬레이션하는 현실적인 디지털 트윈 + 의도 컴파일러 + 패치 플래너 + 안전 검증기 + 포렌식 원장 플랫폼을 구현합니다.

## 핵심 기능

### 1. 자연어 인텐트 처리
- 자연어로 의도를 입력하면 시스템이 자동으로 구조화된 DSL과 제약 IR로 변환
- 모호성 감지 및 경고 기능
- 불명확한 인텐트는 인계 검토 요청

### 2. 2D 공간 디지털 트윈
- 20x20 그리드 기반 시뮬레이션
- 존, 출구, 복도, 장애물 모델링
- 실시간 메트릭 계산 (대피 시간, 인구 밀도, 스트레스 등)

### 3. 패치 플래너
- 여러 후보 패치 자동 생성
- 각 패치의 예상 효과 및 리스크 평가
- 우선순위 기반 순위화

### 4. 안전성 검증기
- 구조적 불변조건 검사
- 대피invariants 검증
- 접근성invariants 확인
- 결정: 승인/거부/인계 검토/샌드박스 전용

### 5. 포렌식 원장
- 모든 이벤트 추적 (인텐트 수신 → 파싱 → DSL → IR → 패치 → 검증 → 적용)
- 완전한 감사 추적
- 리플레이 기능

## 아키텍처

```
HAF-9_Studio/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 라우트
│   │   ├── domain/       # 도메인 모델 (Cell, Zone, Exit, etc.)
│   │   ├── simulation/   # 2D 그리드 시뮬레이션
│   │   ├── services/     # 인텐트 파서, DSL/IR 컴파일러, 패치 플래너
│   │   ├── ledger/       # 포렌식 원장
│   │   └── replay/       # 리플레이 엔진
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React 컴포넌트
│   │   ├── services/     # API 클라이언트
│   │   └── App.tsx       # 메인 앱
│   └── package.json
├── docs/                 # 기술 문서
└── examples/             # 예시 시나리오
```

## 시작하기

### 필수 요구사항

- Python 3.12+
- Node.js 18+
- npm 또는 yarn

### 설치

1. 백엔드 설치:
```bash
cd HAF9_Studio/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. 프론트엔드 설치:
```bash
cd HAF9_Studio/frontend
npm install
```

### 실행

1. 백엔드 실행:
```bash
cd HAF9_Studio/backend
uvicorn app.main:app --reload --port 8000
```

2. 프론트엔드 실행 (새 터미널):
```bash
cd HAF9_Studio/frontend
npm run dev
```

3. 브라우저에서 접속:
```
http://localhost:3000
```

## 예시 시나리오

시스템에는 기본 예시 시나리오가 포함되어 있습니다:

- 20x20 그리드
- 3개 존 (Operations, Assembly, Laboratory)
- 2개 출구 (주 출구, 긴급 출구)
- 여러 장애물

**테스트 인텐트:**
```
"Reduce evacuation time in zone3 to under 12 seconds while maintaining structural safety"
```

이 인텐트는:
1. 파싱되어 구조화된 인텐트로 변환
2. DSL로 컴파일
3. 제약 IR로 변환
4. 여러 패치 후보 생성
5. 안전성 검증
6. 승인 시 패치 적용

## API 엔드포인트

### 시뮬레이션
- `POST /api/simulation/load-example` - 예시 시나리오 로드
- `GET /api/simulation/state` - 현재 상태 조회
- `GET /api/simulation/metrics` - 메트릭 조회

### 인텐트 처리
- `POST /api/intent/parse` - 인텐트 파싱
- `POST /api/dsl/compile` - DSL 컴파일
- `POST /api/ir/compile` - IR 컴파일

### 패치
- `POST /api/patches/generate` - 패치 후보 생성
- `POST /api/patches/{id}/verify` - 패치 검증
- `POST /api/patches/{id}/apply` - 패치 적용

### 원장 및 리플레이
- `GET /api/ledger` - 원장 조회
- `GET /api/replay/timeline` - 타임라인 조회

## 개발 현황

현재 MVP 단계입니다. 다음 기능들이 계획되어 있습니다:

- 3D 시뮬레이션 지원
- CAD/BIM 통합
- IoT 센서 연동
- 액추에이터 연동
- 실시간 데이터 시각화

## 라이선스

MIT License

## 기여자

HAF-9 Development Team
