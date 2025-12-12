"""
TEST-010: 환경 변수에서 Oracle 연결 정보(host, port, service_name, user, password) 로드
TEST-011: 환경 변수에서 Meilisearch 연결 정보(host, api_key) 로드
TEST-012: 필수 환경 변수 누락 시 명확한 에러 메시지 반환
TEST-013: 기본값 설정 (Meilisearch 기본 포트 7700 등)
"""
import os
import pytest


def test_load_oracle_config_from_env():
    """환경 변수에서 Oracle 연결 정보를 로드하는지 확인"""
    # Arrange: 환경 변수 설정
    os.environ["ORACLE_HOST"] = "localhost"
    os.environ["ORACLE_PORT"] = "1521"
    os.environ["ORACLE_SERVICE_NAME"] = "XEPDB1"
    os.environ["ORACLE_USER"] = "testuser"
    os.environ["ORACLE_PASSWORD"] = "testpass"

    # Act: config 모듈에서 Oracle 설정 로드
    from src.config import get_oracle_config

    config = get_oracle_config()

    # Assert: 모든 설정이 올바르게 로드되었는지 확인
    assert config["host"] == "localhost"
    assert config["port"] == 1521
    assert config["service_name"] == "XEPDB1"
    assert config["user"] == "testuser"
    assert config["password"] == "testpass"

    # Cleanup
    for key in ["ORACLE_HOST", "ORACLE_PORT", "ORACLE_SERVICE_NAME", "ORACLE_USER", "ORACLE_PASSWORD"]:
        os.environ.pop(key, None)


def test_load_meilisearch_config_from_env():
    """환경 변수에서 Meilisearch 연결 정보를 로드하는지 확인"""
    # Arrange: 환경 변수 설정
    os.environ["MEILISEARCH_HOST"] = "http://localhost:7700"
    os.environ["MEILISEARCH_API_KEY"] = "masterKey123"

    # Act: config 모듈에서 Meilisearch 설정 로드
    from src.config import get_meilisearch_config

    config = get_meilisearch_config()

    # Assert: 모든 설정이 올바르게 로드되었는지 확인
    assert config["host"] == "http://localhost:7700"
    assert config["api_key"] == "masterKey123"

    # Cleanup
    for key in ["MEILISEARCH_HOST", "MEILISEARCH_API_KEY"]:
        os.environ.pop(key, None)


def test_missing_oracle_env_raises_clear_error():
    """Oracle 필수 환경 변수 누락 시 명확한 에러 메시지 반환"""
    # Arrange: 환경 변수 제거 (혹시 남아있을 수 있는 것들)
    for key in ["ORACLE_HOST", "ORACLE_PORT", "ORACLE_SERVICE_NAME", "ORACLE_USER", "ORACLE_PASSWORD"]:
        os.environ.pop(key, None)

    # Act & Assert: ORACLE_HOST가 없을 때
    from src.config import get_oracle_config, ConfigError

    with pytest.raises(ConfigError) as exc_info:
        get_oracle_config()

    assert "ORACLE_HOST" in str(exc_info.value)


def test_missing_meilisearch_env_raises_clear_error():
    """Meilisearch 필수 환경 변수 누락 시 명확한 에러 메시지 반환"""
    # Arrange: 환경 변수 제거
    for key in ["MEILISEARCH_HOST", "MEILISEARCH_API_KEY"]:
        os.environ.pop(key, None)

    # Act & Assert: MEILISEARCH_API_KEY가 없을 때 (HOST는 선택적)
    from src.config import get_meilisearch_config, ConfigError

    with pytest.raises(ConfigError) as exc_info:
        get_meilisearch_config()

    assert "MEILISEARCH_API_KEY" in str(exc_info.value)


def test_meilisearch_config_uses_default_host_when_not_set():
    """MEILISEARCH_HOST가 설정되지 않은 경우 기본값 사용"""
    # Arrange: MEILISEARCH_HOST만 제거, API_KEY는 설정
    os.environ.pop("MEILISEARCH_HOST", None)
    os.environ["MEILISEARCH_API_KEY"] = "testKey"

    # Act
    from src.config import get_meilisearch_config

    config = get_meilisearch_config()

    # Assert: 기본 호스트가 설정되어야 함
    assert config["host"] == "http://localhost:7700"
    assert config["api_key"] == "testKey"

    # Cleanup
    os.environ.pop("MEILISEARCH_API_KEY", None)


def test_oracle_config_uses_default_port_when_not_set():
    """ORACLE_PORT가 설정되지 않은 경우 기본값 1521 사용"""
    # Arrange: PORT만 제거, 나머지는 설정
    os.environ["ORACLE_HOST"] = "localhost"
    os.environ.pop("ORACLE_PORT", None)
    os.environ["ORACLE_SERVICE_NAME"] = "XEPDB1"
    os.environ["ORACLE_USER"] = "testuser"
    os.environ["ORACLE_PASSWORD"] = "testpass"

    # Act
    from src.config import get_oracle_config

    config = get_oracle_config()

    # Assert: 기본 포트 1521이 설정되어야 함
    assert config["host"] == "localhost"
    assert config["port"] == 1521
    assert config["service_name"] == "XEPDB1"

    # Cleanup
    for key in ["ORACLE_HOST", "ORACLE_PORT", "ORACLE_SERVICE_NAME", "ORACLE_USER", "ORACLE_PASSWORD"]:
        os.environ.pop(key, None)



def test_load_config_from_dotenv_file_when_env_not_set():
    """TEST-141: 환경 변수 미설정 시 .env 파일 읽기"""
    import tempfile
    import os
    
    # Arrange: Create a temporary .env file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('ORACLE_HOST=dotenv-host\n')
        f.write('ORACLE_PORT=1522\n')
        f.write('ORACLE_SERVICE_NAME=dotenv-service\n')
        f.write('ORACLE_USER=dotenv-user\n')
        f.write('ORACLE_PASSWORD=dotenv-pass\n')
        f.write('MEILISEARCH_HOST=http://dotenv-meilisearch:7700\n')
        f.write('MEILISEARCH_API_KEY=dotenv-key\n')
        dotenv_path = f.name
    
    # Clean up any existing environment variables
    for key in ['ORACLE_HOST', 'ORACLE_PORT', 'ORACLE_SERVICE_NAME', 'ORACLE_USER', 'ORACLE_PASSWORD',
                'MEILISEARCH_HOST', 'MEILISEARCH_API_KEY']:
        os.environ.pop(key, None)
    
    try:
        # Act: Load config from .env file
        from src.config import load_dotenv, get_oracle_config, get_meilisearch_config
        
        load_dotenv(dotenv_path)
        
        oracle_config = get_oracle_config()
        meilisearch_config = get_meilisearch_config()
        
        # Assert: Config should be loaded from .env file
        assert oracle_config['host'] == 'dotenv-host'
        assert oracle_config['port'] == 1522
        assert oracle_config['service_name'] == 'dotenv-service'
        assert oracle_config['user'] == 'dotenv-user'
        assert oracle_config['password'] == 'dotenv-pass'
        
        assert meilisearch_config['host'] == 'http://dotenv-meilisearch:7700'
        assert meilisearch_config['api_key'] == 'dotenv-key'
        
    finally:
        # Cleanup
        os.unlink(dotenv_path)
        for key in ['ORACLE_HOST', 'ORACLE_PORT', 'ORACLE_SERVICE_NAME', 'ORACLE_USER', 'ORACLE_PASSWORD',
                    'MEILISEARCH_HOST', 'MEILISEARCH_API_KEY']:
            os.environ.pop(key, None)
