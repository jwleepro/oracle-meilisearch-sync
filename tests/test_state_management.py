"""
State Management Tests

TEST-110: 동기화 상태 저장 (시작 시간, 종료 시간, 처리 건수)
TEST-111: 마지막 성공 동기화 정보 조회
TEST-112: 동기화 히스토리 조회
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


def test_save_sync_status():
    """동기화 상태를 저장할 수 있는지 확인 (시작 시간, 종료 시간, 처리 건수)"""
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
    
    # Act: Save sync status
    start_time = datetime(2025, 1, 1, 10, 0, 0)
    end_time = datetime(2025, 1, 1, 10, 5, 0)
    record_count = 1000
    
    sync_engine.save_sync_status(
        table_name='users',
        start_time=start_time,
        end_time=end_time,
        record_count=record_count,
        status='success'
    )
    
    # Assert: Verify sync status was saved
    status = sync_engine.get_sync_status('users')
    
    assert status is not None, "Sync status should be saved"
    assert status['table_name'] == 'users'
    assert status['start_time'] == start_time
    assert status['end_time'] == end_time
    assert status['record_count'] == record_count
    assert status['status'] == 'success'



def test_get_last_successful_sync_info():
    """마지막 성공한 동기화 정보를 조회할 수 있는지 확인"""
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
    
    # Act: Save multiple sync statuses
    sync_engine.save_sync_status(
        table_name='users',
        start_time=datetime(2025, 1, 1, 10, 0, 0),
        end_time=datetime(2025, 1, 1, 10, 5, 0),
        record_count=1000,
        status='success'
    )
    
    sync_engine.save_sync_status(
        table_name='users',
        start_time=datetime(2025, 1, 2, 10, 0, 0),
        end_time=datetime(2025, 1, 2, 10, 3, 0),
        record_count=500,
        status='failed'
    )
    
    sync_engine.save_sync_status(
        table_name='users',
        start_time=datetime(2025, 1, 3, 10, 0, 0),
        end_time=datetime(2025, 1, 3, 10, 4, 0),
        record_count=800,
        status='success'
    )
    
    # Assert: Get last successful sync
    last_success = sync_engine.get_last_successful_sync('users')
    
    assert last_success is not None, "Last successful sync should exist"
    assert last_success['status'] == 'success'
    assert last_success['start_time'] == datetime(2025, 1, 3, 10, 0, 0)
    assert last_success['record_count'] == 800



def test_get_sync_history():
    """동기화 히스토리를 조회할 수 있는지 확인"""
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
    
    # Act: Save multiple sync statuses
    sync_engine.save_sync_status(
        table_name='users',
        start_time=datetime(2025, 1, 1, 10, 0, 0),
        end_time=datetime(2025, 1, 1, 10, 5, 0),
        record_count=1000,
        status='success'
    )
    
    sync_engine.save_sync_status(
        table_name='users',
        start_time=datetime(2025, 1, 2, 10, 0, 0),
        end_time=datetime(2025, 1, 2, 10, 3, 0),
        record_count=500,
        status='failed'
    )
    
    sync_engine.save_sync_status(
        table_name='users',
        start_time=datetime(2025, 1, 3, 10, 0, 0),
        end_time=datetime(2025, 1, 3, 10, 4, 0),
        record_count=800,
        status='success'
    )
    
    # Assert: Get sync history
    history = sync_engine.get_sync_history('users')
    
    assert history is not None, "Sync history should exist"
    assert len(history) == 3, "Should have 3 sync records"
    
    # Verify history is in chronological order
    assert history[0]['start_time'] == datetime(2025, 1, 1, 10, 0, 0)
    assert history[1]['start_time'] == datetime(2025, 1, 2, 10, 0, 0)
    assert history[2]['start_time'] == datetime(2025, 1, 3, 10, 0, 0)
    
    # Verify all statuses are present
    assert history[0]['status'] == 'success'
    assert history[1]['status'] == 'failed'
    assert history[2]['status'] == 'success'
