# DuckDB Web Application - Harness Plan

**Date:** 2026-04-18  
**Project:** DuckDB-based Data Processing Web Application  
 **Status:** 신규 구축 (New Harness Construction)

---

## Phase 0: 현황 감사

### 현재 상태
- **하네스:** 신규 구축 (`.claude/agents/`, `.claude/skills/` 디렉토리 없음)
- **프로젝트:** DuckDB 기반 데이터 처리 웹 애플리케이션
- **최근 완료:** Excel 파일 지원 구현, 백엔드 테스트 55/55 통과
- **기술 스택:** Python, FastAPI, DuckDB, PostgreSQL, MySQL, pandas, openpyxl
- **아키텍처:**
  - Backend: FastAPI + DuckDB
  - Connectors: CSV, Excel (구현), PostgreSQL/MySQL (존재 but 미연동)
  - API: Workflow execution, Job processing, Authentication
  - Tests: 34개 테스트 파일 (unit, integration, e2e, api)

### 감사 결과
- **불실된 기회:** UI에서 "csv/excel file" 표시되었지만 Excel만 구현 완료
- **미구현 기능:** 
  - `load_database()` - NotImplementedError
  - `load_api()` - NotImplementedError  
  - JSON/JSONL, Parquet 커넥터 미존재
  - 일부 데이터 변환 기능 미완성
- **테스트 현황:** Backend unit tests 55/55 passing ✓

### 실행 계획
**신규 구축 분기** → Phase 1부터 전체 실행

---

## Phase 1: 도메인 분석

### 1-1. 핵심 작업 유형 식별

**1. 데이터 로딩 (Data Ingestion)**
- CSV/Excel 파일 처리
- 데이터베이스 쿼리 (PostgreSQL, MySQL)
- API 데이터 수집
- 파일 형식 변환 (JSON, Parquet)

**2. 데이터 처리 (Data Processing)**
- 필터링, 집계, 피벗팅
- SQL 쿼리 실행
- 스트리밍 처리
- 데이터 변환

**3. 데이터 내보내기 (Data Export)**
- CSV, JSON, Parquet, Excel 내보내기
- DuckDB 데이터베이스 내보내기
- 쿼리 결과 내보내기

**4. 워크플로우 실행 (Workflow Orchestration)**
- 비동기 작업 실행
- 진행 상태 추적
- 결과 관리

### 1-2. 사용자 숙련도 감지
- **사용자:** CJ-1981
- **숙련도:** 고급 (Python 개발자, 데이터 엔지니어링)
- **커뮤니케이션 톤:** 기술적 용어 사용 OK, 구체적 구현 패턴 논의 가능

### 1-3. 기존 MoAI 시스템과의 관계
- 프로젝트 이미 MoAI 시스템 사용 (`/moai`, `/agency` 명령어)
- 기존 에이전트들과 중복 피해야 함
- **하네스 포지셔닝:** MoAI는 일반 작업용, 새 하네스는 데이터 처리 특화

---

## Phase 2: 팀 아키텍처 설계

### 2-1. 실행 모드 선택

**에이전트 팀 (기본 모드)**
- 2명 이상 에이전트 협업 필요 (분석 + 구현)
- 실시간 조율·피드백 중요 (데이터 파이프라인 설계)
- 복잡한 워크플로우 처리

### 2-2. 아키텍처 패턴: **생성-검증-통합**

```
┌─────────────────────────────────────────────────────────┐
│           Orchestrator (리더)                          │
│  - 전체 워크플로우 조율                                │
│  - 팀 구성/작업 할당                                    │
│  - 결과 종합                                            │
└──────────────┬──────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│  Data        │  │  Backend     │
│  Architect   │  │  Developer   │
│  (분석 전문가) │  │  (구현 전문가)│
└──────────────┘  └──────────────┘
       │                │
       └───────┬────────┘
               ▼
       ┌──────────────────┐
       │   Integration    │
       │   Specialist    │
       │  (검증/통합)     │
       └──────────────────┘
```

