"""
Meilisearch 클라이언트 관리 모듈
"""
import meilisearch


class MeilisearchClient:
    """Meilisearch 클라이언트 클래스"""

    def __init__(self, config):
        """Meilisearch 클라이언트 초기화

        Args:
            config (dict): Meilisearch 연결 정보
                - host: 호스트 주소
                - api_key: API 키
        """
        self.config = config
        self._client = None

    def get_client(self):
        """Meilisearch 클라이언트 생성

        Returns:
            meilisearch.Client: Meilisearch 클라이언트 객체
        """
        self._client = meilisearch.Client(
            self.config["host"],
            self.config["api_key"]
        )
        return self._client


    def get_index(self, index_name):
        """인덱스 객체 가져오기

        Args:
            index_name (str): 인덱스 이름

        Returns:
            Index: Meilisearch 인덱스 객체
        """
        return self._client.get_index(index_name)


    def health_check(self):
        """Meilisearch 서버 health check

        Returns:
            dict: health check 결과
        """
        return self._client.health()

    def is_healthy(self):
        """Meilisearch 서버가 사용 가능한지 확인

        Returns:
            bool: 서버가 사용 가능하면 True
        """
        health = self.health_check()
        return health.get("status") == "available"


    def index_exists(self, index_name):
        """인덱스가 존재하는지 확인

        Args:
            index_name (str): 인덱스 이름

        Returns:
            bool: 인덱스가 존재하면 True, 아니면 False
        """
        try:
            self._client.get_index(index_name)
            return True
        except Exception:
            return False


    def create_index(self, index_name, primary_key):
        """인덱스 생성

        Args:
            index_name (str): 인덱스 이름
            primary_key (str): Primary key 필드 이름

        Returns:
            Task: 인덱스 생성 작업
        """
        return self._client.create_index(index_name, {"primaryKey": primary_key})


    def update_searchable_attributes(self, index_name, searchable_attributes):
        """인덱스의 searchable attributes 업데이트

        Args:
            index_name (str): 인덱스 이름
            searchable_attributes (list): 검색 가능한 필드 목록

        Returns:
            Task: 업데이트 작업
        """
        index = self._client.get_index(index_name)
        return index.update_searchable_attributes(searchable_attributes)

    def update_filterable_attributes(self, index_name, filterable_attributes):
        """인덱스의 filterable attributes 업데이트

        Args:
            index_name (str): 인덱스 이름
            filterable_attributes (list): 필터링 가능한 필드 목록

        Returns:
            Task: 업데이트 작업
        """
        index = self._client.get_index(index_name)
        return index.update_filterable_attributes(filterable_attributes)

    def update_index_settings(self, index_name, settings):
        """인덱스 설정 업데이트

        Args:
            index_name (str): 인덱스 이름
            settings (dict): 인덱스 설정
                - searchableAttributes: 검색 가능한 필드 목록
                - filterableAttributes: 필터링 가능한 필드 목록
                - sortableAttributes: 정렬 가능한 필드 목록 등

        Returns:
            Task: 업데이트 작업
        """
        index = self._client.get_index(index_name)
        return index.update_settings(settings)


    def delete_index(self, index_name):
        """인덱스 삭제

        Args:
            index_name (str): 인덱스 이름

        Returns:
            Task: 삭제 작업
        """
        index = self._client.get_index(index_name)
        return index.delete()


    def add_document(self, index_name, document):
        """단일 문서 추가

        Args:
            index_name (str): 인덱스 이름
            document (dict): 추가할 문서

        Returns:
            Task: 문서 추가 작업
        """
        index = self._client.get_index(index_name)
        return index.add_documents([document])


    def add_documents(self, index_name, documents):
        """배치로 여러 문서 추가

        Args:
            index_name (str): 인덱스 이름
            documents (list): 추가할 문서 리스트

        Returns:
            Task: 문서 추가 작업
        """
        index = self._client.get_index(index_name)
        return index.add_documents(documents)


    def update_documents(self, index_name, documents):
        """문서 업데이트 (upsert 방식)

        Args:
            index_name (str): 인덱스 이름
            documents (list): 업데이트할 문서 리스트

        Returns:
            Task: 문서 업데이트 작업
        """
        index = self._client.get_index(index_name)
        return index.update_documents(documents)


    def delete_document(self, index_name, document_id):
        """단일 문서 삭제

        Args:
            index_name (str): 인덱스 이름
            document_id (str): 삭제할 문서 ID

        Returns:
            Task: 문서 삭제 작업
        """
        index = self._client.get_index(index_name)
        return index.delete_document(document_id)

    def delete_documents(self, index_name, document_ids):
        """여러 문서 삭제

        Args:
            index_name (str): 인덱스 이름
            document_ids (list): 삭제할 문서 ID 리스트

        Returns:
            Task: 문서 삭제 작업
        """
        index = self._client.get_index(index_name)
        return index.delete_documents(document_ids)


    def wait_for_task(self, task_uid, timeout_in_ms=None):
        """작업 완료 대기

        Args:
            task_uid (int): 작업 UID
            timeout_in_ms (int, optional): 타임아웃 (밀리초)

        Returns:
            Task: 완료된 작업 정보
        """
        if timeout_in_ms is not None:
            return self._client.wait_for_task(task_uid, timeout_in_ms=timeout_in_ms)
        return self._client.wait_for_task(task_uid)
