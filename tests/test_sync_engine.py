"""
Sync Engine Tests

TEST-070: Oracle에서 전체 데이터 추출
TEST-071: 추출된 데이터를 Meilisearch 문서 형식으로 변환
TEST-072: Meilisearch에 배치 단위로 문서 삽입
TEST-073: Full Sync 완료 후 문서 수 일치 확인
TEST-074: Full Sync 전 기존 인덱스 처리 (삭제 후 재생성 옵션)
TEST-080: 마지막 동기화 시점 저장 및 조회
TEST-081: 변경된 레코드만 추출 (수정 시간 기준)
TEST-082: 변경된 레코드 Meilisearch에 upsert
TEST-083: 삭제된 레코드 처리 (soft delete 플래그 기준)
TEST-084: Incremental Sync 후 동기화 시점 업데이트
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


def test_extract_all_data_from_oracle():
    """Oracle에서 전체 데이터를 추출할 수 있는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection:
        mock_conn_instance = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_conn_instance
        
        # Mock fetch_as_dict_with_iso_dates to return sample data
        mock_conn_instance.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 1, 'NAME': 'Alice', 'EMAIL': 'alice@example.com', 'CREATED_AT': '2024-01-01T10:00:00'},
            {'ID': 2, 'NAME': 'Bob', 'EMAIL': 'bob@example.com', 'CREATED_AT': '2024-01-02T10:00:00'},
            {'ID': 3, 'NAME': 'Charlie', 'EMAIL': 'charlie@example.com', 'CREATED_AT': '2024-01-03T10:00:00'}
        ]
        
        # Create sync engine
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        
        # Extract all data from Oracle
        table_name = "users"
        results = sync_engine.extract_from_oracle(table_name)
        
        # Assert: 전체 데이터가 딕셔너리 리스트로 추출되는지 확인
        assert isinstance(results, list)
        assert len(results) == 3
        assert results[0]['ID'] == 1
        assert results[0]['NAME'] == 'Alice'
        assert results[1]['ID'] == 2
        assert results[2]['ID'] == 3
        
        # Verify the query was executed correctly
        mock_conn_instance.fetch_as_dict_with_iso_dates.assert_called_once_with("SELECT * FROM users")



def test_transform_data_to_meilisearch_format():
    """추출된 데이터를 Meilisearch 문서 형식으로 변환할 수 있는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Oracle에서 추출한 데이터 형식
    oracle_data = [
        {'ID': 1, 'NAME': 'Alice', 'EMAIL': 'alice@example.com', 'CREATED_AT': '2024-01-01T10:00:00'},
        {'ID': 2, 'NAME': 'Bob', 'EMAIL': 'bob@example.com', 'CREATED_AT': '2024-01-02T10:00:00'},
        {'ID': 3, 'NAME': 'Charlie', 'EMAIL': 'charlie@example.com', 'CREATED_AT': '2024-01-03T10:00:00'}
    ]
    
    # Act
    sync_engine = SyncEngine(oracle_config, meilisearch_config)
    documents = sync_engine.transform_to_documents(oracle_data, primary_key='ID')
    
    # Assert: Meilisearch 문서 형식으로 변환되는지 확인
    assert isinstance(documents, list)
    assert len(documents) == 3
    
    # 각 문서가 올바른 형식인지 확인
    for doc in documents:
        assert isinstance(doc, dict)
        assert 'ID' in doc
        assert 'NAME' in doc
        assert 'EMAIL' in doc
        assert 'CREATED_AT' in doc
    
    # 데이터가 그대로 유지되는지 확인
    assert documents[0]['ID'] == 1
    assert documents[0]['NAME'] == 'Alice'
    assert documents[1]['ID'] == 2
    assert documents[2]['ID'] == 3



def test_insert_documents_in_batches_to_meilisearch():
    """Meilisearch에 배치 단위로 문서를 삽입할 수 있는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    documents = [
        {'ID': 1, 'NAME': 'Alice', 'EMAIL': 'alice@example.com'},
        {'ID': 2, 'NAME': 'Bob', 'EMAIL': 'bob@example.com'},
        {'ID': 3, 'NAME': 'Charlie', 'EMAIL': 'charlie@example.com'}
    ]
    
    # Act
    with patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient:
        mock_client_instance = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client_instance
        mock_client_instance.get_index.return_value = mock_index
        
        # Mock add_documents to return task info
        mock_index.add_documents.return_value = {'taskUid': 123}
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        task_info = sync_engine.insert_documents_batch('users', documents)
        
        # Assert: add_documents가 호출되고 task info가 반환되는지 확인
        mock_client_instance.get_index.assert_called_once_with('users')
        mock_index.add_documents.assert_called_once_with(documents)
        assert task_info == {'taskUid': 123}



