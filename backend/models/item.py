from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Enum, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.sql_database import Base
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped" 
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Item(Base):
    __tablename__ = "items"

    # Columns
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)  # Added length for better performance
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, index=True)  # Index for price range queries
    category = Column(String(100), nullable=False, index=True)  # Added length
    stock_quantity = Column(Integer, default=0, nullable=False, index=True)  # Index for stock queries
    image_url = Column(String(500), nullable=True)  # Added length
    is_active = Column(Boolean, default=True, index=True)  # Index for active item queries
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # Index for date queries
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="created_items")
    purchases = relationship("Purchase", back_populates="item")
    cart_items = relationship("CartItem", back_populates="item")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_items_category_active', 'category', 'is_active'),
        Index('idx_items_price_category', 'price', 'category'),
        Index('idx_items_stock_active', 'stock_quantity', 'is_active'),
        Index('idx_items_created_active', 'created_at', 'is_active'),
        Index('idx_items_name_search', 'name'),  # For text search optimization
    )

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="cart_items")
    item = relationship("Item", back_populates="cart_items")

    # Ensure unique cart items per user
    __table_args__ = (
        UniqueConstraint('user_id', 'item_id', name='unique_user_item_cart'),
        Index('idx_cart_user_added', 'user_id', 'added_at'),
    )

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    status_updated_at = Column(DateTime(timezone=True), server_default=func.now())
    tracking_number = Column(String(100), nullable=True, index=True)  # For tracking lookups
    notes = Column(Text, nullable=True)
    purchase_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    customer = relationship("User", back_populates="purchases")
    item = relationship("Item", back_populates="purchases")
    payment = relationship("Payment", back_populates="purchase", uselist=False)

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_purchases_customer_date', 'customer_id', 'purchase_date'),
        Index('idx_purchases_status_date', 'status', 'purchase_date'),
        Index('idx_purchases_item_date', 'item_id', 'purchase_date'),
        Index('idx_purchases_customer_status', 'customer_id', 'status'),
    )