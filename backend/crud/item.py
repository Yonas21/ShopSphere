from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, asc, desc
from models.item import Item, Purchase
from models.user import User
from schemas.item import ItemCreate, ItemUpdate, PurchaseCreate, OrderStatusUpdate
from models.item import OrderStatus
from typing import List, Optional
import hashlib
import json
from utils.cache import cache_get, cache_set, cache_delete, cache_invalidator
import logging

logger = logging.getLogger("app.crud.item")

def create_item(db: Session, item: ItemCreate, creator_id: int):
    db_item = Item(
        name=item.name,
        description=item.description,
        price=item.price,
        category=item.category,
        stock_quantity=item.stock_quantity,
        image_url=item.image_url,
        created_by=creator_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Invalidate relevant caches
    cache_invalidator.invalidate_item_cache(db_item.id)
    cache_invalidator.invalidate_category_cache(item.category)
    
    logger.info(f"Created item {db_item.id}: {db_item.name}")
    return db_item

def get_item(db: Session, item_id: int):
    # Try to get from cache first
    cache_key = f"item:{item_id}"
    cached_item = cache_get(cache_key)
    
    if cached_item is not None:
        logger.debug(f"Item {item_id} retrieved from cache")
        return cached_item
    
    # Get from database
    db_item = db.query(Item).options(joinedload(Item.creator)).filter(Item.id == item_id).first()
    
    if db_item:
        # Cache for 10 minutes
        cache_set(cache_key, db_item, ttl=600)
        logger.debug(f"Item {item_id} cached from database")
    
    return db_item

def get_items(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    category: Optional[str] = None, 
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = True,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    active_only: bool = True
):
    # Generate cache key from parameters
    params = {
        "skip": skip,
        "limit": limit,
        "category": category,
        "search": search,
        "min_price": min_price,
        "max_price": max_price,
        "in_stock_only": in_stock_only,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "active_only": active_only
    }
    
    # Create hash of parameters for cache key
    params_str = json.dumps(params, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()
    cache_key = f"items:list:{params_hash}"
    
    # Try to get from cache (shorter TTL for dynamic data)
    cached_items = cache_get(cache_key)
    if cached_items is not None:
        logger.debug("Items list retrieved from cache")
        return cached_items
    
    # Build query
    query = db.query(Item).options(joinedload(Item.creator))
    
    if active_only:
        query = query.filter(Item.is_active == True)
    
    if in_stock_only:
        query = query.filter(Item.stock_quantity > 0)
    
    if category:
        query = query.filter(Item.category == category)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Item.name.ilike(search_term),
                Item.description.ilike(search_term),
                Item.category.ilike(search_term)
            )
        )
    
    if min_price is not None:
        query = query.filter(Item.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Item.price <= max_price)
    
    # Apply sorting
    sort_column = getattr(Item, sort_by, Item.created_at)
    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
    
    items = query.offset(skip).limit(limit).all()
    
    # Cache results for 5 minutes (shorter for dynamic lists)
    cache_set(cache_key, items, ttl=300)
    logger.debug(f"Items list cached ({len(items)} items)")
    
    return items

def update_item(db: Session, item_id: int, item_update: ItemUpdate):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        return None
    
    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item:
        db_item.is_active = False
        db.commit()
        db.refresh(db_item)
        return db_item
    return None

def get_categories(db: Session):
    return db.query(Item.category).filter(Item.is_active == True).distinct().all()

def create_purchase(db: Session, purchase: PurchaseCreate, customer_id: int):
    # Get the item and check stock
    item = db.query(Item).filter(Item.id == purchase.item_id).first()
    if not item:
        return None
    
    if item.stock_quantity < purchase.quantity:
        raise ValueError("Insufficient stock")
    
    # Calculate total price
    total_price = item.price * purchase.quantity
    
    # Create purchase
    db_purchase = Purchase(
        customer_id=customer_id,
        item_id=purchase.item_id,
        quantity=purchase.quantity,
        total_price=total_price
    )
    
    # Update item stock
    item.stock_quantity -= purchase.quantity
    
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

def get_purchase(db: Session, purchase_id: int):
    """Get a purchase by ID"""
    return db.query(Purchase).filter(Purchase.id == purchase_id).first()

def get_user_purchases(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (db.query(Purchase)
            .options(joinedload(Purchase.item), joinedload(Purchase.customer))
            .filter(Purchase.customer_id == user_id)
            .offset(skip)
            .limit(limit)
            .all())

def get_all_purchases(db: Session, skip: int = 0, limit: int = 100):
    return (db.query(Purchase)
            .options(joinedload(Purchase.item), joinedload(Purchase.customer))
            .order_by(desc(Purchase.purchase_date))
            .offset(skip)
            .limit(limit)
            .all())

def update_order_status(db: Session, purchase_id: int, status_update: OrderStatusUpdate):
    """Update order status"""
    from sqlalchemy import func
    
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        return None
    
    # Update status and timestamp
    purchase.status = status_update.status
    purchase.status_updated_at = func.now()
    
    if status_update.tracking_number is not None:
        purchase.tracking_number = status_update.tracking_number
    
    if status_update.notes is not None:
        purchase.notes = status_update.notes
    
    db.commit()
    db.refresh(purchase)
    return purchase

def get_order_stats(db: Session):
    """Get order statistics for admin dashboard"""
    from sqlalchemy import func, case
    
    # Get total counts by status
    status_counts = (
        db.query(
            Purchase.status,
            func.count(Purchase.id).label('count')
        )
        .group_by(Purchase.status)
        .all()
    )
    
    # Get total revenue
    total_revenue = db.query(func.sum(Purchase.total_price)).scalar() or 0
    
    # Get total orders
    total_orders = db.query(func.count(Purchase.id)).scalar() or 0
    
    # Recent orders (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_orders = (
        db.query(func.count(Purchase.id))
        .filter(Purchase.purchase_date >= thirty_days_ago)
        .scalar() or 0
    )
    
    # Format status counts
    status_dict = {status.value: 0 for status in OrderStatus}
    for status, count in status_counts:
        status_dict[status.value] = count
    
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "recent_orders": recent_orders,
        "status_counts": status_dict,
        "orders_by_status": [
            {"status": status, "count": count} 
            for status, count in status_counts
        ]
    }