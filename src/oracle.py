"""
Oracle 데이터베이스 연결 관리 모듈
"""
import oracledb


class OracleConnection:
    """Oracle 데이터베이스 연결 클래스"""

    def __init__(self, config):
        """Oracle 연결 초기화

        Args:
            config (dict): Oracle 연결 정보
                - host: 호스트 주소
                - port: 포트 번호
                - service_name: 서비스 이름
                - user: 사용자 이름
                - password: 비밀번호
        """
        self.config = config
        self._connection = None

    def connect(self):
        """Oracle 데이터베이스에 연결

        Returns:
            oracledb.Connection: Oracle 연결 객체
        """
        self._connection = oracledb.connect(
            host=self.config["host"],
            port=self.config["port"],
            service_name=self.config["service_name"],
            user=self.config["user"],
            password=self.config["password"]
        )
        return self._connection
