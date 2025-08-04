from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.item import OrderStatus

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    stock_quantity: int = Field(default=0, ge=0)
    image_url: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    stock_quantity: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ItemResponse(ItemBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ItemDetailResponse(ItemResponse):
    creator_username: Optional[str] = None

class PurchaseBase(BaseModel):
    item_id: int
    quantity: int = Field(..., gt=0)

class PurchaseCreate(PurchaseBase):
    pass

class PurchaseResponse(PurchaseBase):
    id: int
    customer_id: int
    total_price: float
    status: OrderStatus
    status_updated_at: datetime
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    purchase_date: datetime
    item_name: Optional[str] = None
    customer_username: Optional[str] = None

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    tracking_number: Optional[str] = None
    notes: Optional[str] = None