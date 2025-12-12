"""
TEST-040: Meilisearch 클라이언트 생성
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


def test_create_meilisearch_client():
    """Meilisearch 클라이언트를 생성할 수 있는지 확인"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act & Assert: MeilisearchClient 객체가 생성되는지 확인
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        
        assert client is not None
        assert isinstance(client, MeilisearchClient)


def test_client_initialization_with_credentials():
    """Meilisearch 클라이언트가 올바른 인증 정보로 초기화되는지 확인"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        result = client.get_client()
        
        # Assert: Client가 올바른 인증 정보로 생성되는지 확인
        mock_client.assert_called_once_with(
            config["host"],
            config["api_key"]
        )
        assert result == mock_instance



def test_meilisearch_health_check():
    """Meilisearch 서버 health check를 수행할 수 있는지 확인"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_instance.health.return_value = {"status": "available"}
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # Health check 수행
        health = client.health_check()
        
        # Assert: health check가 호출되고 결과가 반환되는지 확인
        mock_instance.health.assert_called_once()
        assert health == {"status": "available"}


def test_health_check_returns_true_when_available():
    """Meilisearch 서버가 사용 가능할 때 True를 반환하는지 확인"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_instance.health.return_value = {"status": "available"}
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # Health check 수행
        is_healthy = client.is_healthy()
        
        # Assert: 서버가 사용 가능할 때 True 반환
        assert is_healthy is True



def test_connection_failure_raises_exception():
    """Meilisearch 연결 실패 시 적절한 예외를 발생시키는지 확인"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://invalid-host:7700",
        "api_key": "invalid_key"
    }
    
    # Act & Assert
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        # health() 호출 시 일반 예외 발생 (연결 실패)
        mock_instance.health.side_effect = Exception("Connection failed")
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 연결 실패 시 예외가 발생하는지 확인
        with pytest.raises(Exception):
            client.health_check()



def test_check_index_exists():
    """인덱스가 존재하는지 확인할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_index = Mock()
        mock_instance.get_index.return_value = mock_index
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 인덱스 존재 여부 확인
        exists = client.index_exists("users")
        
        # Assert: get_index가 호출되고 True 반환
        mock_instance.get_index.assert_called_once_with("users")
        assert exists is True


def test_check_index_not_exists():
    """인덱스가 존재하지 않을 때 False를 반환하는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        # 인덱스가 없을 때 예외 발생
        mock_instance.get_index.side_effect = Exception("Index not found")
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 인덱스 존재 여부 확인
        exists = client.index_exists("nonexistent")
        
        # Assert: False 반환
        assert exists is False



def test_create_index_with_primary_key():
    """인덱스를 primary key와 함께 생성할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_task = Mock()
        mock_task.task_uid = 1
        mock_instance.create_index.return_value = mock_task
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 인덱스 생성
        task = client.create_index("users", primary_key="id")
        
        # Assert: create_index가 호출되고 task가 반환됨
        mock_instance.create_index.assert_called_once_with("users", {"primaryKey": "id"})
        assert task.task_uid == 1


def test_update_index_searchable_attributes():
    """인덱스의 searchable attributes를 업데이트할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_index = Mock()
        mock_task = Mock()
        mock_task.task_uid = 2
        mock_index.update_searchable_attributes.return_value = mock_task
        mock_instance.get_index.return_value = mock_index
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # searchable attributes 업데이트
        searchable_attrs = ["name", "email", "description"]
        task = client.update_searchable_attributes("users", searchable_attrs)
        
        # Assert: update_searchable_attributes가 호출되고 task가 반환됨
        mock_instance.get_index.assert_called_once_with("users")
        mock_index.update_searchable_attributes.assert_called_once_with(searchable_attrs)
        assert task.task_uid == 2


def test_update_index_filterable_attributes():
    """인덱스의 filterable attributes를 업데이트할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_index = Mock()
        mock_task = Mock()
        mock_task.task_uid = 3
        mock_index.update_filterable_attributes.return_value = mock_task
        mock_instance.get_index.return_value = mock_index
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # filterable attributes 업데이트
        filterable_attrs = ["status", "created_at", "category"]
        task = client.update_filterable_attributes("users", filterable_attrs)
        
        # Assert: update_filterable_attributes가 호출되고 task가 반환됨
        mock_instance.get_index.assert_called_once_with("users")
        mock_index.update_filterable_attributes.assert_called_once_with(filterable_attrs)
        assert task.task_uid == 3


def test_update_index_settings():
    """인덱스의 여러 설정을 한 번에 업데이트할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_index = Mock()
        mock_task = Mock()
        mock_task.task_uid = 4
        mock_index.update_settings.return_value = mock_task
        mock_instance.get_index.return_value = mock_index
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 인덱스 설정 업데이트
        settings = {
            "searchableAttributes": ["name", "email"],
            "filterableAttributes": ["status", "created_at"],
            "sortableAttributes": ["created_at"]
        }
        task = client.update_index_settings("users", settings)
        
        # Assert: update_settings가 호출되고 task가 반환됨
        mock_instance.get_index.assert_called_once_with("users")
        mock_index.update_settings.assert_called_once_with(settings)
        assert task.task_uid == 4


