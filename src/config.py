"""
설정 관리 모듈
환경 변수에서 Oracle 및 Meilisearch 연결 정보를 로드합니다.
"""
import os


class ConfigError(Exception):
    """설정 관련 에러"""
    pass


def get_oracle_config():
    """환경 변수에서 Oracle 연결 정보를 로드합니다.

    Returns:
        dict: Oracle 연결 정보 딕셔너리
            - host: 호스트 주소
            - port: 포트 번호 (int, 기본값: 1521)
            - service_name: 서비스 이름
            - user: 사용자 이름
            - password: 비밀번호

    Raises:
        ConfigError: 필수 환경 변수가 누락된 경우
    """
    # ORACLE_PORT는 선택적, 나머지는 필수
    required_vars = ["ORACLE_HOST", "ORACLE_SERVICE_NAME", "ORACLE_USER", "ORACLE_PASSWORD"]

    for var in required_vars:
        if var not in os.environ:
            raise ConfigError(f"필수 환경 변수가 설정되지 않았습니다: {var}")

    return {
        "host": os.environ["ORACLE_HOST"],
        "port": int(os.environ.get("ORACLE_PORT", "1521")),
        "service_name": os.environ["ORACLE_SERVICE_NAME"],
        "user": os.environ["ORACLE_USER"],
        "password": os.environ["ORACLE_PASSWORD"],
    }


def get_meilisearch_config():
    """환경 변수에서 Meilisearch 연결 정보를 로드합니다.

    Returns:
        dict: Meilisearch 연결 정보 딕셔너리
            - host: 호스트 주소 (기본값: http://localhost:7700)
            - api_key: API 키

    Raises:
        ConfigError: 필수 환경 변수가 누락된 경우
    """
    # MEILISEARCH_HOST는 선택적 (기본값 있음), API_KEY는 필수
    required_vars = ["MEILISEARCH_API_KEY"]

    for var in required_vars:
        if var not in os.environ:
            raise ConfigError(f"필수 환경 변수가 설정되지 않았습니다: {var}")

    return {
        "host": os.environ.get("MEILISEARCH_HOST", "http://localhost:7700"),
        "api_key": os.environ["MEILISEARCH_API_KEY"],
    }
