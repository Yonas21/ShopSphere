from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.sql_database import get_db
from schemas.cart import CartItemCreate, CartItemUpdate, CartItemResponse, CartSummary, CheckoutRequest
from schemas.item import PurchaseResponse
from crud import cart as crud_cart
from auth import get_current_active_user
from models.user import User
from typing import List

router = APIRouter(prefix="/cart", tags=["cart"])

@router.post("/add", response_model=CartItemResponse)
def add_to_cart(
    cart_item: CartItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add item to cart or update quantity if already exists"""
    try:
        db_cart_item = crud_cart.add_to_cart(db=db, user_id=current_user.id, cart_item=cart_item)
        return db_cart_item
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=CartSummary)
def get_cart(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's cart with item details and totals"""
    return crud_cart.get_cart_summary(db=db, user_id=current_user.id)

@router.put("/{cart_item_id}", response_model=CartItemResponse)
def update_cart_item(
    cart_item_id: int,
    cart_update: CartItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update quantity of item in cart"""
    if cart_update.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
    
    db_cart_item = crud_cart.update_cart_item(
        db=db, user_id=current_user.id, cart_item_id=cart_item_id, cart_update=cart_update
    )
    if not db_cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return db_cart_item

@router.delete("/{cart_item_id}")
def remove_from_cart(
    cart_item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    success = crud_cart.remove_from_cart(db=db, user_id=current_user.id, cart_item_id=cart_item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Item removed from cart"}

@router.delete("/")
def clear_cart(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clear all items from cart"""
    crud_cart.clear_cart(db=db, user_id=current_user.id)
    return {"message": "Cart cleared"}

@router.post("/checkout", response_model=List[PurchaseResponse])
def checkout(
    checkout_request: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Checkout cart - convert cart items to purchases and clear cart"""
    try:
        purchases = crud_cart.checkout_cart(db=db, user_id=current_user.id)
        if not purchases:
            raise HTTPException(status_code=400, detail="Cart is empty or items unavailable")
        
        # Convert to response format
        response_purchases = []
        for purchase in purchases:
            purchase_dict = PurchaseResponse.from_orm(purchase).dict()
            purchase_dict["item_name"] = purchase.item.name if purchase.item else None
            purchase_dict["customer_username"] = current_user.username
            response_purchases.append(PurchaseResponse(**purchase_dict))
        
        return response_purchases
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))