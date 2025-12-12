"""
Bug Fix Verification: full_sync_batch() with recreate_index=True
"""
from unittest.mock import MagicMock, patch
from src.sync_engine import SyncEngine

def test_full_sync_batch_with_recreate_index_true():
    """recreate_index=True가 정상 작동하는지 확인"""

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

    with patch('src.sync_engine.OracleConnection') as MockOracleConnection, \
         patch('src.sync_engine.MeilisearchClient') as MockMeilisearchClient:

        # Mock Oracle data extraction
        mock_oracle_conn = MagicMock()
        MockOracleConnection.return_value.__enter__.return_value = mock_oracle_conn
        mock_oracle_conn.fetch_as_dict_with_iso_dates.return_value = [
            {'ID': 1, 'NAME': 'Alice'},
            {'ID': 2, 'NAME': 'Bob'},
            {'ID': 3, 'NAME': 'Charlie'}
        ]

        # Mock Meilisearch client
        mock_client = MagicMock()
        mock_index = MagicMock()
        MockMeilisearchClient.return_value = mock_client
        mock_client.get_client.return_value = None
        mock_client.get_index.return_value = mock_index
        mock_client.index_exists.return_value = True
        mock_client.delete_index.return_value = {'taskUid': 456}
        mock_client.create_index.return_value = {'taskUid': 789}
        mock_index.add_documents.return_value = {'taskUid': 123}

        sync_engine = SyncEngine(oracle_config, meilisearch_config)

        # This should now work without AttributeError
        result = sync_engine.full_sync_batch('users', primary_key='ID', batch_size=3, recreate_index=True)

        # Verify that index was recreated
        mock_client.index_exists.assert_called_once_with('users')
        mock_client.delete_index.assert_called_once_with('users')
        mock_client.create_index.assert_called_once_with('users', 'ID')

        # Verify sync result
        assert result['success'] is True
        assert result['total_records'] == 3
        assert result['successful_records'] == 3
        assert result['failed_batches'] == 0

        print("SUCCESS: Bug fix verified! recreate_index=True works correctly.")

if __name__ == "__main__":
    test_full_sync_batch_with_recreate_index_true()
