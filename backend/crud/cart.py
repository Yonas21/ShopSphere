from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.item import CartItem, Item, Purchase
from schemas.cart import CartItemCreate, CartItemUpdate, CartItemDetail, CartSummary
from typing import List, Optional

def add_to_cart(db: Session, user_id: int, cart_item: CartItemCreate) -> CartItem:
    # Check if item already exists in cart
    existing_cart_item = db.query(CartItem).filter(
        and_(CartItem.user_id == user_id, CartItem.item_id == cart_item.item_id)
    ).first()
    
    if existing_cart_item:
        # Update quantity if item already in cart
        existing_cart_item.quantity += cart_item.quantity
        db.commit()
        db.refresh(existing_cart_item)
        return existing_cart_item
    else:
        # Create new cart item
        db_cart_item = CartItem(
            user_id=user_id,
            item_id=cart_item.item_id,
            quantity=cart_item.quantity
        )
        db.add(db_cart_item)
        db.commit()
        db.refresh(db_cart_item)
        return db_cart_item

def get_cart_items(db: Session, user_id: int) -> List[CartItem]:
    return db.query(CartItem).filter(CartItem.user_id == user_id).all()

def get_cart_summary(db: Session, user_id: int) -> CartSummary:
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    
    cart_details = []
    total_price = 0.0
    total_items = 0
    
    for cart_item in cart_items:
        item = cart_item.item
        if item and item.is_active:
            subtotal = item.price * cart_item.quantity
            cart_detail = CartItemDetail(
                id=cart_item.id,
                user_id=cart_item.user_id,
                item_id=cart_item.item_id,
                quantity=cart_item.quantity,
                added_at=cart_item.added_at,
                item_name=item.name,
                item_price=item.price,
                item_image_url=item.image_url,
                item_stock_quantity=item.stock_quantity,
                subtotal=subtotal
            )
            cart_details.append(cart_detail)
            total_price += subtotal
            total_items += cart_item.quantity
    
    return CartSummary(
        items=cart_details,
        total_items=total_items,
        total_price=total_price
    )

def update_cart_item(db: Session, user_id: int, cart_item_id: int, cart_update: CartItemUpdate) -> Optional[CartItem]:
    cart_item = db.query(CartItem).filter(
        and_(CartItem.id == cart_item_id, CartItem.user_id == user_id)
    ).first()
    
    if cart_item:
        cart_item.quantity = cart_update.quantity
        db.commit()
        db.refresh(cart_item)
        return cart_item
    return None

def remove_from_cart(db: Session, user_id: int, cart_item_id: int) -> bool:
    cart_item = db.query(CartItem).filter(
        and_(CartItem.id == cart_item_id, CartItem.user_id == user_id)
    ).first()
    
    if cart_item:
        db.delete(cart_item)
        db.commit()
        return True
    return False

def clear_cart(db: Session, user_id: int) -> bool:
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    for cart_item in cart_items:
        db.delete(cart_item)
    db.commit()
    return True

def checkout_cart(db: Session, user_id: int) -> List[Purchase]:
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    purchases = []
    
    for cart_item in cart_items:
        item = cart_item.item
        if item and item.is_active and item.stock_quantity >= cart_item.quantity:
            # Create purchase
            purchase = Purchase(
                customer_id=user_id,
                item_id=cart_item.item_id,
                quantity=cart_item.quantity,
                total_price=item.price * cart_item.quantity
            )
            db.add(purchase)
            
            # Update stock
            item.stock_quantity -= cart_item.quantity
            
            purchases.append(purchase)
    
    # Clear cart after successful checkout
    if purchases:
        clear_cart(db, user_id)
        db.commit()
        
        # Refresh all purchases
        for purchase in purchases:
            db.refresh(purchase)
    
    return purchases