# Plan: Oracle-Meilisearch Sync Agent (Phase 1)

> TDD 방식으로 개발합니다. 각 테스트를 순서대로 구현하고, 완료 시 `[x]`로 마킹합니다.

---

## 0. 프로젝트 초기화

- [ ] **T0.1**: Go 모듈 초기화 및 기본 프로젝트 구조 생성

---

## 1. 설정 관리 (Config)

- [ ] **T1.1**: `LoadConfig`가 환경변수에서 Oracle DSN을 읽어온다
- [ ] **T1.2**: `LoadConfig`가 환경변수에서 Meilisearch URL을 읽어온다
- [ ] **T1.3**: `LoadConfig`가 환경변수에서 Meilisearch API Key를 읽어온다
- [ ] **T1.4**: `LoadConfig`가 필수 설정 누락 시 에러를 반환한다
- [ ] **T1.5**: `LoadConfig`가 폴링 주기 기본값(3초)을 설정한다
- [ ] **T1.6**: `LoadConfig`가 배치 크기 기본값(1000)을 설정한다

---

## 2. Oracle 연결 (Repository)

- [ ] **T2.1**: `OracleRepository`가 연결 문자열로 Oracle에 연결한다
- [ ] **T2.2**: `OracleRepository.Ping`이 연결 상태를 확인한다
- [ ] **T2.3**: `OracleRepository.Close`가 연결을 정상 종료한다

---

## 3. Meilisearch 연결 (Client)

- [ ] **T3.1**: `MeilisearchClient`가 URL과 API Key로 클라이언트를 생성한다
- [ ] **T3.2**: `MeilisearchClient.Health`가 Meilisearch 상태를 확인한다
- [ ] **T3.3**: `MeilisearchClient.CreateIndex`가 인덱스를 생성한다
- [ ] **T3.4**: `MeilisearchClient.CreateIndex`가 이미 존재하는 인덱스에 대해 에러 없이 처리한다

---

## 4. 데이터 조회 (Oracle → 도메인 모델)

- [ ] **T4.1**: `OracleRepository.FetchAll`이 CRASIVTTST 테이블의 모든 레코드를 조회한다
- [ ] **T4.2**: `OracleRepository.FetchAll`이 배치 크기 단위로 레코드를 반환한다
- [ ] **T4.3**: `OracleRepository.FetchUpdatedSince`가 특정 시간 이후 변경된 레코드를 조회한다
- [ ] **T4.4**: `OracleRepository.FetchUpdatedSince`가 빈 결과에 대해 빈 슬라이스를 반환한다

---

## 5. Full Sync (FR-01)

- [ ] **T5.1**: `SyncService.FullSync`가 Oracle의 모든 데이터를 Meilisearch에 색인한다
- [ ] **T5.2**: `SyncService.FullSync`가 배치 단위로 데이터를 전송한다
- [ ] **T5.3**: `SyncService.FullSync`가 진행 상황을 로깅한다
- [ ] **T5.4**: `SyncService.FullSync`가 실패 시 에러를 반환한다

---

## 6. Incremental Sync (FR-02)

- [ ] **T6.1**: `SyncService.IncrementalSync`가 마지막 동기화 시점 이후 변경된 데이터를 동기화한다
- [ ] **T6.2**: `SyncService.IncrementalSync`가 마지막 동기화 시점을 저장한다
- [ ] **T6.3**: `SyncService.IncrementalSync`가 변경된 레코드가 없으면 아무 작업도 하지 않는다

---

## 7. Soft Delete 동기화 (FR-05)

- [ ] **T7.1**: `OracleRepository.FetchDeletedSince`가 삭제 플래그가 설정된 레코드를 조회한다
- [ ] **T7.2**: `SyncService.SyncDeletes`가 삭제된 레코드를 Meilisearch에서 제거한다
- [ ] **T7.3**: `SyncService.IncrementalSync`가 삭제 동기화를 포함한다

---

## 8. Meilisearch 문서 관리

- [ ] **T8.1**: `MeilisearchClient.AddDocuments`가 문서 배열을 인덱스에 추가한다
- [ ] **T8.2**: `MeilisearchClient.AddDocuments`가 기존 문서를 업데이트한다 (upsert)
- [ ] **T8.3**: `MeilisearchClient.DeleteDocument`가 ID로 문서를 삭제한다
- [ ] **T8.4**: `MeilisearchClient.DeleteDocuments`가 여러 ID로 문서들을 삭제한다

---

## 9. 검색 기능 (FR-06, FR-08, FR-09)

- [ ] **T9.1**: `SearchService.Search`가 키워드로 문서를 검색한다
- [ ] **T9.2**: `SearchService.Search`가 필터 조건을 적용한다
- [ ] **T9.3**: `SearchService.Search`가 정렬 조건을 적용한다
- [ ] **T9.4**: `SearchService.Search`가 페이지네이션을 지원한다 (offset, limit)
- [ ] **T9.5**: `SearchService.Search`가 총 결과 수를 반환한다

---

## 10. 스케줄러 (Polling)

- [ ] **T10.1**: `Scheduler`가 설정된 주기로 `IncrementalSync`를 실행한다
- [ ] **T10.2**: `Scheduler`가 graceful shutdown을 지원한다
- [ ] **T10.3**: `Scheduler`가 동기화 실패 시 다음 주기에 재시도한다

---

## 11. 상태 관리

- [ ] **T11.1**: `StateStore`가 마지막 동기화 시점을 파일에 저장한다
- [ ] **T11.2**: `StateStore`가 마지막 동기화 시점을 파일에서 읽어온다
- [ ] **T11.3**: `StateStore`가 파일이 없으면 zero time을 반환한다

---

## 12. Health Check

- [ ] **T12.1**: `HealthChecker`가 Oracle 연결 상태를 확인한다
- [ ] **T12.2**: `HealthChecker`가 Meilisearch 연결 상태를 확인한다
- [ ] **T12.3**: `HealthChecker`가 전체 상태를 JSON으로 반환한다

---

## 13. HTTP API (관리용)

- [ ] **T13.1**: `GET /health`가 시스템 상태를 반환한다
- [ ] **T13.2**: `POST /sync/full`이 Full Sync를 트리거한다
- [ ] **T13.3**: `POST /sync/incremental`이 Incremental Sync를 트리거한다
- [ ] **T13.4**: `GET /sync/status`가 마지막 동기화 상태를 반환한다

---

## 14. 메인 애플리케이션

- [ ] **T14.1**: `main`이 설정을 로드하고 의존성을 초기화한다
- [ ] **T14.2**: `main`이 HTTP 서버와 스케줄러를 동시에 실행한다
- [ ] **T14.3**: `main`이 SIGINT/SIGTERM에 graceful shutdown한다

---

## 완료 기준

- 모든 테스트가 `[x]`로 마킹됨
- `go test ./...` 통과
- `go build` 성공
- 린터 경고 없음
