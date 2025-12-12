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


    def __enter__(self):
        """컨텍스트 매니저 진입 시 연결 생성

        Returns:
            oracledb.Connection: Oracle 연결 객체
        """
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료 시 연결 해제

        Args:
            exc_type: 예외 타입
            exc_val: 예외 값
            exc_tb: 예외 트레이스백
        """
        if self._connection:
            self._connection.close()


    def fetch_all(self, query):
        """테이블에서 전체 레코드 조회

        Args:
            query (str): SQL 쿼리

        Returns:
            list: 조회 결과 (튜플 리스트)
        """
        cursor = self._connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return results


    def fetch_as_dict(self, query):
        """테이블에서 레코드를 조회하여 딕셔너리 리스트로 변환

        Args:
            query (str): SQL 쿼리

        Returns:
            list: 딕셔너리 리스트 (컬럼명: 값)
        """
        cursor = self._connection.cursor()
        cursor.execute(query)
        
        # 컬럼명 추출
        columns = [desc[0] for desc in cursor.description]
        
        # 결과를 딕셔너리 리스트로 변환
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results


    def fetch_batches(self, query, batch_size=1000):
        """배치 단위로 데이터 조회 (제너레이터)

        Args:
            query (str): SQL 쿼리
            batch_size (int): 배치 크기 (기본값: 1000)

        Yields:
            list: 배치 단위의 레코드 리스트
        """
        cursor = self._connection.cursor()
        cursor.execute(query)
        
        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break
            yield batch


    def fetch_incremental(self, query, last_sync_time):
        """마지막 동기화 시간 이후 변경된 레코드 조회

        Args:
            query (str): SQL 쿼리 (파라미터 바인딩 포함)
            last_sync_time (datetime): 마지막 동기화 시간

        Returns:
            list: 조회 결과 (튜플 리스트)
        """
        cursor = self._connection.cursor()
        cursor.execute(query, last_sync=last_sync_time)
        results = cursor.fetchall()
        return results


    def fetch_as_dict_with_iso_dates(self, query):
        """테이블에서 레코드를 조회하여 딕셔너리 리스트로 변환 (datetime을 ISO 8601 문자열로 변환)

        Args:
            query (str): SQL 쿼리

        Returns:
            list: 딕셔너리 리스트 (컬럼명: 값, datetime은 ISO 8601 문자열)
        """
        from datetime import datetime
        
        cursor = self._connection.cursor()
        cursor.execute(query)
        
        # 컬럼명 추출
        columns = [desc[0] for desc in cursor.description]
        
        # 결과를 딕셔너리 리스트로 변환 (datetime을 ISO 8601로 변환)
        results = []
        for row in cursor.fetchall():
            row_dict = {}
            for col, value in zip(columns, row):
                # datetime 객체를 ISO 8601 문자열로 변환
                if isinstance(value, datetime):
                    row_dict[col] = value.isoformat()
                else:
                    row_dict[col] = value
            results.append(row_dict)
        
        return results

    def execute(self, query, params=None):
        """SQL 쿼리를 실행 (INSERT, UPDATE, DELETE, CREATE, DROP 등)

        Args:
            query (str): 실행할 SQL 쿼리
            params (tuple, optional): 쿼리 파라미터

        Returns:
            None
        """
        cursor = self._connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self._connection.commit()
        cursor.close()



class OracleConnectionPool:
    """Oracle 데이터베이스 연결 풀 클래스"""

    def __init__(self, config):
        """Oracle 연결 풀 초기화

        Args:
            config (dict): Oracle 연결 정보
                - host: 호스트 주소
                - port: 포트 번호
                - service_name: 서비스 이름
                - user: 사용자 이름
                - password: 비밀번호
                - min_pool_size: 최소 연결 풀 크기
                - max_pool_size: 최대 연결 풀 크기
        """
        self.config = config
        self.pool = None

    def create_pool(self):
        """연결 풀 생성

        Returns:
            oracledb.ConnectionPool: 연결 풀 객체
        """
        self.pool = oracledb.create_pool(
            host=self.config["host"],
            port=self.config["port"],
            service_name=self.config["service_name"],
            user=self.config["user"],
            password=self.config["password"],
            min=self.config["min_pool_size"],
            max=self.config["max_pool_size"]
        )
        return self.pool

    def acquire(self):
        """연결 풀에서 연결 가져오기

        Returns:
            oracledb.Connection: 연결 객체
        """
        return self.pool.acquire()

    def close(self):
        """연결 풀 닫기"""
        self.pool.close()


    def __enter__(self):
        """컨텍스트 매니저 진입 시 연결 획득

        Returns:
            oracledb.Connection: 연결 객체
        """
        self._connection = self.acquire()
        return self._connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료 시 연결 해제

        Args:
            exc_type: 예외 타입
            exc_val: 예외 값
            exc_tb: 예외 트레이스백
        """
        if self._connection:
            self._connection.close()
