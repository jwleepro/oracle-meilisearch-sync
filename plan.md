# Phase 01 개발 계획: Oracle-Meilisearch 데이터 동기화

이 문서는 TDD(Test-Driven Development) 방식으로 Phase 01을 구현하기 위한 테스트 계획입니다.
각 테스트 앞의 체크박스는 구현 완료 시 체크합니다.

## 기술 스택
- **데이터 파이프라인**: Python (python-oracledb)
- **검색 엔진**: Meilisearch
- **테스트 프레임워크**: pytest

---

## 1. 프로젝트 설정

### 1.1 개발 환경 설정
- [x] **TEST-001**: pytest 실행 확인 - 빈 테스트가 통과하는지 확인
- [x] **TEST-002**: python-oracledb 패키지 import 가능 확인
- [x] **TEST-003**: meilisearch 패키지 import 가능 확인

---

## 2. 설정 관리 (Config)

### 2.1 환경 설정 로드
- [x] **TEST-010**: 환경 변수에서 Oracle 연결 정보(host, port, service_name, user, password) 로드
- [x] **TEST-011**: 환경 변수에서 Meilisearch 연결 정보(host, api_key) 로드
- [x] **TEST-012**: 필수 환경 변수 누락 시 명확한 에러 메시지 반환
- [x] **TEST-013**: 기본값 설정 (Meilisearch 기본 포트 7700 등)

---

## 3. Oracle 데이터베이스 연결

### 3.1 연결 관리
- [x] **TEST-020**: Oracle DB 연결 객체 생성
- [x] **TEST-021**: Oracle DB 연결 성공 시 연결 객체 반환
- [x] **TEST-022**: Oracle DB 연결 실패 시 적절한 예외 발생
- [x] **TEST-023**: 연결 풀(Connection Pool) 생성 및 관리
- [x] **TEST-024**: 컨텍스트 매니저로 연결 자동 해제

### 3.2 데이터 조회
- [x] **TEST-030**: 단일 테이블에서 전체 레코드 조회
- [x] **TEST-031**: 조회 결과를 딕셔너리 리스트로 변환
- [x] **TEST-032**: 배치 단위로 데이터 조회 (cursor.fetchmany)
- [x] **TEST-033**: 마지막 수정 시간 기준 변경된 레코드만 조회 (Incremental)
- [x] **TEST-034**: NULL 값 처리
- [x] **TEST-035**: Oracle 날짜/시간 타입을 ISO 8601 문자열로 변환

---

## 4. Meilisearch 연결

### 4.1 연결 관리
- [x] **TEST-040**: Meilisearch 클라이언트 생성
- [x] **TEST-041**: Meilisearch 서버 health check
- [x] **TEST-042**: Meilisearch 연결 실패 시 적절한 예외 발생

### 4.2 인덱스 관리
- [x] **TEST-050**: 인덱스 존재 여부 확인
- [x] **TEST-051**: 인덱스 생성 (primary key 지정)
- [x] **TEST-052**: 인덱스 설정 업데이트 (searchable attributes, filterable attributes)
- [x] **TEST-053**: 인덱스 삭제

### 4.3 문서 관리
- [x] **TEST-060**: 단일 문서 추가
- [x] **TEST-061**: 배치 문서 추가 (add_documents)
- [x] **TEST-062**: 문서 업데이트 (upsert 방식)
- [x] **TEST-063**: 문서 삭제
- [x] **TEST-064**: 작업 완료 대기 (wait_for_task)

---

## 5. 동기화 엔진 (Sync Engine)

### 5.1 Full Sync (FR-101)
- [x] **TEST-070**: Oracle에서 전체 데이터 추출
- [x] **TEST-071**: 추출된 데이터를 Meilisearch 문서 형식으로 변환
- [x] **TEST-072**: Meilisearch에 배치 단위로 문서 삽입
- [x] **TEST-073**: Full Sync 완료 후 문서 수 일치 확인
- [x] **TEST-074**: Full Sync 전 기존 인덱스 처리 (삭제 후 재생성 옵션)

### 5.2 Incremental Sync (FR-102)
- [x] **TEST-080**: 마지막 동기화 시점 저장 및 조회
- [x] **TEST-081**: 변경된 레코드만 추출 (수정 시간 기준)
- [x] **TEST-082**: 변경된 레코드 Meilisearch에 upsert
- [x] **TEST-083**: 삭제된 레코드 처리 (soft delete 플래그 기준)
- [x] **TEST-084**: Incremental Sync 후 동기화 시점 업데이트

### 5.3 동기화 실패 처리 (FR-103)
- [x] **TEST-090**: 동기화 실패 시 재시도 (최대 3회)
- [x] **TEST-091**: 재시도 간 지수 백오프(exponential backoff) 적용
- [x] **TEST-092**: 최종 실패 시 에러 정보 기록
- [x] **TEST-093**: 부분 실패 시 실패한 배치 정보 기록

---

## 6. 모니터링 및 로깅 (FR-104)

### 6.1 로깅
- [x] **TEST-100**: 동기화 시작/완료 로그 기록
- [x] **TEST-101**: 동기화 진행률 로그 (처리된 레코드 수)
- [x] **TEST-102**: 에러 발생 시 상세 로그 기록
- [x] **TEST-103**: 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR)

### 6.2 상태 관리
- [x] **TEST-110**: 동기화 상태 저장 (시작 시간, 종료 시간, 처리 건수)
- [x] **TEST-111**: 마지막 성공 동기화 정보 조회
- [x] **TEST-112**: 동기화 히스토리 조회

---

## 7. 스케줄러 통합
- [x] **TEST-120**: 주기적 Incremental Sync 실행
- [x] **TEST-121**: Cron 표현식 파싱

---  

## 8. 통합 테스트

### 8.1 End-to-End 테스트
- [X] **TEST-130**: Oracle 테스트 데이터 → Meilisearch Full Sync → 검색 확인
- [X] **TEST-131**: Oracle 데이터 생성 → Incremental Sync → 변경 반영 확인
- [X] **TEST-132**: 대용량 데이터(10,000건) Full Sync 성능 테스트

---

## 9. 프로덕션 준비
- [X] **TEST-140**: sync_state.json 파일로 시점 저장/로드
- [X] **TEST-141**: 환경 변수 미설정 시 .env 파일 읽기

---

## 비기능 요구사항 검증

### 성능 테스트 (수동)
- [ ] **PERF-001**: 동기화 지연 시간 < 5초 확인 (NFR-102)
- [ ] **PERF-002**: 데이터 정합성 99.99% 확인 (NFR-105)

---

## 구현 순서 가이드

1. **TEST-001 ~ TEST-003**: 프로젝트 기본 설정
2. **TEST-010 ~ TEST-013**: 설정 관리
3. **TEST-020 ~ TEST-035**: Oracle 연결 및 데이터 조회
4. **TEST-040 ~ TEST-064**: Meilisearch 연결 및 문서 관리
5. **TEST-070 ~ TEST-074**: Full Sync 구현
6. **TEST-080 ~ TEST-084**: Incremental Sync 구현
7. **TEST-090 ~ TEST-093**: 에러 처리 및 재시도
8. **TEST-100 ~ TEST-112**: 모니터링 및 로깅
9. **TEST-120 ~ TEST-121**: 스케줄러 통합
10. **TEST-130 ~ TEST-132**: 통합 테스트
11. **TEST-140 ~ TEST-141**: 프로덕션 준비
