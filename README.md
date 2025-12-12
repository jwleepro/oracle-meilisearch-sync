# oracle-meilisearch-sync
Oracle DB를 Meilisearch로 동기화하는 프로젝트

## 개요
Oracle 11g 데이터베이스의 데이터를 Meilisearch 검색 엔진으로 동기화하여 빠르고 유연한 검색 경험을 제공합니다.

## 설정 방법

### 환경 변수 설정

프로젝트는 환경 변수 또는 `.env` 파일을 통해 설정을 로드합니다.

#### Option 1: .env 파일 사용 (권장)

1. `.env.example` 파일을 복사하여 `.env` 파일 생성:
   ```bash
   cp .env.example .env
   ```

2. `.env` 파일을 편집하여 실제 값 입력:
   ```bash
   # Oracle Database Configuration
   ORACLE_HOST=your-oracle-host.example.com
   ORACLE_PORT=1521
   ORACLE_SERVICE_NAME=XEPDB1
   ORACLE_USER=your-username
   ORACLE_PASSWORD=your-password

   # Meilisearch Configuration
   MEILISEARCH_HOST=http://localhost:7700
   MEILISEARCH_API_KEY=your-master-key
   ```

3. 프로그램 실행 시 자동으로 `.env` 파일이 로드됩니다.

#### Option 2: 환경 변수 직접 설정

```bash
# Linux/macOS
export ORACLE_HOST=your-oracle-host.example.com
export ORACLE_PORT=1521
export ORACLE_SERVICE_NAME=XEPDB1
export ORACLE_USER=your-username
export ORACLE_PASSWORD=your-password
export MEILISEARCH_HOST=http://localhost:7700
export MEILISEARCH_API_KEY=your-master-key

# Windows (PowerShell)
$env:ORACLE_HOST="your-oracle-host.example.com"
$env:ORACLE_PORT="1521"
$env:ORACLE_SERVICE_NAME="XEPDB1"
$env:ORACLE_USER="your-username"
$env:ORACLE_PASSWORD="your-password"
$env:MEILISEARCH_HOST="http://localhost:7700"
$env:MEILISEARCH_API_KEY="your-master-key"
```

**참고**: 환경 변수가 설정되어 있으면 `.env` 파일보다 우선합니다.

## 테스트 실행

### 단위 테스트 (Unit Tests)
모든 단위 테스트 실행 (Oracle/Meilisearch 서버 불필요):
```bash
pytest tests/ -m "not integration" -v
```

### 통합 테스트 (Integration Tests)

**중요**: 통합 테스트는 실제 Oracle과 Meilisearch 인스턴스가 필요합니다.

#### 1. 테스트 DB 환경 (개발/테스트용)
Oracle 테스트 DB에서 테이블 생성/삭제 권한이 있는 경우:

```bash
# 환경 변수 설정
export ORACLE_HOST=localhost
export ORACLE_PORT=1521
export ORACLE_SERVICE_NAME=XEPDB1
export ORACLE_USER=testuser
export ORACLE_PASSWORD=testpass
export MEILISEARCH_HOST=http://localhost:7700
export MEILISEARCH_API_KEY=masterKey

# 테스트 실행
pytest tests/test_integration.py -m "requires_test_db" -v
```

#### 2. 읽기 전용 DB 환경 (운영용)
Oracle 운영 DB에서 SELECT 권한만 있는 경우:

**사전 준비** (DBA가 실행):
```sql
-- 테스트용 테이블 생성
CREATE TABLE SYNC_TEST_USERS (
    id NUMBER PRIMARY KEY,
    name VARCHAR2(100),
    email VARCHAR2(100),
    status VARCHAR2(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 테스트 데이터 삽입
INSERT INTO SYNC_TEST_USERS (id, name, email, status) VALUES
    (1, 'Alice Johnson', 'alice@example.com', 'active');
INSERT INTO SYNC_TEST_USERS (id, name, email, status) VALUES
    (2, 'Bob Smith', 'bob@example.com', 'active');
INSERT INTO SYNC_TEST_USERS (id, name, email, status) VALUES
    (3, 'Charlie Brown', 'charlie@example.com', 'inactive');
INSERT INTO SYNC_TEST_USERS (id, name, email, status) VALUES
    (4, 'Diana Prince', 'diana@example.com', 'active');
INSERT INTO SYNC_TEST_USERS (id, name, email, status) VALUES
    (5, 'Eve Wilson', 'eve@example.com', 'active');
COMMIT;

-- 동기화 계정에 조회 권한 부여
GRANT SELECT ON SYNC_TEST_USERS TO sync_readonly;
```

**테스트 실행**:
```bash
# 환경 변수 설정
export ORACLE_HOST=production-oracle.example.com
export ORACLE_PORT=1521
export ORACLE_SERVICE_NAME=PROD
export ORACLE_USER=sync_readonly
export ORACLE_PASSWORD=readonly_pass
export ORACLE_TEST_TABLE=SYNC_TEST_USERS
export MEILISEARCH_HOST=http://localhost:7700
export MEILISEARCH_API_KEY=masterKey

# 테스트 실행
pytest tests/test_integration.py -m "requires_read_only_db" -v
```

#### 3. 모든 통합 테스트 실행
```bash
pytest tests/test_integration.py -m integration -v
```

## Oracle 권한 제약사항

⚠️ **중요**: 운영 환경에서는 Oracle DB에 **읽기 전용(SELECT) 권한만** 부여됩니다.

- ✅ 허용: `SELECT` 쿼리
- ❌ 금지: `CREATE`, `INSERT`, `UPDATE`, `DELETE`, `DROP`

이는 원본 데이터의 무결성을 보호하고 Oracle DB를 SSOT(Single Source of Truth)로 유지하기 위함입니다.

## 프로젝트 구조
```
oracle-meilisearch-sync/
├── src/
│   ├── oracle.py              # Oracle 연결 및 데이터 조회
│   ├── meilisearch_client.py  # Meilisearch 클라이언트
│   ├── sync_engine.py         # 동기화 엔진
│   └── config.py              # 설정 관리
├── tests/
│   ├── test_oracle.py         # Oracle 단위 테스트
│   ├── test_meilisearch.py    # Meilisearch 단위 테스트
│   ├── test_sync_engine.py    # 동기화 엔진 단위 테스트
│   └── test_integration.py    # 통합 테스트
├── docs/
│   └── Phase 01/
│       └── prd.md            # 제품 요구사항 문서
└── plan.md                   # TDD 테스트 계획