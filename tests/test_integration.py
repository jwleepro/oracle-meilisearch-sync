"""
Integration Tests

These tests require actual Oracle and Meilisearch instances running.

Test Markers:
- integration: All integration tests
- requires_test_db: Requires Oracle test DB with full privileges (CREATE, INSERT, DROP)
- requires_read_only_db: Requires Oracle production DB with SELECT-only privileges

Run examples:
  pytest tests/test_integration.py -m integration                    # All integration tests
  pytest tests/test_integration.py -m "requires_test_db"             # Test DB only
  pytest tests/test_integration.py -m "requires_read_only_db"        # Read-only DB only

TEST-120: Oracle 테스트 데이터 → Meilisearch Full Sync → 검색 확인
  - test_end_to_end_full_sync_with_test_data_creation: 테스트 DB용 (데이터 생성)
  - test_end_to_end_full_sync_with_existing_data: 운영 DB용 (기존 데이터 사용)
TEST-121: Oracle 데이터 변경 → Incremental Sync → 변경 반영 확인
TEST-122: 대용량 데이터(10,000건) Full Sync 성능 테스트
"""
import pytest
import os
from datetime import datetime
from src.sync_engine import SyncEngine
from src.oracle import OracleConnection
from src.meilisearch_client import MeilisearchClient


