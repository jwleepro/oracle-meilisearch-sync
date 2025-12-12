"""
TEST-120: 주기적 Incremental Sync 실행
TEST-121: Cron 표현식 파싱
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time


class TestScheduler:
    """스케줄러 통합 테스트"""
    
    def test_periodic_incremental_sync_execution(self):
        """TEST-120: 주기적 Incremental Sync 실행
        
        스케줄러가 지정된 간격으로 incremental sync를 실행하는지 확인
        """
        from src.scheduler import Scheduler
        from src.sync_engine import SyncEngine
        
        # Mock SyncEngine
        mock_sync_engine = Mock(spec=SyncEngine)
        mock_sync_engine.incremental_sync = Mock(return_value={'status': 'success', 'records_synced': 5})
        
        # Create scheduler with 1 second interval
        scheduler = Scheduler(sync_engine=mock_sync_engine, interval_seconds=1)
        
        # Start scheduler in background
        scheduler.start()
        
        try:
            # Wait for at least 2 executions (2+ seconds)
            time.sleep(2.5)
            
            # Verify incremental_sync was called at least 2 times
            assert mock_sync_engine.incremental_sync.call_count >= 2, \
                f"Expected at least 2 calls, got {mock_sync_engine.incremental_sync.call_count}"
        finally:
            # Stop scheduler
            scheduler.stop()
            
        # Verify scheduler stopped cleanly
        assert scheduler.is_running() is False
    
    def test_cron_expression_parsing(self):
        """TEST-121: Cron 표현식 파싱
        
        Cron 표현식을 파싱하여 다음 실행 시간을 계산할 수 있는지 확인
        """
        from src.scheduler import CronScheduler
        
        # Create a cron scheduler with "*/5 * * * *" (every 5 minutes)
        cron_scheduler = CronScheduler(cron_expression="*/5 * * * *")
        
        # Get next execution time
        next_run = cron_scheduler.get_next_run_time()
        
        # Verify next run time is a datetime object
        assert isinstance(next_run, datetime), "Next run time should be a datetime object"
        
        # Verify next run time is in the future
        assert next_run > datetime.now(), "Next run time should be in the future"
        
        # Verify next run time is within 5 minutes
        time_diff = (next_run - datetime.now()).total_seconds()
        assert 0 < time_diff <= 300, f"Next run should be within 5 minutes, got {time_diff} seconds"