def test_full_sync_verifies_document_count():
    """Full Sync 완료 후 문서 수가 일치하는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection, \
         patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient:
        
        # Mock Oracle data extraction
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        mock_oracle_conn.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 1, 'NAME': 'Alice'},
            {'ID': 2, 'NAME': 'Bob'},
            {'ID': 3, 'NAME': 'Charlie'}
        ]
        
        # Mock Meilisearch client
        mock_client = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        mock_client.get_index.return_value = mock_index
        mock_index.add_documents.return_value = {'taskUid': 123}
        
        # Mock index stats to verify document count
        mock_index.get_stats.return_value = {'numberOfDocuments': 3}
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        result = sync_engine.full_sync('users', primary_key='ID')
        
        # Assert: Full Sync가 성공하고 문서 수가 일치하는지 확인
        assert result['success'] is True
        assert result['oracle_count'] == 3
        assert result['meilisearch_count'] == 3
        assert result['oracle_count'] == result['meilisearch_count']



def test_full_sync_with_recreate_index_option():
    """Full Sync 전 기존 인덱스를 삭제 후 재생성하는 옵션을 테스트"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection, \
         patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient:
        
        # Mock Oracle data extraction
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        mock_oracle_conn.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 1, 'NAME': 'Alice'},
            {'ID': 2, 'NAME': 'Bob'}
        ]
        
        # Mock Meilisearch client
        mock_client = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        mock_client.get_index.return_value = mock_index
        mock_index.add_documents.return_value = {'taskUid': 123}
        mock_index.get_stats.return_value = {'numberOfDocuments': 2}
        
        # Mock index existence and deletion
        mock_client.index_exists.return_value = True
        mock_client.delete_index.return_value = {'taskUid': 456}
        mock_client.create_index.return_value = {'taskUid': 789}
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        result = sync_engine.full_sync('users', primary_key='ID', recreate_index=True)
        
        # Assert: 기존 인덱스가 삭제되고 재생성되었는지 확인
        mock_client.index_exists.assert_called_once_with('users')
        mock_client.delete_index.assert_called_once_with('users')
        mock_client.create_index.assert_called_once_with('users', 'ID')
        assert result['success'] is True


def test_save_and_retrieve_last_sync_timestamp():
    """마지막 동기화 시점을 저장하고 조회할 수 있는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    sync_engine = SyncEngine(oracle_config, meilisearch_config)
    
    # Act: 동기화 시점 저장
    test_timestamp = datetime(2024, 1, 15, 10, 30, 45)
    sync_engine.save_last_sync_timestamp('users', test_timestamp)
    
    # Act: 동기화 시점 조회
    retrieved_timestamp = sync_engine.get_last_sync_timestamp('users')
    
    # Assert: 저장된 시점과 조회된 시점이 일치하는지 확인
    assert retrieved_timestamp is not None
    assert retrieved_timestamp == test_timestamp


def test_extract_only_changed_records_by_modified_time():
    """마지막 동기화 시점 이후 변경된 레코드만 추출할 수 있는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection:
        mock_conn_instance = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_conn_instance
        
        # Mock fetch_as_dict_with_iso_dates to return only changed records
        mock_conn_instance.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 2, 'NAME': 'Bob Updated', 'EMAIL': 'bob@example.com', 'MODIFIED_AT': '2024-01-16T10:00:00'},
            {'ID': 4, 'NAME': 'Diana', 'EMAIL': 'diana@example.com', 'MODIFIED_AT': '2024-01-16T11:00:00'}
        ]
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        
        # 마지막 동기화 시점 설정
        last_sync = datetime(2024, 1, 15, 10, 0, 0)
        
        # Extract only changed records since last sync
        table_name = "users"
        modified_column = "MODIFIED_AT"
        results = sync_engine.extract_changed_records(table_name, modified_column, last_sync)
        
        # Assert: 변경된 레코드만 추출되는지 확인
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]['ID'] == 2
        assert results[0]['NAME'] == 'Bob Updated'
        assert results[1]['ID'] == 4
        assert results[1]['NAME'] == 'Diana'
        
        # Verify the query was executed with WHERE clause for incremental sync
        call_args = mock_conn_instance.fetch_as_dict_with_iso_dates.call_args[0][0]
        assert "WHERE" in call_args
        assert modified_column in call_args