def test_delete_index():
    """인덱스를 삭제할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_index = Mock()
        mock_task = Mock()
        mock_task.task_uid = 5
        mock_index.delete.return_value = mock_task
        mock_instance.get_index.return_value = mock_index
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 인덱스 삭제
        task = client.delete_index("users")
        
        # Assert: delete가 호출되고 task가 반환됨
        mock_instance.get_index.assert_called_once_with("users")
        mock_index.delete.assert_called_once()
        assert task.task_uid == 5


def test_add_single_document():
    """단일 문서를 추가할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_index = Mock()
        mock_task = Mock()
        mock_task.task_uid = 6
        mock_index.add_documents.return_value = mock_task
        mock_instance.get_index.return_value = mock_index
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 단일 문서 추가
        document = {"id": 1, "name": "John Doe", "email": "john@example.com"}
        task = client.add_document("users", document)
        
        # Assert: add_documents가 호출되고 task가 반환됨
        mock_instance.get_index.assert_called_once_with("users")
        mock_index.add_documents.assert_called_once_with([document])
        assert task.task_uid == 6


def test_add_batch_documents():
    """배치로 여러 문서를 추가할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_index = Mock()
        mock_task = Mock()
        mock_task.task_uid = 7
        mock_index.add_documents.return_value = mock_task
        mock_instance.get_index.return_value = mock_index
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 배치 문서 추가
        documents = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
            {"id": 3, "name": "Bob Johnson", "email": "bob@example.com"}
        ]
        task = client.add_documents("users", documents)
        
        # Assert: add_documents가 호출되고 task가 반환됨
        mock_instance.get_index.assert_called_once_with("users")
        mock_index.add_documents.assert_called_once_with(documents)
        assert task.task_uid == 7


def test_update_documents():
    """문서를 업데이트(upsert)할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_index = Mock()
        mock_task = Mock()
        mock_task.task_uid = 8
        mock_index.update_documents.return_value = mock_task
        mock_instance.get_index.return_value = mock_index
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 문서 업데이트
        documents = [
            {"id": 1, "name": "John Doe Updated", "email": "john.new@example.com"},
            {"id": 2, "name": "Jane Smith Updated", "email": "jane.new@example.com"}
        ]
        task = client.update_documents("users", documents)
        
        # Assert: update_documents가 호출되고 task가 반환됨
        mock_instance.get_index.assert_called_once_with("users")
        mock_index.update_documents.assert_called_once_with(documents)
        assert task.task_uid == 8


def test_delete_document():
    """문서를 삭제할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_index = Mock()
        mock_task = Mock()
        mock_task.task_uid = 9
        mock_index.delete_document.return_value = mock_task
        mock_instance.get_index.return_value = mock_index
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 문서 삭제
        document_id = "1"
        task = client.delete_document("users", document_id)
        
        # Assert: delete_document가 호출되고 task가 반환됨
        mock_instance.get_index.assert_called_once_with("users")
        mock_index.delete_document.assert_called_once_with(document_id)
        assert task.task_uid == 9


def test_delete_documents():
    """여러 문서를 삭제할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_index = Mock()
        mock_task = Mock()
        mock_task.task_uid = 10
        mock_index.delete_documents.return_value = mock_task
        mock_instance.get_index.return_value = mock_index
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 여러 문서 삭제
        document_ids = ["1", "2", "3"]
        task = client.delete_documents("users", document_ids)
        
        # Assert: delete_documents가 호출되고 task가 반환됨
        mock_instance.get_index.assert_called_once_with("users")
        mock_index.delete_documents.assert_called_once_with(document_ids)
        assert task.task_uid == 10


def test_wait_for_task():
    """작업 완료를 대기할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_task_result = Mock()
        mock_task_result.status = "succeeded"
        mock_instance.wait_for_task.return_value = mock_task_result
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 작업 완료 대기
        task_uid = 1
        result = client.wait_for_task(task_uid)
        
        # Assert: wait_for_task가 호출되고 결과가 반환됨
        mock_instance.wait_for_task.assert_called_once_with(task_uid)
        assert result.status == "succeeded"


def test_wait_for_task_with_timeout():
    """타임아웃을 설정하여 작업 완료를 대기할 수 있는지 테스트"""
    # Arrange
    from src.meilisearch_client import MeilisearchClient
    
    config = {
        "host": "http://localhost:7700",
        "api_key": "test_master_key"
    }
    
    # Act
    with patch('meilisearch.Client') as mock_client:
        mock_instance = Mock()
        mock_task_result = Mock()
        mock_task_result.status = "succeeded"
        mock_instance.wait_for_task.return_value = mock_task_result
        mock_client.return_value = mock_instance
        
        client = MeilisearchClient(config)
        client.get_client()
        
        # 타임아웃을 설정하여 작업 완료 대기
        task_uid = 1
        timeout_ms = 5000
        result = client.wait_for_task(task_uid, timeout_in_ms=timeout_ms)
        
        # Assert: wait_for_task가 타임아웃과 함께 호출됨
        mock_instance.wait_for_task.assert_called_once_with(task_uid, timeout_in_ms=timeout_ms)
        assert result.status == "succeeded"
