"""
Logging Tests

TEST-100: 동기화 시작/완료 로그 기록
TEST-101: 동기화 진행률 로그 (처리된 레코드 수)
TEST-102: 에러 발생 시 상세 로그 기록
TEST-103: 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import logging


def test_log_sync_start_and_completion():
    """동기화 시작 및 완료 로그가 기록되는지 확인"""
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
         patch('src.sync_engine.logger') as mock_logger:
        
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
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        result = sync_engine.full_sync('users', primary_key='ID')
        
        # Assert: 시작 및 완료 로그가 기록되었는지 확인
        assert result['success'] is True
        
        # Check that info logs were called for start and completion
        info_calls = mock_logger.info.call_args_list
        assert len(info_calls) >= 2
        
        # Verify start log
        start_log_found = False
        for call_item in info_calls:
            if 'Starting full sync' in str(call_item) or 'started' in str(call_item).lower():
                start_log_found = True
                break
        assert start_log_found, "Start log not found"
        
        # Verify completion log
        completion_log_found = False
        for call_item in info_calls:
            if 'completed' in str(call_item).lower() or 'finished' in str(call_item).lower():
                completion_log_found = True
                break
        assert completion_log_found, "Completion log not found"



def test_log_sync_progress_with_record_count():
    """동기화 진행률 로그가 처리된 레코드 수를 포함하는지 확인"""
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
         patch('src.sync_engine.logger') as mock_logger:
        
        # Mock Oracle data extraction - 150건의 데이터
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        
        # 150건의 데이터 반환
        test_data = [{'ID': i, 'NAME': f'User{i}'} for i in range(1, 151)]
        
        mock_oracle_conn.fetch_as_dict_with_iso_dates.return_value = test_data
        
        # Mock Meilisearch client
        mock_client = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        mock_client.get_index.return_value = mock_index
        mock_index.add_documents.return_value = {'taskUid': 123}
        mock_index.get_stats.return_value = {'numberOfDocuments': 150}
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        result = sync_engine.full_sync('users', primary_key='ID')
        
        # Assert: 진행률 로그가 처리된 레코드 수를 포함하는지 확인
        assert result['success'] is True
        
        # Check that info logs were called with progress information
        info_calls = mock_logger.info.call_args_list
        
        # Verify progress logs contain record counts
        progress_log_found = False
        for call_item in info_calls:
            call_str = str(call_item)
            # 진행률 로그는 "processed" 또는 "Processing batch"와 레코드 수를 포함해야 함
            if ('processing' in call_str.lower() or 'processed' in call_str.lower()) and \
               ('150' in call_str or '150 records' in call_str.lower()):
                progress_log_found = True
                break
        
        assert progress_log_found, f"Progress log with record count not found. Info calls: {info_calls}"



def test_log_error_with_detailed_info_on_sync_failure():
    """동기화 실패 시 상세한 에러 정보가 로그에 기록되는지 확인"""
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
         patch('src.sync_engine.logger') as mock_logger:
        
        # Mock Oracle connection to raise an exception
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        
        # Simulate a database error
        test_error = Exception("ORA-12345: Database connection lost")
        mock_oracle_conn.fetch_as_dict_with_iso_dates.side_effect = test_error
        
        # Mock Meilisearch client
        mock_client = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        
        sync_engine = SyncEngine(oracle_config, meilisearch_config)
        
        # Act: Expect the sync to fail
        try:
            result = sync_engine.full_sync('users', primary_key='ID')
            # If no exception is raised, the test should fail
            assert False, "Expected an exception but none was raised"
        except Exception as e:
            # Exception is expected
            pass
        
        # Assert: 에러 로그가 상세 정보와 함께 기록되었는지 확인
        error_calls = mock_logger.error.call_args_list
        
        # Verify that error was logged
        assert len(error_calls) > 0, "No error logs found"
        
        # Verify error log contains detailed information
        error_log_found = False
        for call_item in error_calls:
            call_str = str(call_item)
            # 에러 로그는 에러 메시지와 관련 정보를 포함해야 함
            if 'ORA-12345' in call_str or 'Database connection lost' in call_str:
                error_log_found = True
                break
        
        assert error_log_found, f"Detailed error log not found. Error calls: {error_calls}"



def test_configure_log_level():
    """로그 레벨을 설정할 수 있는지 확인 (DEBUG, INFO, WARNING, ERROR)"""
    # Arrange
    import logging
    from src.sync_engine import logger
    
    # Test each log level
    log_levels = [
        (logging.DEBUG, 'DEBUG'),
        (logging.INFO, 'INFO'),
        (logging.WARNING, 'WARNING'),
        (logging.ERROR, 'ERROR')
    ]
    
    for level, level_name in log_levels:
        # Act: Set log level
        logger.setLevel(level)
        
        # Assert: Verify log level is set correctly
        assert logger.level == level, f"Expected log level {level_name} ({level}), but got {logger.level}"
    
    # Verify that logger supports all standard logging methods
    assert hasattr(logger, 'debug'), "Logger should have debug method"
    assert hasattr(logger, 'info'), "Logger should have info method"
    assert hasattr(logger, 'warning'), "Logger should have warning method"
    assert hasattr(logger, 'error'), "Logger should have error method"
