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