@pytest.mark.integration
@pytest.mark.requires_test_db
def test_end_to_end_full_sync_with_test_data_creation():
    """TEST-120 (Part 1): Oracle 테스트 데이터 → Meilisearch Full Sync → 검색 확인
    
    [개발/테스트 환경용]
    이 테스트는 Oracle 테스트 DB에서 실행됩니다 (전체 권한 필요: CREATE, INSERT, DROP).
    
    Complete end-to-end flow:
    1. Create test table in Oracle test DB
    2. Insert test data
    3. Perform full sync to Meilisearch
    4. Verify data was synced correctly
    5. Perform search queries to validate search functionality
    6. Cleanup: Drop test table and delete test index
    
    Environment requirements:
    - Oracle test DB with CREATE/INSERT/DROP privileges
    - Meilisearch instance
    """
    # Arrange: Setup configurations
    oracle_config = {
        "host": os.environ.get("ORACLE_HOST", "localhost"),
        "port": int(os.environ.get("ORACLE_PORT", 1521)),
        "service_name": os.environ.get("ORACLE_SERVICE_NAME", "XEPDB1"),
        "user": os.environ.get("ORACLE_USER", "testuser"),
        "password": os.environ.get("ORACLE_PASSWORD", "testpass")
    }
    
    meilisearch_config = {
        "host": os.environ.get("MEILISEARCH_HOST", "http://localhost:7700"),
        "api_key": os.environ.get("MEILISEARCH_API_KEY", "masterKey")
    }
    
    test_table = "test_users_integration"
    test_index = "test_users_integration"
    
    # Setup: Create test table in Oracle and insert test data
    with OracleConnection(oracle_config) as conn:
        # Drop table if exists
        try:
            conn.execute(f"DROP TABLE {test_table}")
        except:
            pass  # Table doesn't exist, that's fine
        
        # Create test table
        conn.execute(f"""
            CREATE TABLE {test_table} (
                id NUMBER PRIMARY KEY,
                name VARCHAR2(100),
                email VARCHAR2(100),
                status VARCHAR2(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        test_data = [
            (1, "Alice Johnson", "alice@example.com", "active"),
            (2, "Bob Smith", "bob@example.com", "active"),
            (3, "Charlie Brown", "charlie@example.com", "inactive"),
            (4, "Diana Prince", "diana@example.com", "active"),
            (5, "Eve Wilson", "eve@example.com", "active")
        ]
        
        for row in test_data:
            conn.execute(
                f"""INSERT INTO {test_table} (id, name, email, status) 
                   VALUES (:1, :2, :3, :4)""",
                row
            )
    
    # Act: Perform full sync
    sync_engine = SyncEngine(oracle_config, meilisearch_config)
    sync_result = sync_engine.full_sync(test_table, primary_key="id", recreate_index=True)
    
    # Assert: Verify sync was successful
    assert sync_result["success"] is True
    assert sync_result["oracle_count"] == 5
    assert sync_result["meilisearch_count"] == 5
    
    # Act: Perform search queries in Meilisearch
    ms_client = MeilisearchClient(
        meilisearch_config["host"],
        meilisearch_config["api_key"]
    )
    index = ms_client.get_index(test_index)
    
    # Wait for indexing to complete
    import time
    time.sleep(1)
    
    # Search for "Alice"
    search_result_alice = index.search("Alice")
    
    # Search for "active" status
    search_result_active = index.search("active")
    
    # Search for email domain
    search_result_email = index.search("@example.com")
    
    # Assert: Verify search results
    assert search_result_alice["hits"] is not None
    assert len(search_result_alice["hits"]) >= 1
    assert any(hit["name"] == "Alice Johnson" for hit in search_result_alice["hits"])
    
    assert search_result_active["hits"] is not None
    assert len(search_result_active["hits"]) >= 4  # 4 users with active status
    
    assert search_result_email["hits"] is not None
    assert len(search_result_email["hits"]) >= 5  # All users have @example.com
    
    # Cleanup: Drop test table and delete test index
    with OracleConnection(oracle_config) as conn:
        conn.execute(f"DROP TABLE {test_table}")
    
    ms_client.delete_index(test_index)



@pytest.mark.integration
@pytest.mark.requires_read_only_db
def test_end_to_end_full_sync_with_existing_data():
    """TEST-120 (Part 2): Oracle 테스트 데이터 → Meilisearch Full Sync → 검색 확인
    
    [운영 환경용 - 읽기 전용]
    이 테스트는 Oracle 운영 DB에서 실행됩니다 (SELECT 권한만 필요).
    
    Complete end-to-end flow:
    1. Use existing test table in Oracle production DB
    2. Perform full sync to Meilisearch
    3. Verify data was synced correctly
    4. Perform search queries to validate search functionality
    5. Cleanup: Delete test index only (Oracle table is untouched)
    
    Environment requirements:
    - Oracle production DB with SELECT-only privileges
    - Meilisearch instance
    - Pre-existing test table: SYNC_TEST_USERS with test data
    
    Pre-requisites (DBA must create):
    ```sql
    CREATE TABLE SYNC_TEST_USERS (
        id NUMBER PRIMARY KEY,
        name VARCHAR2(100),
        email VARCHAR2(100),
        status VARCHAR2(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    INSERT INTO SYNC_TEST_USERS (id, name, email, status) VALUES
        (1, 'Alice Johnson', 'alice@example.com', 'active'),
        (2, 'Bob Smith', 'bob@example.com', 'active'),
        (3, 'Charlie Brown', 'charlie@example.com', 'inactive'),
        (4, 'Diana Prince', 'diana@example.com', 'active'),
        (5, 'Eve Wilson', 'eve@example.com', 'active');
    COMMIT;
    
    GRANT SELECT ON SYNC_TEST_USERS TO <sync_user>;
    ```
    """
    # Arrange: Setup configurations
    oracle_config = {
        "host": os.environ.get("ORACLE_HOST", "localhost"),
        "port": int(os.environ.get("ORACLE_PORT", 1521)),
        "service_name": os.environ.get("ORACLE_SERVICE_NAME", "XEPDB1"),
        "user": os.environ.get("ORACLE_USER", "sync_readonly"),
        "password": os.environ.get("ORACLE_PASSWORD", "readonly_pass")
    }
    
    meilisearch_config = {
        "host": os.environ.get("MEILISEARCH_HOST", "http://localhost:7700"),
        "api_key": os.environ.get("MEILISEARCH_API_KEY", "masterKey")
    }
    
    # Use existing table (must be pre-created by DBA)
    test_table = os.environ.get("ORACLE_TEST_TABLE", "SYNC_TEST_USERS")
    test_index = "sync_test_users_readonly"
    
    # Verify table exists (read-only check)
    with OracleConnection(oracle_config) as conn:
        try:
            test_query = f"SELECT COUNT(*) FROM {test_table} WHERE ROWNUM = 1"
            conn.fetch_all(test_query)
        except Exception as e:
            pytest.skip(f"Test table {test_table} not found or not accessible. "
                       f"DBA must create it first. Error: {e}")
    
    # Act: Perform full sync
    sync_engine = SyncEngine(oracle_config, meilisearch_config)
    sync_result = sync_engine.full_sync(test_table, primary_key="id", recreate_index=True)
    
    # Assert: Verify sync was successful
    assert sync_result["success"] is True
    assert sync_result["oracle_count"] >= 5  # At least 5 test records
    assert sync_result["meilisearch_count"] == sync_result["oracle_count"]
    
    # Act: Perform search queries in Meilisearch
    ms_client = MeilisearchClient(
        meilisearch_config["host"],
        meilisearch_config["api_key"]
    )
    index = ms_client.get_index(test_index)
    
    # Wait for indexing to complete
    import time
    time.sleep(1)
    
    # Search for "Alice"
    search_result_alice = index.search("Alice")
    
    # Search for "active" status
    search_result_active = index.search("active")
    
    # Search for email domain
    search_result_email = index.search("@example.com")
    
    # Assert: Verify search results
    assert search_result_alice["hits"] is not None
    assert len(search_result_alice["hits"]) >= 1
    assert any(hit["name"] == "Alice Johnson" for hit in search_result_alice["hits"])
    
    assert search_result_active["hits"] is not None
    assert len(search_result_active["hits"]) >= 4  # At least 4 users with active status
    
    assert search_result_email["hits"] is not None
    assert len(search_result_email["hits"]) >= 5  # All users have @example.com
    
    # Cleanup: Delete test index only (DO NOT touch Oracle table - read-only!)
    ms_client.delete_index(test_index)
    
    # NOTE: Oracle table is NOT dropped because we only have SELECT privileges


@pytest.mark.integration
@pytest.mark.requires_test_db
def test_incremental_sync_with_data_changes():
    """TEST-121: Oracle 데이터 변경 → Incremental Sync → 변경 반영 확인
    
    Complete incremental sync flow:
    1. Create test table in Oracle test DB
    2. Insert initial test data
    3. Perform full sync to Meilisearch
    4. Modify some records in Oracle (update)
    5. Insert new records in Oracle
    6. Perform incremental sync
    7. Verify all changes were synced correctly
    8. Cleanup: Drop test table and delete test index
    
    Environment requirements:
    - Oracle test DB with CREATE/INSERT/UPDATE/DROP privileges
    - Meilisearch instance
    """
    # Arrange: Setup configurations
    oracle_config = {
        "host": os.environ.get("ORACLE_HOST", "localhost"),
        "port": int(os.environ.get("ORACLE_PORT", 1521)),
        "service_name": os.environ.get("ORACLE_SERVICE_NAME", "XEPDB1"),
        "user": os.environ.get("ORACLE_USER", "testuser"),
        "password": os.environ.get("ORACLE_PASSWORD", "testpass")
    }
    
    meilisearch_config = {
        "host": os.environ.get("MEILISEARCH_HOST", "http://localhost:7700"),
        "api_key": os.environ.get("MEILISEARCH_API_KEY", "masterKey")
    }
    
    test_table = "test_users_incremental"
    test_index = "test_users_incremental"
    
    # Setup: Create test table in Oracle
    with OracleConnection(oracle_config) as conn:
        # Drop table if exists
        try:
            conn.execute(f"DROP TABLE {test_table}")
        except:
            pass  # Table doesn't exist, that's fine
        
        # Create test table with modified_at column for incremental sync
        conn.execute(f"""
            CREATE TABLE {test_table} (
                id NUMBER PRIMARY KEY,
                name VARCHAR2(100),
                email VARCHAR2(100),
                status VARCHAR2(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert initial test data
        initial_data = [
            (1, "Alice Johnson", "alice@example.com", "active"),
            (2, "Bob Smith", "bob@example.com", "active"),
            (3, "Charlie Brown", "charlie@example.com", "inactive")
        ]
        
        for row in initial_data:
            conn.execute(
                f"""INSERT INTO {test_table} (id, name, email, status) 
                   VALUES (:1, :2, :3, :4)""",
                row
            )
    
    # Act: Perform initial full sync
    sync_engine = SyncEngine(oracle_config, meilisearch_config)
    full_sync_result = sync_engine.full_sync(test_table, primary_key="id", recreate_index=True)
    
    # Assert: Verify initial sync was successful
    assert full_sync_result["success"] is True
    assert full_sync_result["oracle_count"] == 3
    assert full_sync_result["meilisearch_count"] == 3
    
    # Wait for indexing to complete
    import time
    time.sleep(1)
    
    # Act: Modify data in Oracle
    with OracleConnection(oracle_config) as conn:
        # Update existing record (Bob's status changes from active to inactive)
        conn.execute(
            f"""UPDATE {test_table} 
               SET status = :1, modified_at = CURRENT_TIMESTAMP 
               WHERE id = :2""",
            ("inactive", 2)
        )
        
        # Insert new records
        new_data = [
            (4, "Diana Prince", "diana@example.com", "active"),
            (5, "Eve Wilson", "eve@example.com", "active")
        ]
        
        for row in new_data:
            conn.execute(
                f"""INSERT INTO {test_table} (id, name, email, status) 
                   VALUES (:1, :2, :3, :4)""",
                row
            )
    
    # Wait a moment to ensure timestamps are different
    time.sleep(1)
    
    # Act: Perform incremental sync
    incremental_sync_result = sync_engine.incremental_sync(
        test_table, 
        primary_key="id",
        modified_column="modified_at"
    )
    
    # Assert: Verify incremental sync was successful
    assert incremental_sync_result["success"] is True
    assert incremental_sync_result["changed_count"] == 3  # 1 updated + 2 new
    
    # Wait for indexing to complete
    time.sleep(1)
    
    # Act: Verify changes in Meilisearch
    ms_client = MeilisearchClient(
        meilisearch_config["host"],
        meilisearch_config["api_key"]
    )
    index = ms_client.get_index(test_index)
    
    # Get all documents
    all_docs = index.get_documents()
    
    # Assert: Verify all documents are present
    assert len(all_docs["results"]) == 5
    
    # Assert: Verify Bob's status was updated to inactive
    bob_doc = next((doc for doc in all_docs["results"] if doc["id"] == 2), None)
    assert bob_doc is not None
    assert bob_doc["status"] == "inactive"
    
    # Assert: Verify new records were added
    diana_doc = next((doc for doc in all_docs["results"] if doc["id"] == 4), None)
    eve_doc = next((doc for doc in all_docs["results"] if doc["id"] == 5), None)
    assert diana_doc is not None
    assert eve_doc is not None
    assert diana_doc["name"] == "Diana Prince"
    assert eve_doc["name"] == "Eve Wilson"
    
    # Cleanup: Drop test table and delete test index
    with OracleConnection(oracle_config) as conn:
        conn.execute(f"DROP TABLE {test_table}")
    
    ms_client.delete_index(test_index)



@pytest.mark.integration
@pytest.mark.requires_test_db
def test_large_scale_full_sync_performance():
    """TEST-122: 대용량 데이터(10,000건) Full Sync 성능 테스트
    
    Performance test for large-scale data synchronization:
    1. Create test table in Oracle test DB
    2. Insert 10,000 test records
    3. Perform full sync to Meilisearch
    4. Measure sync performance
    5. Verify all data was synced correctly
    6. Cleanup: Drop test table and delete test index
    
    Performance expectations:
    - Should handle 10,000 records successfully
    - Sync should complete without errors
    - All records should be searchable in Meilisearch
    
    Environment requirements:
    - Oracle test DB with CREATE/INSERT/DROP privileges
    - Meilisearch instance
    """
    # Arrange: Setup configurations
    oracle_config = {
        "host": os.environ.get("ORACLE_HOST", "localhost"),
        "port": int(os.environ.get("ORACLE_PORT", 1521)),
        "service_name": os.environ.get("ORACLE_SERVICE_NAME", "XEPDB1"),
        "user": os.environ.get("ORACLE_USER", "testuser"),
        "password": os.environ.get("ORACLE_PASSWORD", "testpass")
    }
    
    meilisearch_config = {
        "host": os.environ.get("MEILISEARCH_HOST", "http://localhost:7700"),
        "api_key": os.environ.get("MEILISEARCH_API_KEY", "masterKey")
    }
    
    test_table = "test_users_large_scale"
    test_index = "test_users_large_scale"
    record_count = 10000
    
    # Setup: Create test table in Oracle
    with OracleConnection(oracle_config) as conn:
        # Drop table if exists
        try:
            conn.execute(f"DROP TABLE {test_table}")
        except:
            pass  # Table doesn't exist, that's fine
        
        # Create test table
        conn.execute(f"""
            CREATE TABLE {test_table} (
                id NUMBER PRIMARY KEY,
                name VARCHAR2(100),
                email VARCHAR2(100),
                status VARCHAR2(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert 10,000 test records in batches for better performance
        batch_size = 1000
        for batch_start in range(0, record_count, batch_size):
            batch_data = []
            for i in range(batch_start, min(batch_start + batch_size, record_count)):
                user_id = i + 1
                name = f"User {user_id}"
                email = f"user{user_id}@example.com"
                status = "active" if user_id % 3 != 0 else "inactive"
                batch_data.append((user_id, name, email, status))
            
            # Insert batch using executemany for better performance
            conn.cursor.executemany(
                f"""INSERT INTO {test_table} (id, name, email, status) 
                   VALUES (:1, :2, :3, :4)""",
                batch_data
            )
    
    # Act: Perform full sync and measure performance
    import time
    sync_engine = SyncEngine(oracle_config, meilisearch_config)
    
    start_time = time.time()
    sync_result = sync_engine.full_sync(test_table, primary_key="id", recreate_index=True)
    end_time = time.time()
    
    sync_duration = end_time - start_time
    
    # Assert: Verify sync was successful
    assert sync_result["success"] is True
    assert sync_result["oracle_count"] == record_count
    assert sync_result["meilisearch_count"] == record_count
    
    # Log performance metrics
    print(f"\n{'='*60}")
    print(f"Performance Metrics:")
    print(f"  Records synced: {record_count}")
    print(f"  Duration: {sync_duration:.2f} seconds")
    print(f"  Throughput: {record_count / sync_duration:.2f} records/second")
    print(f"{'='*60}\n")
    
    # Act: Verify data in Meilisearch
    ms_client = MeilisearchClient(
        meilisearch_config["host"],
        meilisearch_config["api_key"]
    )
    index = ms_client.get_index(test_index)
    
    # Wait for indexing to complete
    time.sleep(2)
    
    # Verify total document count
    stats = index.get_stats()
    assert stats["numberOfDocuments"] == record_count
    
    # Perform sample searches to verify searchability
    search_result_user_100 = index.search("User 100")
    assert len(search_result_user_100["hits"]) >= 1
    assert any(hit["name"] == "User 100" for hit in search_result_user_100["hits"])
    
    search_result_user_5000 = index.search("User 5000")
    assert len(search_result_user_5000["hits"]) >= 1
    assert any(hit["name"] == "User 5000" for hit in search_result_user_5000["hits"])
    
    search_result_active = index.search("active")
    # Approximately 2/3 of users should be active (user_id % 3 != 0)
    assert len(search_result_active["hits"]) > 0
    
    # Cleanup: Drop test table and delete test index
    with OracleConnection(oracle_config) as conn:
        conn.execute(f"DROP TABLE {test_table}")
    
    ms_client.delete_index(test_index)