**역할 분담:**
- **Data Architect:** 도메인 분석, 커넥터 설계, 데이터 모델링
- **Backend Developer:** 커넥터 구현, API 개발, 테스트 작성
- **Integration Specialist:** 통합 테스트, 검증, 문서화

### 2-3. 에이전트 분리 기준

| 에이전트 | 전문성 | 병렬성 | 컨텍스트 | 재사용성 |
|---------|--------|--------|----------|----------|
| Data Architect | 높음 (도메인 지식) | 낮음 (의존적) | 높음 (프로젝트 전체) | 높음 (다른 프로젝트) |
| Backend Developer | 높음 (구현 기술) | 높음 (독립 모듈) | 중간 (코드베이스) | 높음 (표준 패턴) |
| Integration Specialist | 중간 (검증 기술) | 중간 (의존적) | 낮음 (산출물 기반) | 중간 (프로젝트별) |

---

## Phase 3: 에이전트 정의 생성

### 3-1. Data Architect (data-architect.md)

**핵심 역할:**
- 데이터 처리 파이프라인 설계
- 커넥터 아키텍처 정의
- 데이터 모델 및 스키마 설계
- 성능 최적화 가이드

**작업 원칙:**
- DuckDB 최적 활용 패턴 적용
- 메모리 효율적 스트리밍 전략 수립
- 타입 시스템 통합 (INTEGER, FLOAT, BOOLEAN, DATE, VARCHAR)
- NULL 값 처리 표준화

**입력 프로토콜:**
- 사용자 요구사항 (데이터 소스, 변환 요건)
- 기존 데이터베이스 스키마
- 성능 요구사항

**출력 프로토콜:**
- 커넥터 인터페이스 명세
- 데이터 처리 파이프라인 다이어그램
- 스키마 정의서
- 성능 최적화 가이드

### 3-2. Backend Developer (backend-developer.md)

**핵심 역할:**
- 데이터 커넥터 구현 (CSV, Excel, JSON, Parquet, DB)
- FastAPI 엔드포인트 개발
- DuckDB 연동 로직 구현
- 단위/통합 테스트 작성

**작업 원칙:**
- Clean Code 원칙 준수
- Type hints 사용 (Python 3.12+)
- Error handling 구조화
- 로깅 및 모니터링 포함

**입력 프로토콜:**
- Data Architect가 설계한 명세
- API 요구사항
- 기존 코드베이스

**출력 프로토콜:**
- 구현된 커넥터 모듈
- API 엔드포인트
- 테스트 코드
- 구현 문서

### 3-3. Integration Specialist (integration-specialist.md)

**핵심 역할:**
- 커넥터 통합 테스트
- E2E 시나리오 검증
- API 테스트 자동화
- 문서화 및 가이드 작성

**작업 원칙:**
- 경계면 교차 검증 (API 응답 ↔ DB 상태)
- 점진적 QA (각 모듈 완성 시 검증)
- 재현 가능한 테스트 케이스 작성
- 사용자 관점 문서화

**입력 프로토콜:**
- Backend Developer가 구현한 코드
- API 명세서
- 사용자 시나리오

**출력 프로토콜:**
- 통합 테스트 스위트
- E2E 테스트 결과
- 테스트 리포트
- 사용자 가이드

---

## Phase 4: 스킬 생성

### 4-1. Connector Design (skills/connector-design/SKILL.md)

**Description:** 데이터 커넥터 설계, 인터페이스 정의, DuckDB 통합 전략, 타입 추론, NULL 처리, 스트리밍, 성능 최적화. CSV, Excel, JSON, Parquet, PostgreSQL, MySQL 커넥터 설계 시 반드시 사용. 새로운 데이터 소스 통합이 필요하거나 데이터 로딩 아키텍처를 논의할 때 이 스킬을 사용하라. 다시 실행, 재설계, 수정, 보완, 기존 설계 개선 요청 시에도 사용하라.

