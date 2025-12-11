"""
TEST-001: pytest 실행 확인 - 빈 테스트가 통과하는지 확인
TEST-002: python-oracledb 패키지 import 가능 확인
TEST-003: meilisearch 패키지 import 가능 확인
"""


def test_pytest_is_working():
    """빈 테스트가 통과하는지 확인"""
    assert True


def test_oracledb_package_is_importable():
    """python-oracledb 패키지를 import 할 수 있는지 확인"""
    try:
        import oracledb
        assert oracledb is not None
    except ImportError as e:
        assert False, f"oracledb 패키지를 import 할 수 없습니다: {e}"


def test_meilisearch_package_is_importable():
    """meilisearch 패키지를 import 할 수 있는지 확인"""
    try:
        import meilisearch
        assert meilisearch is not None
    except ImportError as e:
        assert False, f"meilisearch 패키지를 import 할 수 없습니다: {e}"