def test_upsert_changed_records_to_meilisearch():
    """변경된 레코드를 Meilisearch에 upsert할 수 있는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    changed_records = [
        {'ID': 2, 'NAME': 'Bob Updated', 'EMAIL': 'bob_updated@example.com'},
        {'ID': 4, 'NAME': 'Diana', 'EMAIL': 'diana@example.com'}
    ]
    
    # Act
    with patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient:
        mock_client_instance = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client_instance
        mock_client_instance.get_index.return_value = mock_index
        
        # Mock update_documents (upsert) to return task info
        mock_index.update_documents.return_value = {'taskUid': 456}
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        task_info = sync_engine.upsert_documents('users', changed_records)
        
        # Assert: update_documents가 호출되고 task info가 반환되는지 확인
        mock_client_instance.get_index.assert_called_once_with('users')
        mock_index.update_documents.assert_called_once_with(changed_records)
        assert task_info == {'taskUid': 456}


def test_handle_deleted_records_by_soft_delete_flag():
    """soft delete 플래그 기준으로 삭제된 레코드를 처리할 수 있는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection:
        mock_conn_instance = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_conn_instance
        
        # Mock fetch_as_dict_with_iso_dates to return deleted records (IS_DELETED = 1 or 'Y')
        mock_conn_instance.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 3, 'NAME': 'Charlie', 'EMAIL': 'charlie@example.com', 'IS_DELETED': 1},
            {'ID': 5, 'NAME': 'Eve', 'EMAIL': 'eve@example.com', 'IS_DELETED': 1}
        ]
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        
        # 마지막 동기화 시점 설정
        last_sync = datetime(2024, 1, 15, 10, 0, 0)
        
        # Extract deleted records since last sync
        table_name = "users"
        modified_column = "MODIFIED_AT"
        delete_flag_column = "IS_DELETED"
        results = sync_engine.extract_deleted_records(table_name, modified_column, delete_flag_column, last_sync)
        
        # Assert: 삭제된 레코드만 추출되는지 확인
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]['ID'] == 3
        assert results[0]['IS_DELETED'] == 1
        assert results[1]['ID'] == 5
        
        # Verify the query was executed with WHERE clause for deleted records
        call_args = mock_conn_instance.fetch_as_dict_with_iso_dates.call_args[0][0]
        assert "WHERE" in call_args
        assert delete_flag_column in call_args
        assert modified_column in call_args


def test_incremental_sync_updates_timestamp():
    """Incremental Sync 후 동기화 시점이 업데이트되는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    import time
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection, \
         patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient:
        
        # Mock Oracle data extraction
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        mock_oracle_conn.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 2, 'NAME': 'Bob Updated', 'EMAIL': 'bob_updated@example.com'},
            {'ID': 4, 'NAME': 'Diana', 'EMAIL': 'diana@example.com'}
        ]
        
        # Mock Meilisearch client
        mock_client = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        mock_client.get_index.return_value = mock_index
        mock_index.update_documents.return_value = {'taskUid': 123}
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        
        # Set initial timestamp
        last_sync = datetime(2024, 1, 15, 10, 0, 0)
        sync_engine.save_last_sync_timestamp('users', last_sync)
        
        # Wait a tiny bit to ensure time difference
        time.sleep(0.01)
        
        # Perform incremental sync
        result = sync_engine.incremental_sync('users', 'ID', 'MODIFIED_AT')
        
        # Assert: 동기화가 성공하고 시점이 업데이트되었는지 확인
        assert result['success'] is True
        updated_timestamp = sync_engine.get_last_sync_timestamp('users')
        assert updated_timestamp is not None
        assert updated_timestamp > last_sync


def test_sync_retry_on_failure_up_to_3_times():
    """동기화 실패 시 최대 3회 재시도하는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection, \
         patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient:
        
        # Mock Oracle data extraction
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        mock_oracle_conn.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 1, 'NAME': 'Alice'},
            {'ID': 2, 'NAME': 'Bob'}
        ]
        
        # Mock Meilisearch client to fail
        mock_client = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        mock_client.get_index.return_value = mock_index
        
        # Make add_documents fail every time to trigger retries
        mock_index.add_documents.side_effect = Exception("Connection error")
        mock_index.get_stats.return_value = {'numberOfDocuments': 0}
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        result = sync_engine.full_sync_with_retry('users', primary_key='ID')
        
        # Assert: 실패 후 재시도가 3회 발생했는지 확인
        assert result['success'] is False
        assert result['retry_count'] == 3
        assert mock_index.add_documents.call_count == 3  # Initial + 3 retries = 4 attempts total, or just 3 retries


