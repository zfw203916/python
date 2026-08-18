"""Database tests with transaction rollback."""

from __future__ import annotations
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.models.db import Base, User


# @pytest.fixture(scope="module") # ❌ 整个模块共享一个数据库，测试互相污染
@pytest.fixture(scope="function")  # ✅ 每个测试函数独立数据库，测试互相隔离
def db_session():
    """Create fresh database for each test, rollback after."""
    # 1. 创建内存数据库
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)  # 创建表
    Session = sessionmaker(bind=engine)

    # 2. 创建连接 + 开始事务
    connection = engine.connect()
    transaction = connection.begin()

    # 3. 创建 session（绑定到事务连接）
    session = Session(bind=connection)

    yield session

    # 3. 回滚 + 清理
    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()


class TestUserModel:
    """Test User CRUD operations."""

    def test_create_user(self, db_session) -> None:
        """Test creating a new user."""
        user = User(username="John", email="john@test.com")
        db_session.add(user)
        db_session.flush()  # 生成 ID，但不提交
        assert user.id is not None
        assert user.username == "John"

    def test_user_isolation(self, db_session) -> None:
        """Test each test gets clean database."""
        # 上一个测试的数据不应该存在
        count = db_session.query(User).count()
        assert count == 0  # 因为是新数据库

    def test_query_user(self, db_session) -> None:
        """Test querying users."""
        user1 = User(username="alice", email="alice@test.com")
        user2 = User(username="bob", email="bob@test.com")
        db_session.add_all([user1, user2])
        db_session.flush()

        users = db_session.query(User).all()
        assert len(users) == 2
        assert users[0].username == "alice"
