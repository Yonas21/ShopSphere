from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.sql_database import Base
import enum

class NotificationType(str, enum.Enum):
    ORDER_CREATED = "order_created"
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_PROCESSING = "order_processing"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    REFUND_PROCESSED = "refund_processed"
    LOW_STOCK_ALERT = "low_stock_alert"
    NEW_ORDER_ADMIN = "new_order_admin"
    SYSTEM_MAINTENANCE = "system_maintenance"
    ACCOUNT_CREATED = "account_created"
    PASSWORD_CHANGED = "password_changed"

class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    IN_APP = "in_app" 
    SMS = "sms"  # For future implementation
    PUSH = "push"  # For future implementation

class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Recipient information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification content
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Notification settings
    channel = Column(Enum(NotificationChannel), nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False)
    
    # Status tracking
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    
    # Related entities (optional)
    related_id = Column(Integer, nullable=True)  # Could be order_id, payment_id, etc.
    related_type = Column(String(50), nullable=True)  # "order", "payment", "item", etc.
    
    # Email specific fields
    email_to = Column(String(255), nullable=True)
    email_subject = Column(String(255), nullable=True)
    email_html_content = Column(Text, nullable=True)
    email_text_content = Column(Text, nullable=True)
    
    # Metadata and customization
    notification_metadata = Column(JSON, nullable=True)
    action_url = Column(String(500), nullable=True)  # URL for action buttons
    action_text = Column(String(100), nullable=True)  # Text for action button
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For temporary notifications
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Relationships
    user = relationship("User", back_populates="notifications")

class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Template identification
    type = Column(Enum(NotificationType), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template content
    title_template = Column(String(255), nullable=False)
    message_template = Column(Text, nullable=False)
    
    # Email specific templates
    email_subject_template = Column(String(255), nullable=True)
    email_html_template = Column(Text, nullable=True)
    email_text_template = Column(Text, nullable=True)
    
    # Template settings
    is_active = Column(Boolean, default=True)
    channels = Column(JSON, nullable=False)  # List of supported channels
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Auto-send settings
    auto_send = Column(Boolean, default=True)
    delay_minutes = Column(Integer, default=0)  # Delay before sending
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    
    # User preferences
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    
    # Timing preferences
    quiet_hours_start = Column(String(5), nullable=True)  # Format: "22:00"
    quiet_hours_end = Column(String(5), nullable=True)    # Format: "08:00"
    timezone = Column(String(50), default="UTC")
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")

    # Unique constraint to prevent duplicate preferences
    __table_args__ = (
        {"schema": None},
    )