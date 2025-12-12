"""
동기화 엔진 모듈

Oracle 데이터베이스와 Meilisearch 간의 데이터 동기화를 담당합니다.
"""
import logging
from datetime import datetime
from src.oracle import OracleConnection
from src.meilisearch_client import MeilisearchClient

# Configure logger
logger = logging.getLogger(__name__)


class SyncEngine:
    """Oracle과 Meilisearch 간 데이터 동기화 엔진"""

    def __init__(self, oracle_config, meilisearch_config):
        """동기화 엔진 초기화

        Args:
            oracle_config (dict): Oracle 연결 설정
            meilisearch_config (dict): Meilisearch 연결 설정
        """
        self.oracle_config = oracle_config
        self.meilisearch_config = meilisearch_config
        self._last_sync_timestamps = {}
        self._sync_history = {}  # Store sync history by table_name as a list  # Store sync status by table_name

    def extract_from_oracle(self, table_name):
        """Oracle에서 전체 데이터 추출

        Args:
            table_name (str): 조회할 테이블 이름

        Returns:
            list: 딕셔너리 리스트 형태의 레코드
        """
        with OracleConnection(self.oracle_config) as conn:
            query = f"SELECT * FROM {table_name}"
            results = conn.fetch_as_dict_with_iso_dates(query)
            return results

    def extract_changed_records(self, table_name, modified_column, last_sync_timestamp):
        """마지막 동기화 시점 이후 변경된 레코드만 추출

        Args:
            table_name (str): 조회할 테이블 이름
            modified_column (str): 수정 시간 컬럼 이름
            last_sync_timestamp (datetime): 마지막 동기화 시점

        Returns:
            list: 변경된 레코드의 딕셔너리 리스트
        """
        with OracleConnection(self.oracle_config) as conn:
            # Convert datetime to Oracle-compatible format
            timestamp_str = last_sync_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            query = f"SELECT * FROM {table_name} WHERE {modified_column} > TO_TIMESTAMP('{timestamp_str}', 'YYYY-MM-DD HH24:MI:SS')"
            results = conn.fetch_as_dict_with_iso_dates(query)
            return results

    def extract_deleted_records(self, table_name, modified_column, delete_flag_column, last_sync_timestamp):
        """마지막 동기화 시점 이후 삭제된 레코드 추출 (soft delete)

        Args:
            table_name (str): 조회할 테이블 이름
            modified_column (str): 수정 시간 컬럼 이름
            delete_flag_column (str): soft delete 플래그 컬럼 이름
            last_sync_timestamp (datetime): 마지막 동기화 시점

        Returns:
            list: 삭제된 레코드의 딕셔너리 리스트
        """
        with OracleConnection(self.oracle_config) as conn:
            # Convert datetime to Oracle-compatible format
            timestamp_str = last_sync_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            query = f"SELECT * FROM {table_name} WHERE {modified_column} > TO_TIMESTAMP('{timestamp_str}', 'YYYY-MM-DD HH24:MI:SS') AND {delete_flag_column} = 1"
            results = conn.fetch_as_dict_with_iso_dates(query)
            return results


    def transform_to_documents(self, data, primary_key):
        """추출된 데이터를 Meilisearch 문서 형식으로 변환

        Args:
            data (list): Oracle에서 추출한 딕셔너리 리스트
            primary_key (str): Meilisearch primary key 필드명

        Returns:
            list: Meilisearch 문서 형식의 딕셔너리 리스트
        """
        # 현재 단계에서는 데이터가 이미 딕셔너리 형식이므로 그대로 반환
        return data


    def insert_documents_batch(self, index_name, documents):
        """Meilisearch에 배치 단위로 문서 삽입

        Args:
            index_name (str): Meilisearch 인덱스 이름
            documents (list): 삽입할 문서 리스트

        Returns:
            dict: 작업 정보 (taskUid 포함)
        """
        client = MeilisearchClient(self.meilisearch_config)
        client.get_client()
        index = client.get_index(index_name)
        
        # Log progress with record count
        logger.info(f"Processing batch: {len(documents)} records to be inserted into '{index_name}'")
        
        return index.add_documents(documents)

    def upsert_documents(self, index_name, documents):
        """Meilisearch에 문서를 upsert (update or insert)

        Args:
            index_name (str): Meilisearch 인덱스 이름
            documents (list): upsert할 문서 리스트

        Returns:
            dict: 작업 정보 (taskUid 포함)
        """
        client = MeilisearchClient(self.meilisearch_config)
        client.get_client()
        index = client.get_index(index_name)
        return index.update_documents(documents)


    def full_sync(self, table_name, primary_key, recreate_index=False):
        """Oracle에서 전체 데이터를 추출하여 Meilisearch에 동기화

        Args:
            table_name (str): Oracle 테이블 이름 (Meilisearch 인덱스 이름으로도 사용)
            primary_key (str): Meilisearch primary key 필드명
            recreate_index (bool): 기존 인덱스를 삭제 후 재생성할지 여부 (기본값: False)

        Returns:
            dict: 동기화 결과
                - success (bool): 성공 여부
                - oracle_count (int): Oracle에서 추출한 레코드 수
                - meilisearch_count (int): Meilisearch에 저장된 문서 수
        """
        # Log sync start
        logger.info(f"Starting full sync for table '{table_name}'")
        
        try:
            client = MeilisearchClient(self.meilisearch_config)
            client.get_client()
            
            # 0. (옵션) 기존 인덱스 삭제 후 재생성
            if recreate_index:
                if client.index_exists(table_name):
                    client.delete_index(table_name)
                client.create_index(table_name, primary_key)
            
            # 1. Oracle에서 전체 데이터 추출
            oracle_data = self.extract_from_oracle(table_name)
            oracle_count = len(oracle_data)
            
            # 2. Meilisearch 문서 형식으로 변환
            documents = self.transform_to_documents(oracle_data, primary_key)
            
            # 3. Meilisearch에 배치 삽입
            self.insert_documents_batch(table_name, documents)
            
            # 4. Meilisearch 문서 수 확인
            index = client.get_index(table_name)
            stats = index.get_stats()
            meilisearch_count = stats['numberOfDocuments']
            
            # Log sync completion
            logger.info(f"Full sync completed for table '{table_name}': {meilisearch_count} documents synced")
            
            return {
                'success': True,
                'oracle_count': oracle_count,
                'meilisearch_count': meilisearch_count
            }
        except Exception as e:
            # Log detailed error information
            logger.error(f"Full sync failed for table '{table_name}': {type(e).__name__}: {str(e)}")
            raise

    def incremental_sync(self, table_name, primary_key, modified_column):
        """Oracle에서 변경된 데이터만 추출하여 Meilisearch에 동기화

        Args:
            table_name (str): Oracle 테이블 이름 (Meilisearch 인덱스 이름으로도 사용)
            primary_key (str): Meilisearch primary key 필드명
            modified_column (str): 수정 시간 컬럼 이름

        Returns:
            dict: 동기화 결과
                - success (bool): 성공 여부
                - changed_count (int): 변경된 레코드 수
        """
        # 1. 마지막 동기화 시점 조회
        last_sync = self.get_last_sync_timestamp(table_name)
        
        # 2. 변경된 레코드 추출
        changed_records = self.extract_changed_records(table_name, modified_column, last_sync)
        changed_count = len(changed_records)
        
        # 3. 변경된 레코드를 Meilisearch에 upsert
        if changed_count > 0:
            documents = self.transform_to_documents(changed_records, primary_key)
            self.upsert_documents(table_name, documents)
        
        # 4. 동기화 시점 업데이트
        current_time = datetime.now()
        self.save_last_sync_timestamp(table_name, current_time)
        
        return {
            'success': True,
            'changed_count': changed_count
        }

    
    def full_sync_with_retry(self, index_name: str, primary_key: str, recreate_index: bool = False, max_retries: int = 3):
        """
        Full Sync with retry logic and exponential backoff.
        
        Args:
            index_name: Name of the Meilisearch index
            primary_key: Primary key field name
            recreate_index: Whether to recreate the index before syncing
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            dict: Sync result including success status and retry count
        """
        import time
        from datetime import datetime
        
        retry_count = 0
        last_exception = None
        
        while retry_count < max_retries:
            try:
                result = self.full_sync(index_name, primary_key, recreate_index)
                return {
                    **result,
                    'retry_count': retry_count
                }
            except Exception as e:
                retry_count += 1
                last_exception = e
                if retry_count >= max_retries:
                    break
                
                # Exponential backoff: 2^(retry_count - 1) seconds
                delay = 2 ** (retry_count - 1)
                time.sleep(delay)
        
        # All retries failed - log error information
        return {
            'success': False,
            'retry_count': retry_count,
            'error': str(last_exception),
            'index_name': index_name,
            'timestamp': datetime.now().isoformat()
        }

    
    def full_sync_batch(self, index_name: str, primary_key: str, batch_size: int = 1000, recreate_index: bool = False):
        """
        Full Sync with batch processing and partial failure tracking.

        Args:
            index_name: Name of the Meilisearch index
            primary_key: Primary key field name
            batch_size: Number of records per batch
            recreate_index: Whether to recreate the index before syncing

        Returns:
            dict: Sync result including success status and failed batch information
        """
        # Recreate index if requested
        if recreate_index:
            client = MeilisearchClient(self.meilisearch_config)
            client.get_client()
            if client.index_exists(index_name):
                client.delete_index(index_name)
            client.create_index(index_name, primary_key)
        
        # Extract all data from Oracle
        data = self.extract_from_oracle(index_name)
        documents = self.transform_to_documents(data, primary_key)
        
        total_records = len(documents)
        successful_records = 0
        failed_batches = 0
        failed_batch_info = []
        
        # Process in batches
        batch_number = 0
        for i in range(0, len(documents), batch_size):
            batch_number += 1
            batch = documents[i:i + batch_size]
            
            try:
                self.insert_documents_batch(index_name, batch)
                successful_records += len(batch)
            except Exception as e:
                failed_batches += 1
                failed_batch_info.append({
                    'batch_number': batch_number,
                    'error': str(e),
                    'record_count': len(batch)
                })
        
        # Check if all batches succeeded
        success = failed_batches == 0
        
        return {
            'success': success,
            'total_records': total_records,
            'successful_records': successful_records,
            'failed_batches': failed_batches,
            'failed_batch_info': failed_batch_info
        }

    def save_last_sync_timestamp(self, table_name, timestamp):
        """마지막 동기화 시점을 저장

        Args:
            table_name (str): 테이블 이름
            timestamp (datetime): 동기화 시점
        """
        self._last_sync_timestamps[table_name] = timestamp

    def get_last_sync_timestamp(self, table_name):
        """마지막 동기화 시점을 조회

        Args:
            table_name (str): 테이블 이름

        Returns:
            datetime: 마지막 동기화 시점 (없으면 None)
        """
        return self._last_sync_timestamps.get(table_name)

    def save_sync_status(self, table_name, start_time, end_time, record_count, status):
        """동기화 상태 저장

        Args:
            table_name (str): 테이블 이름
            start_time (datetime): 동기화 시작 시간
            end_time (datetime): 동기화 종료 시간
            record_count (int): 처리된 레코드 수
            status (str): 동기화 상태 ('success', 'failed', 'partial')
        """
        if table_name not in self._sync_history:
            self._sync_history[table_name] = []
        
        self._sync_history[table_name].append({
            'table_name': table_name,
            'start_time': start_time,
            'end_time': end_time,
            'record_count': record_count,
            'status': status
        })

    def get_sync_status(self, table_name):
        """동기화 상태 조회 (최신 상태)

        Args:
            table_name (str): 테이블 이름

        Returns:
            dict: 동기화 상태 정보 또는 None
        """
        if table_name in self._sync_history and len(self._sync_history[table_name]) > 0:
            return self._sync_history[table_name][-1]
        return None

    def get_last_successful_sync(self, table_name):
        """마지막 성공한 동기화 정보 조회

        Args:
            table_name (str): 테이블 이름

        Returns:
            dict: 마지막 성공한 동기화 상태 정보 또는 None
        """
        if table_name not in self._sync_history:
            return None
        
        # Find the most recent successful sync
        for status in reversed(self._sync_history[table_name]):
            if status['status'] == 'success':
                return status
        
        return None

    def get_sync_history(self, table_name):
        """동기화 히스토리 조회

        Args:
            table_name (str): 테이블 이름

        Returns:
            list: 동기화 히스토리 (시간순 정렬) 또는 빈 리스트
        """
        return self._sync_history.get(table_name, [])