**본문 구조:**
- 커넥터 인터페이스 표준
- DuckDB 통합 패턴
- 타입 추론 시스템
- NULL 값 처리 전략
- 스트리밍 처리 가이드
- 성능 최적화 기법

### 4-2. Backend Implementation (skills/backend-impl/SKILL.md)

**Description:** FastAPI, DuckDB, pandas, SQLAlchemy를 활용한 데이터 처리 백엔드 구현. 데이터 커넥터, API 엔드포인트, 비동기 작업 처리, 에러 핸들링, 로깅, 테스트 작성, 배포 설정. 데이터 로딩, 변환, 내보내기 기능 구현 시 반드시 사용. 코드 리팩토링, 성능 최적화, 버그 수정 요청 시에도 사용하라. 기존 구현 다시 실행, 수정, 보완 시에도 사용하라.

**본문 구조:**
- 프로젝트 구조 표준
- 커넥터 구현 패턴
- API 엔드포인트 설계
- 비동기 처리 (Celery/asyncio)
- 에러 핸들링 프레임워크
- 테스트 전략
- 배포 및 운영

### 4-3. Integration Testing (skills/integration-test/SKILL.md)

**Description:** 통합 테스트, E2E 테스트, API 테스트 작성 및 실행. pytest, requests, TestClient 사용. 경계면 교차 검증, 재현 가능한 테스트 케이스, 테스트 리포트 작성. 커넥터 통합 검증, API 응답 검증, 전체 시스템 동작 확인 시 반드시 사용. 테스트 실패 분석, 재시 작성, 테스트 커버리지 개선 시에도 사용하라. 다시 테스트, 추가 테스트 요청 시에도 사용하라.

**본문 구조:**
- pytest 프로젝트 구조
- 단위/통합/E2E 테스트 작성
- API 테스트 패턴
- 데이터베이스 테스트 전략
- 경계면 검증 기법
- 테스트 리포팅
- CI/CD 연동

---

## Phase 5: 통합 및 오케스트레이션

### 5-1. 오케스트레이터 스킬 구조

**실행 모드:** 에이전트 팀

**데이터 전달 프로토콜:**
- 태스크 기반 (TaskCreate/TaskUpdate) - 작업 할당 및 상태 추적
- 파일 기반 - `_workspace/` 디렉토리에 중간 산출물 저장
- 메시지 기반 (SendMessage) - 실시간 협업 및 피드백

### 5-2. 워크플로우 단계

**Phase 0: 컨텍스트 확인**
- `_workspace/` 존재 여부 확인
- 사용자 요청 유형 파악 (신규/수정/확장)
- 기존 산출물 확인

**Phase 1: 도메인 분석**
- 사용자 요구사항 수집
- 기술 제약 사항 확인
- Data Architect에게 도메인 분석 요청

**Phase 2: 아키텍처 설계**
- Data Architect가 커넥터 설계
- 데이터 파이프라인 정의
- Backend Developer가 구현 계획 수립

**Phase 3: 구현**
- Backend Developer가 커넥터/API 구현
- Integration Specialist가 테스트 준비

**Phase 4: 검증**
- Integration Specialist가 통합 테스트 실행
- 버그 발견 시 Backend Developer에게 수정 요청
- 모든 테스트 통과 시 완료

**Phase 5: 통합**
- 전체 시스템 통합 확인
- 문서화 완료
- 사용자 전달

### 5-3. 에러 핸들링

- **Data Architect 오류:** Orchestrator가 직접 해결 시도 후 실패 시 사용자에게 보고
- **Backend Developer 오류:** Integration Specialist가 버그 상세를 수집하여 수정 요청
- **Integration Specialist 오류:** Orchestrator가 대안 방안 제시

### 5-4. 팀 크기
- **소규모:** 2명 (Data Architect + Backend Developer)
- **중규모:** 3명 (Integration Specialist 추가)

---

## Phase 6: 검증 및 테스트

