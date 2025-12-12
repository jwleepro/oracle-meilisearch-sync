"""
TEST-020: Oracle DB 연결 객체 생성
TEST-021: Oracle DB 연결 성공 시 연결 객체 반환
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


def test_create_oracle_connection():
    """Oracle DB 연결 객체를 생성할 수 있는지 확인"""
    # Arrange
    from src.oracle import OracleConnection

    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }

    # Act & Assert: OracleConnection 객체가 생성되는지 확인
    with patch('oracledb.connect') as mock_connect:
        mock_connect.return_value = Mock()

        conn = OracleConnection(config)

        assert conn is not None
        assert isinstance(conn, OracleConnection)


def test_connect_returns_connection_object():
    """Oracle DB 연결 성공 시 연결 객체를 반환하는지 확인"""
    # Arrange
    from src.oracle import OracleConnection

    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }

    # Act
    with patch('oracledb.connect') as mock_connect:
        mock_db_connection = MagicMock()
        mock_connect.return_value = mock_db_connection

        conn = OracleConnection(config)
        result = conn.connect()

        # Assert: connect 메서드가 호출되었고 연결 객체가 반환되는지 확인
        mock_connect.assert_called_once_with(
            host=config["host"],
            port=config["port"],
            service_name=config["service_name"],
            user=config["user"],
            password=config["password"]
        )
        assert result == mock_db_connection


def test_connect_raises_exception_on_failure():
    """Oracle DB 연결 실패 시 적절한 예외를 발생시키는지 확인"""
    # Arrange
    from src.oracle import OracleConnection
    import oracledb

    config = {
        "host": "invalid-host",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }

    # Act & Assert: 연결 실패 시 DatabaseError가 발생하는지 확인
    with patch('oracledb.connect') as mock_connect:
        mock_connect.side_effect = oracledb.DatabaseError("Connection failed")

        conn = OracleConnection(config)
        
        with pytest.raises(oracledb.DatabaseError):
            conn.connect()



def test_create_connection_pool():
    """연결 풀을 생성하고 관리할 수 있는지 확인"""
    # Arrange
    from src.oracle import OracleConnectionPool
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass",
        "min_pool_size": 1,
        "max_pool_size": 5
    }
    
    # Act
    with patch('oracledb.create_pool') as mock_create_pool:
        mock_pool = MagicMock()
        mock_create_pool.return_value = mock_pool
        
        pool = OracleConnectionPool(config)
        result = pool.create_pool()
        
        # Assert: 연결 풀이 생성되고 반환되는지 확인
        mock_create_pool.assert_called_once_with(
            host=config["host"],
            port=config["port"],
            service_name=config["service_name"],
            user=config["user"],
            password=config["password"],
            min=config["min_pool_size"],
            max=config["max_pool_size"]
        )
        assert result == mock_pool
        assert pool.pool == mock_pool


def test_acquire_connection_from_pool():
    """연결 풀에서 연결을 가져올 수 있는지 확인"""
    # Arrange
    from src.oracle import OracleConnectionPool
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass",
        "min_pool_size": 1,
        "max_pool_size": 5
    }
    
    # Act
    with patch('oracledb.create_pool') as mock_create_pool:
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_pool.acquire.return_value = mock_connection
        mock_create_pool.return_value = mock_pool
        
        pool = OracleConnectionPool(config)
        pool.create_pool()
        conn = pool.acquire()
        
        # Assert: 연결을 가져올 수 있는지 확인
        mock_pool.acquire.assert_called_once()
        assert conn == mock_connection


def test_close_connection_pool():
    """연결 풀을 닫을 수 있는지 확인"""
    # Arrange
    from src.oracle import OracleConnectionPool
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass",
        "min_pool_size": 1,
        "max_pool_size": 5
    }
    
    # Act
    with patch('oracledb.create_pool') as mock_create_pool:
        mock_pool = MagicMock()
        mock_create_pool.return_value = mock_pool
        
        pool = OracleConnectionPool(config)
        pool.create_pool()
        pool.close()
        
        # Assert: 연결 풀이 닫히는지 확인
        mock_pool.close.assert_called_once()



def test_connection_context_manager():
    """컨텍스트 매니저를 사용하여 연결을 자동으로 해제하는지 확인"""
    # Arrange
    from src.oracle import OracleConnection
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    # Act & Assert
    with patch('oracledb.connect') as mock_connect:
        mock_db_connection = MagicMock()
        mock_connect.return_value = mock_db_connection
        
        # 컨텍스트 매니저로 사용
        with OracleConnection(config) as conn:
            # 연결이 자동으로 설정되는지 확인
            assert conn == mock_db_connection
        
        # 컨텍스트를 벗어나면 close()가 호출되는지 확인
        mock_db_connection.close.assert_called_once()


def test_connection_pool_context_manager():
    """컨텍스트 매니저를 사용하여 연결 풀에서 가져온 연결을 자동으로 해제하는지 확인"""
    # Arrange
    from src.oracle import OracleConnectionPool
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass",
        "min_pool_size": 1,
        "max_pool_size": 5
    }
    
    # Act & Assert
    with patch('oracledb.create_pool') as mock_create_pool:
        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_pool.acquire.return_value = mock_connection
        mock_create_pool.return_value = mock_pool
        
        pool = OracleConnectionPool(config)
        pool.create_pool()
        
        # 컨텍스트 매니저로 연결 획득
        with pool as conn:
            assert conn == mock_connection
        
        # 컨텍스트를 벗어나면 연결이 반환되는지 확인
        mock_connection.close.assert_called_once()



def test_fetch_all_records_from_table():
    """단일 테이블에서 전체 레코드를 조회할 수 있는지 확인"""
    # Arrange
    from src.oracle import OracleConnection
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    # Act
    with patch('oracledb.connect') as mock_connect:
        mock_db_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_db_connection.cursor.return_value = mock_cursor
        
        # Mock fetchall to return sample data
        mock_cursor.fetchall.return_value = [
            (1, 'Alice', 'alice@example.com'),
            (2, 'Bob', 'bob@example.com'),
            (3, 'Charlie', 'charlie@example.com')
        ]
        
        mock_connect.return_value = mock_db_connection
        
        conn = OracleConnection(config)
        conn.connect()
        
        # 테이블에서 전체 레코드 조회
        results = conn.fetch_all("SELECT * FROM users")
        
        # Assert: SQL이 실행되고 결과가 반환되는지 확인
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users")
        mock_cursor.fetchall.assert_called_once()
        assert len(results) == 3
        assert results[0] == (1, 'Alice', 'alice@example.com')
        assert results[1] == (2, 'Bob', 'bob@example.com')
        assert results[2] == (3, 'Charlie', 'charlie@example.com')



def test_convert_results_to_dict_list():
    """조회 결과를 딕셔너리 리스트로 변환할 수 있는지 확인"""
    # Arrange
    from src.oracle import OracleConnection
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    # Act
    with patch('oracledb.connect') as mock_connect:
        mock_db_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_db_connection.cursor.return_value = mock_cursor
        
        # Mock column descriptions
        mock_cursor.description = [
            ('ID', None, None, None, None, None, None),
            ('NAME', None, None, None, None, None, None),
            ('EMAIL', None, None, None, None, None, None)
        ]
        
        # Mock fetchall to return sample data
        mock_cursor.fetchall.return_value = [
            (1, 'Alice', 'alice@example.com'),
            (2, 'Bob', 'bob@example.com'),
            (3, 'Charlie', 'charlie@example.com')
        ]
        
        mock_connect.return_value = mock_db_connection
        
        conn = OracleConnection(config)
        conn.connect()
        
        # 테이블에서 전체 레코드를 딕셔너리 리스트로 조회
        results = conn.fetch_as_dict("SELECT * FROM users")
        
        # Assert: 결과가 딕셔너리 리스트로 반환되는지 확인
        assert len(results) == 3
        assert results[0] == {'ID': 1, 'NAME': 'Alice', 'EMAIL': 'alice@example.com'}
        assert results[1] == {'ID': 2, 'NAME': 'Bob', 'EMAIL': 'bob@example.com'}
        assert results[2] == {'ID': 3, 'NAME': 'Charlie', 'EMAIL': 'charlie@example.com'}



def test_fetch_in_batches():
    """배치 단위로 데이터를 조회할 수 있는지 확인 (cursor.fetchmany)"""
    # Arrange
    from src.oracle import OracleConnection
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    # Act
    with patch('oracledb.connect') as mock_connect:
        mock_db_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_db_connection.cursor.return_value = mock_cursor
        
        # Mock fetchmany to return batches
        mock_cursor.fetchmany.side_effect = [
            [(1, 'Alice'), (2, 'Bob')],  # First batch
            [(3, 'Charlie'), (4, 'David')],  # Second batch
            []  # No more data
        ]
        
        mock_connect.return_value = mock_db_connection
        
        conn = OracleConnection(config)
        conn.connect()
        
        # 배치 단위로 데이터 조회
        batches = list(conn.fetch_batches("SELECT * FROM users", batch_size=2))
        
        # Assert: 배치가 올바르게 반환되는지 확인
        assert len(batches) == 2
        assert batches[0] == [(1, 'Alice'), (2, 'Bob')]
        assert batches[1] == [(3, 'Charlie'), (4, 'David')]
        
        # fetchmany가 batch_size로 호출되었는지 확인
        assert mock_cursor.fetchmany.call_count == 3
        mock_cursor.fetchmany.assert_called_with(2)



def test_fetch_incremental_by_modified_time():
    """마지막 수정 시간 기준으로 변경된 레코드만 조회하는지 확인"""
    # Arrange
    from src.oracle import OracleConnection
    from datetime import datetime
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    # Act
    with patch('oracledb.connect') as mock_connect:
        mock_db_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_db_connection.cursor.return_value = mock_cursor
        
        # Mock fetchall to return modified records
        mock_cursor.fetchall.return_value = [
            (2, 'Bob', datetime(2024, 1, 2, 10, 0, 0)),
            (3, 'Charlie', datetime(2024, 1, 3, 10, 0, 0))
        ]
        
        mock_connect.return_value = mock_db_connection
        
        conn = OracleConnection(config)
        conn.connect()
        
        # 마지막 동기화 시간 이후 변경된 레코드만 조회
        last_sync_time = datetime(2024, 1, 1, 0, 0, 0)
        results = conn.fetch_incremental(
            "SELECT * FROM users WHERE modified_at > :last_sync",
            last_sync_time=last_sync_time
        )
        
        # Assert: 파라미터가 올바르게 바인딩되고 실행되는지 확인
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert call_args[0][0] == "SELECT * FROM users WHERE modified_at > :last_sync"
        assert 'last_sync' in call_args[1]
        assert call_args[1]['last_sync'] == last_sync_time
        
        assert len(results) == 2



def test_handle_null_values():
    """NULL 값을 올바르게 처리하는지 확인"""
    # Arrange
    from src.oracle import OracleConnection
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    # Act
    with patch('oracledb.connect') as mock_connect:
        mock_db_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_db_connection.cursor.return_value = mock_cursor
        
        # Mock column descriptions
        mock_cursor.description = [
            ('ID', None, None, None, None, None, None),
            ('NAME', None, None, None, None, None, None),
            ('EMAIL', None, None, None, None, None, None)
        ]
        
        # Mock fetchall with NULL values
        mock_cursor.fetchall.return_value = [
            (1, 'Alice', 'alice@example.com'),
            (2, None, 'bob@example.com'),  # NULL name
            (3, 'Charlie', None)  # NULL email
        ]
        
        mock_connect.return_value = mock_db_connection
        
        conn = OracleConnection(config)
        conn.connect()
        
        # NULL 값을 포함한 데이터 조회
        results = conn.fetch_as_dict("SELECT * FROM users")
        
        # Assert: NULL 값이 None으로 변환되는지 확인
        assert results[0] == {'ID': 1, 'NAME': 'Alice', 'EMAIL': 'alice@example.com'}
        assert results[1] == {'ID': 2, 'NAME': None, 'EMAIL': 'bob@example.com'}
        assert results[2] == {'ID': 3, 'NAME': 'Charlie', 'EMAIL': None}



def test_convert_datetime_to_iso8601():
    """Oracle 날짜/시간 타입을 ISO 8601 문자열로 변환하는지 확인"""
    # Arrange
    from src.oracle import OracleConnection
    from datetime import datetime
    
    config = {
        "host": "localhost",
        "port": 1521,
        "service_name": "XEPDB1",
        "user": "testuser",
        "password": "testpass"
    }
    
    # Act
    with patch('oracledb.connect') as mock_connect:
        mock_db_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_db_connection.cursor.return_value = mock_cursor
        
        # Mock column descriptions
        mock_cursor.description = [
            ('ID', None, None, None, None, None, None),
            ('NAME', None, None, None, None, None, None),
            ('CREATED_AT', None, None, None, None, None, None)
        ]
        
        # Mock fetchall with datetime values
        mock_cursor.fetchall.return_value = [
            (1, 'Alice', datetime(2024, 1, 15, 10, 30, 45)),
            (2, 'Bob', datetime(2024, 2, 20, 14, 15, 30))
        ]
        
        mock_connect.return_value = mock_db_connection
        
        conn = OracleConnection(config)
        conn.connect()
        
        # 날짜/시간을 ISO 8601 문자열로 변환하여 조회
        results = conn.fetch_as_dict_with_iso_dates("SELECT * FROM users")
        
        # Assert: datetime이 ISO 8601 문자열로 변환되는지 확인
        assert results[0]['CREATED_AT'] == '2024-01-15T10:30:45'
        assert results[1]['CREATED_AT'] == '2024-02-20T14:15:30'
        assert isinstance(results[0]['CREATED_AT'], str)
