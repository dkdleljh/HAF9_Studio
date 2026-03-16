# HAF-9_Studio 문서 인덱스

HAF-9_Studio에 오신 것을 환영합니다. 이 문서들은 시스템의 모든 측면을 설명합니다.

## 시작하기

- **[README.md](../README.md)** - 프로젝트 개요, 설치, 실행 방법
- **[USER_GUIDE.md](./USER_GUIDE.md)** - 운영자 사용 가이드

## 기술 문서

- **[architecture.md](./architecture.md)** - 시스템 아키텍처 및 설계 원칙
- **[domain_model.md](./domain_model.md)** - 도메인 모델 (Cell, Zone, Corridor, Exit, Obstacle)
- **[intent_dsl.md](./intent_dsl.md)** - 인텐트 DSL 스키마 및 예제
- **[constraint_ir.md](./constraint_ir.md)** - 제약 IR (Intermediate Representation)
- **[safety_policy.md](./safety_policy.md)** - 안전성 검증 정책 및 규칙
- **[ledger_spec.md](./ledger_spec.md)** - 포렌식 원장 사양
- **[roadmap.md](./roadmap.md)** - 개발 로드맵

## 빠른 링크

### 백엔드
- 메인 앱: `backend/app/main.py`
- 도메인 모델: `backend/app/domain/spatial.py`
- 시뮬레이션: `backend/app/simulation/grid.py`
- 인텐트 파서: `backend/app/services/intent_parser.py`
- 패치 플래너: `backend/app/services/patch_planner.py`

### 프론트엔드
- 메인 앱: `frontend/src/App.tsx`
- API 클라이언트: `frontend/src/services/api.ts`
- 그리드 뷰: `frontend/src/components/GridView.tsx`

## 예시

예시 시나리오는 `examples/` 폴더에서 확인하세요.

## 지원

문제나 질문이 있으시면 GitHub Issues를 사용해주세요.
