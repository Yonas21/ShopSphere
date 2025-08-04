"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database.sql_database import get_db
from models.user import Base, User, UserRole
from models.item import Item, Purchase
from crud.user import get_password_hash


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Create test engine with SQLite
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def db_session(test_db):
    """Create a database session for direct database operations."""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_admin_user(db_session):
    """Create a test admin user."""
    admin_user = User(
        email="admin@test.com",
        username="admin",
        hashed_password=get_password_hash("adminpass"),
        role=UserRole.ADMIN
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def test_customer_user(db_session):
    """Create a test customer user."""
    customer_user = User(
        email="customer@test.com",
        username="customer",
        hashed_password=get_password_hash("customerpass"),
        role=UserRole.CUSTOMER
    )
    db_session.add(customer_user)
    db_session.commit()
    db_session.refresh(customer_user)
    return customer_user


@pytest.fixture
def test_admin_token(client, test_admin_user):
    """Get authentication token for admin user."""
    response = client.post(
        "/api/users/login",
        data={"username": "admin", "password": "adminpass"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def test_customer_token(client, test_customer_user):
    """Get authentication token for customer user."""
    response = client.post(
        "/api/users/login",
        data={"username": "customer", "password": "customerpass"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(test_admin_token):
    """Get authorization headers for admin user."""
    return {"Authorization": f"Bearer {test_admin_token}"}


@pytest.fixture
def customer_headers(test_customer_token):
    """Get authorization headers for customer user."""
    return {"Authorization": f"Bearer {test_customer_token}"}


@pytest.fixture
def test_item(db_session, test_admin_user):
    """Create a test item."""
    item = Item(
        name="Test Product",
        description="A test product for testing",
        price=99.99,
        category="Electronics",
        stock_quantity=10,
        image_url="https://example.com/image.jpg",
        created_by=test_admin_user.id
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def test_purchase(db_session, test_item, test_customer_user):
    """Create a test purchase."""
    purchase = Purchase(
        item_id=test_item.id,
        customer_id=test_customer_user.id,
        quantity=2,
        total_price=test_item.price * 2
    )
    db_session.add(purchase)
    db_session.commit()
    db_session.refresh(purchase)
    return purchase


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {
        "name": "Sample Product",
        "description": "A sample product for testing",
        "price": 29.99,
        "category": "Books",
        "stock_quantity": 5,
        "image_url": "https://example.com/sample.jpg"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "newuserpass"
    }


# Test data generators
def create_test_users(db_session, count=5):
    """Create multiple test users."""
    users = []
    for i in range(count):
        user = User(
            email=f"user{i}@test.com",
            username=f"user{i}",
            hashed_password=get_password_hash(f"password{i}"),
            role=UserRole.CUSTOMER if i % 2 == 0 else UserRole.ADMIN
        )
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    for user in users:
        db_session.refresh(user)
    return users


def create_test_items(db_session, admin_user, count=5):
    """Create multiple test items."""
    items = []
    categories = ["Electronics", "Books", "Clothing", "Home", "Sports"]
    
    for i in range(count):
        item = Item(
            name=f"Test Product {i}",
            description=f"Description for test product {i}",
            price=round(10.0 + (i * 5.5), 2),
            category=categories[i % len(categories)],
            stock_quantity=10 + i,
            created_by=admin_user.id
        )
        db_session.add(item)
        items.append(item)
    
    db_session.commit()
    for item in items:
        db_session.refresh(item)
    return items


def create_test_purchases(db_session, items, customer_user, count=3):
    """Create multiple test purchases."""
    purchases = []
    
    for i in range(min(count, len(items))):
        item = items[i]
        quantity = i + 1
        purchase = Purchase(
            item_id=item.id,
            customer_id=customer_user.id,
            quantity=quantity,
            total_price=item.price * quantity
        )
        db_session.add(purchase)
        purchases.append(purchase)
    
    db_session.commit()
    for purchase in purchases:
        db_session.refresh(purchase)
    return purchases