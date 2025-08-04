from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CartItemBase(BaseModel):
    item_id: int
    quantity: int = 1

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(CartItemBase):
    id: int
    user_id: int
    added_at: datetime
    
    class Config:
        from_attributes = True

class CartItemDetail(CartItemResponse):
    item_name: str
    item_price: float
    item_image_url: Optional[str] = None
    item_stock_quantity: int
    subtotal: float

class CartSummary(BaseModel):
    items: list[CartItemDetail]
    total_items: int
    total_price: float

class CheckoutRequest(BaseModel):
    pass  # For future expansion (shipping address, payment method, etc.)