def test_retry_with_exponential_backoff():
    """재시도 간 지수 백오프(exponential backoff)가 적용되는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    import time
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection, \
         patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient, \
         patch('time.sleep') as mock_sleep:
        
        # Mock Oracle data extraction
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        mock_oracle_conn.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 1, 'NAME': 'Alice'},
            {'ID': 2, 'NAME': 'Bob'}
        ]
        
        # Mock Meilisearch client to fail
        mock_client = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        mock_client.get_index.return_value = mock_index
        
        # Make add_documents fail every time to trigger retries
        mock_index.add_documents.side_effect = Exception("Connection error")
        mock_index.get_stats.return_value = {'numberOfDocuments': 0}
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        result = sync_engine.full_sync_with_retry('users', primary_key='ID')
        
        # Assert: 지수 백오프가 적용되었는지 확인
        # With 3 max_retries: Attempt 1 fails -> sleep 1s -> Attempt 2 fails -> sleep 2s -> Attempt 3 fails -> stop
        # Total: 3 attempts, 2 sleep calls
        assert result['success'] is False
        assert result['retry_count'] == 3
        assert mock_sleep.call_count == 2  # 2 sleeps between 3 attempts
        
        # Verify exponential backoff delays
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls[0] == 1  # 2^0 = 1 second after 1st failure
        assert sleep_calls[1] == 2  # 2^1 = 2 seconds after 2nd failure


def test_log_error_info_on_final_failure():
    """최종 실패 시 에러 정보를 기록하는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection, \
         patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient, \
         patch('time.sleep') as mock_sleep:
        
        # Mock Oracle data extraction
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        mock_oracle_conn.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 1, 'NAME': 'Alice'},
            {'ID': 2, 'NAME': 'Bob'}
        ]
        
        # Mock Meilisearch client to fail with specific error
        mock_client = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        mock_client.get_index.return_value = mock_index
        
        # Make add_documents fail with specific error message
        error_message = "Connection timeout to Meilisearch server"
        mock_index.add_documents.side_effect = Exception(error_message)
        mock_index.get_stats.return_value = {'numberOfDocuments': 0}
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        result = sync_engine.full_sync_with_retry('users', primary_key='ID')
        
        # Assert: 최종 실패 시 에러 정보가 기록되었는지 확인
        assert result['success'] is False
        assert result['retry_count'] == 3
        assert 'error' in result
        assert error_message in result['error']
        assert 'index_name' in result
        assert result['index_name'] == 'users'
        assert 'timestamp' in result