### 6-1. 구조 검증
- [ ] `.claude/agents/` 디렉토리 생성
- [ ] 에이전트 정의 파일 3개 생성
- [ ] `.claude/skills/` 디렉토리 생성
- [ ] 스킬 파일 3개 생성 (SKILL.md + references/)

### 6-2. 트리거 검증

**Connector Design 스킬:**
- Should-trigger: "커넥터 설계해줘", "데이터 소스 연동 방법", "데이터 파이프라인"
- Should-NOT-trigger: "프론트엔드 디자인", "UI 구현"

**Backend Implementation 스킬:**
- Should-trigger: "API 구현", "커넥터 개발", "데이터 로딩 기능"
- Should-NOT-trigger: "데이터 분석", "비즈니스 로직"

**Integration Testing 스킬:**
- Should-trigger: "테스트 작성", "통합 검증", "E2E 테스트"
- Should-NOT-trigger: "기능 구현", "아키텍처 설계"

### 6-3. 실행 테스트 시나리오

**시나리오 1: 새 커넥터 추가 (JSON)**
1. 사용자: "JSON 파일 지원 추가해줘"
2. Orchestrator: Data Architect → 설계 요청
3. Data Architect: JSON 커넥터 인터페이스 설계
4. Backend Developer: JSONConnector 구현
5. Integration Specialist: 테스트 작성 및 검증
6. 결과: JSON 지원 완료, 테스트 통과

**시나리오 2: 데이터베이스 로딩 구현**
1. 사용자: "PostgreSQL에서 데이터 로딩하게 해줘"
2. Orchestrator: Data Architect → 아키텍처 분석
3. Backend Developer: load_database() 구현
4. Integration Specialist: 통합 테스트
5. 결과: DB 로딩 완료, 테스트 통과

---

## Phase 7: 하네스 진화

### 7-1. 피드백 수집 주기
- 각 완료 후: "결과에서 개선할 부분이 있나요?"
- 에이전트 성능 조정: "에이전트 역할 분리가 적절한가요?"

### 7-2. 진화 방향
- **단기:** JSON/Parquet 커넥터 추가
- **중기:** API 데이터 로딩 구현
- **장기:** 고급 분석 기능, 시각화 도구

### 7-3. 변경 이력 템플릿

```markdown
**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-04-18 | 초기 구성 | 전체 | 데이터 처리 특화 하네스 신규 구축 |
```

---

## CLAUDE.md 등록 내용

```markdown
## 하네스: Data Processing Orchestrator

**목표:** DuckDB 기반 데이터 처리 웹 애플리케이션의 데이터 로딩, 변환, 내보내기 기능을 전문화된 에이전트 팀이 체계적으로 구현하고 검증합니다.

**트리거:** 데이터 커넥터 설계/구현, 데이터 파이프라인 아키텍처, 통합 테스트, 데이터 처리 기능 개발 요청 시 `data-processing-orchestrator` 스킬을 사용하라. 단순 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-04-18 | 초기 구성 | 전체 | 데이터 처리 특화 하네스 신규 구축 |
```

---

## 다음 단계

1. **구현 계획 확인:** `IMPLEMENTATION_PLAN.md` 참조
   - Sprint 1: Quick Wins (DB, JSON/JSONL)
   - Sprint 2: Core Features (API, Parquet, Transformations)
   - Sprint 3: Quality & Documentation

2. **우선순위 선택:** 
   - ✅ Test Suite Health Check → 먼저 실행
   - ✅ Database Loading → PostgreSQL/MySQL 연동
   - ✅ JSON/JSONL → pandas 기반 간단 구현

3. **첫 번째 작업:**
   - 전체 테스트 스위트 실행 → 현황 파악
   - Database connector 연동 → 빠른 완료 가능
   - JSON 커넥터 → 사용도 높음

**관련 문서:**
- 상세 구현 계획: `IMPLEMENTATION_PLAN.md`
- 하네스 아키텍처: 본 문서

이 계획대로 구현을 시작할까요?
