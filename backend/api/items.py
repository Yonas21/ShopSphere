from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database.sql_database import get_db
from schemas.item import ItemCreate, ItemUpdate, ItemResponse, ItemDetailResponse, PurchaseCreate, PurchaseResponse, OrderStatusUpdate
from crud import item as crud_item
from auth import get_admin_user, get_current_active_user, get_admin_or_customer_user
from models.user import User
from typing import List, Optional

router = APIRouter(prefix="/items", tags=["items"])

# Admin-only endpoints
@router.post("/", response_model=ItemResponse)
def create_item(
    item: ItemCreate, 
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    return crud_item.create_item(db=db, item=item, creator_id=current_user.id)

@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_update: ItemUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    db_item = crud_item.update_item(db=db, item_id=item_id, item_update=item_update)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@router.delete("/{item_id}", response_model=ItemResponse)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    db_item = crud_item.delete_item(db=db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

# Public endpoints (available to everyone, no authentication required)
@router.get("/", response_model=List[ItemDetailResponse])
def get_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock_only: bool = Query(True),
    sort_by: Optional[str] = Query("created_at", regex="^(name|price|created_at|stock_quantity)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    items = crud_item.get_items(
        db=db, 
        skip=skip, 
        limit=limit, 
        category=category, 
        search=search,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Add creator username to response
    response_items = []
    for item in items:
        item_dict = ItemDetailResponse.from_orm(item).dict()
        item_dict["creator_username"] = item.creator.username if item.creator else None
        response_items.append(ItemDetailResponse(**item_dict))
    
    return response_items

@router.get("/{item_id}", response_model=ItemDetailResponse)
def get_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    db_item = crud_item.get_item(db=db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Add creator username to response
    item_dict = ItemDetailResponse.from_orm(db_item).dict()
    item_dict["creator_username"] = db_item.creator.username if db_item.creator else None
    return ItemDetailResponse(**item_dict)

@router.get("/categories/list")
def get_categories(
    db: Session = Depends(get_db)
):
    categories = crud_item.get_categories(db=db)
    return {"categories": [cat[0] for cat in categories]}

# Customer purchase endpoints
@router.post("/purchase", response_model=PurchaseResponse)
def purchase_item(
    purchase: PurchaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        db_purchase = crud_item.create_purchase(db=db, purchase=purchase, customer_id=current_user.id)
        if not db_purchase:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Add additional info to response
        purchase_dict = PurchaseResponse.from_orm(db_purchase).dict()
        purchase_dict["item_name"] = db_purchase.item.name if db_purchase.item else None
        purchase_dict["customer_username"] = current_user.username
        return PurchaseResponse(**purchase_dict)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/purchases/my", response_model=List[PurchaseResponse])
def get_my_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    purchases = crud_item.get_user_purchases(db=db, user_id=current_user.id, skip=skip, limit=limit)
    
    # Add additional info to response
    response_purchases = []
    for purchase in purchases:
        purchase_dict = PurchaseResponse.from_orm(purchase).dict()
        purchase_dict["item_name"] = purchase.item.name if purchase.item else None
        purchase_dict["customer_username"] = current_user.username
        response_purchases.append(PurchaseResponse(**purchase_dict))
    
    return response_purchases

# Admin-only purchase management
@router.get("/purchases/all", response_model=List[PurchaseResponse])
def get_all_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    purchases = crud_item.get_all_purchases(db=db, skip=skip, limit=limit)
    
    # Add additional info to response
    response_purchases = []
    for purchase in purchases:
        purchase_dict = PurchaseResponse.from_orm(purchase).dict()
        purchase_dict["item_name"] = purchase.item.name if purchase.item else None
        purchase_dict["customer_username"] = purchase.customer.username if purchase.customer else None
        response_purchases.append(PurchaseResponse(**purchase_dict))
    
    return response_purchases

# Admin-only order status management
@router.put("/purchases/{purchase_id}/status", response_model=PurchaseResponse)
def update_order_status(
    purchase_id: int,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update order status (admin only)"""
    try:
        updated_purchase = crud_item.update_order_status(
            db=db, 
            purchase_id=purchase_id, 
            status_update=status_update
        )
        if not updated_purchase:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Add additional info to response
        purchase_dict = PurchaseResponse.from_orm(updated_purchase).dict()
        purchase_dict["item_name"] = updated_purchase.item.name if updated_purchase.item else None
        purchase_dict["customer_username"] = updated_purchase.customer.username if updated_purchase.customer else None
        return PurchaseResponse(**purchase_dict)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/orders/stats")
def get_order_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get order statistics (admin only)"""
    return crud_item.get_order_stats(db=db)