def test_log_failed_batch_info_on_partial_failure():
    """부분 실패 시 실패한 배치 정보를 기록하는지 확인"""
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection, \
         patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient:
        
        # Mock Oracle data extraction - 6 records (will be split into 2 batches of 3)
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        mock_oracle_conn.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 1, 'NAME': 'Alice'},
            {'ID': 2, 'NAME': 'Bob'},
            {'ID': 3, 'NAME': 'Charlie'},
            {'ID': 4, 'NAME': 'Diana'},
            {'ID': 5, 'NAME': 'Eve'},
            {'ID': 6, 'NAME': 'Frank'}
        ]
        
        # Mock Meilisearch client
        mock_client = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        mock_client.get_index.return_value = mock_index
        
        # First batch succeeds, second batch fails
        call_count = [0]
        def add_documents_side_effect(docs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {'taskUid': 123}  # First batch succeeds
            else:
                raise Exception(f"Batch {call_count[0]} failed: Network error")  # Second batch fails
        
        mock_index.add_documents.side_effect = add_documents_side_effect
        mock_index.get_stats.return_value = {'numberOfDocuments': 3}  # Only first batch succeeded
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        result = sync_engine.full_sync_batch('users', primary_key='ID', batch_size=3)
        
        # Assert: 부분 실패 시 실패한 배치 정보가 기록되는지 확인
        assert result['success'] is False
        assert result['total_records'] == 6
        assert result['successful_records'] == 3
        assert result['failed_batches'] == 1
        assert 'failed_batch_info' in result
        assert len(result['failed_batch_info']) == 1
        
        # Check failed batch information
        failed_batch = result['failed_batch_info'][0]
        assert 'batch_number' in failed_batch
        assert failed_batch['batch_number'] == 2
        assert 'error' in failed_batch
        assert 'Network error' in failed_batch['error']
        assert 'record_count' in failed_batch
        assert failed_batch['record_count'] == 3


def test_full_sync_batch_with_recreate_index():
    """TEST-093 (Additional): full_sync_batch()에서 recreate_index=True가 정상 작동하는지 확인
    
    This test verifies that the recreate_index parameter works correctly
    in the full_sync_batch method, ensuring index deletion and recreation
    happens before batch processing.
    """
    # Arrange
    from src.sync_engine import SyncEngine
    
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    # Act
    with patch('src.sync_engine.OracleConnection') as MockOracleConnection, \
         patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient:
        
        # Mock Oracle data extraction
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        mock_oracle_conn.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 1, 'NAME': 'Alice'},
            {'ID': 2, 'NAME': 'Bob'},
            {'ID': 3, 'NAME': 'Charlie'}
        ]
        
        # Mock Meilisearch client
        mock_client = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        mock_client.get_index.return_value = mock_index
        mock_client.index_exists.return_value = True
        mock_client.delete_index.return_value = {'taskUid': 456}
        mock_client.create_index.return_value = {'taskUid': 789}
        mock_index.add_documents.return_value = {'taskUid': 123}
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        
        # Act: Call full_sync_batch with recreate_index=True
        result = sync_engine.full_sync_batch('users', primary_key='ID', batch_size=3, recreate_index=True)
        
        # Assert: Verify that index was recreated before batch processing
        mock_client.index_exists.assert_called_once_with('users')
        mock_client.delete_index.assert_called_once_with('users')
        mock_client.create_index.assert_called_once_with('users', 'ID')
        
        # Assert: Verify sync result
        assert result['success'] is True
        assert result['total_records'] == 3
        assert result['successful_records'] == 3
        assert result['failed_batches'] == 0


def test_save_and_load_sync_state_to_file():
    """TEST-140: sync_state.json 파일로 시점 저장/로드"""
    import os
    import json
    from src.sync_engine import SyncEngine
    
    # Arrange
    oracle_config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    meilisearch_config = {
        "host": "http://localhost:7700",
        "api_key": "test_api_key"
    }
    
    sync_engine = SyncEngine(oracle_config, meilisearch_config)
    
    # Clean up any existing sync_state.json file
    state_file = 'sync_state.json'
    if os.path.exists(state_file):
        os.remove(state_file)
    
    # Act: Save sync timestamp to file
    test_timestamp = datetime(2024, 1, 15, 10, 30, 0)
    sync_engine.save_last_sync_timestamp('users', test_timestamp)
    sync_engine.persist_sync_state()  # Save to file
    
    # Assert: Verify file was created
    assert os.path.exists(state_file)
    
    # Act: Create new sync engine and load from file
    sync_engine2 = SyncEngine(oracle_config, meilisearch_config)
    sync_engine2.load_sync_state()  # Load from file
    
    # Assert: Verify loaded timestamp matches saved timestamp
    loaded_timestamp = sync_engine2.get_last_sync_timestamp('users')
    assert loaded_timestamp == test_timestamp
    
    # Verify file contents
    with open(state_file, 'r') as f:
        state_data = json.load(f)
    
    assert 'users' in state_data
    assert state_data['users'] == test_timestamp.isoformat()
    
    # Clean up
    if os.path.exists(state_file):
        os.remove(state_file)
