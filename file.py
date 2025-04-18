from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
import ast
import json

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    user =  db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(detail="User not found", status_code=status.HTTP_404_NOT_FOUND)
    return user

def get_users(db:Session, skip: int = 0, limit: int = 10):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

def update_user(db: Session, user_id: int, user: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(detail="User not found", status_code=status.HTTP_404_NOT_FOUND)
    for var, value in vars(user).items():
        if value is not None:
            setattr(db_user, var, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(detail="User not found", status_code=status.HTTP_404_NOT_FOUND)
    else:
        db.delete(db_user)
        db.commit()
        return db_user
    
# ----------------------------------------------------------------------------------------------

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product: schemas.ProductUpdate):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(detail="Product not found", status_code=status.HTTP_404_NOT_FOUND)
    for var, value in vars(product).items():
        if value is not None:
            setattr(db_product, var, value)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_product(db: Session, product_id: int):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(detail="Product not found", status_code=status.HTTP_404_NOT_FOUND)
    return db_product

def get_products(db: Session, skip: int, limit: int, filter_text: str):
    if filter_text:
        filter_text = filter_text if len(filter_text.strip()) > 0 else None
        products = db.query(models.Product).filter(models.Product.name.ilike(f'%{filter_text}%')).offset(skip).limit(limit).all()
        return products
    else:
        products = db.query(models.Product).offset(skip).limit(limit).all()
        return products

def delete_product(db: Session, product_id: int):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(detail="Product not found", status_code=status.HTTP_404_NOT_FOUND)
    elif db.query(models.CartItem).filter(models.CartItem.product_id == product_id).first():
        raise HTTPException(detail="Product exists in user carts", status_code=status.HTTP_400_BAD_REQUEST)
    else:
        db.delete(product)
        db.commit()
        return product

# ----------------------------------------------------------------------------------------------

def create_cart_item(db: Session, cartitem: schemas.CartItemCreate):
    user = db.query(models.User).filter(models.User.id == cartitem.user_id).first()
    product = db.query(models.Product).filter(models.Product.id == cartitem.product_id).first()
    
    if cartitem.quantity <= 0:
        raise HTTPException(detail="Cart Item quantity cannot be 0", status_code=status.HTTP_400_BAD_REQUEST)
    elif not user:
        raise HTTPException(detail="User not found", status_code=status.HTTP_404_NOT_FOUND)
    elif not product:
        raise HTTPException(detail="Product not found", status_code=status.HTTP_404_NOT_FOUND)
    else:
        db_cartitem = models.CartItem(**cartitem.model_dump())
        db.add(db_cartitem)
        db.commit()
        db.refresh(db_cartitem)
        return db_cartitem
    
def get_cart_items(db: Session, user_id: int, skip: int, limit: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(detail="User not found", status_code=status.HTTP_404_NOT_FOUND)
    else:
        cartitems = db.query(models.CartItem).filter(models.CartItem.user_id == user_id).offset(skip).limit(limit).all()
        return cartitems
    
def get_cart_item(db: Session, user_id: int, product_id: int):
    cartitem = db.query(models.CartItem).filter(models.CartItem.user_id == user_id, models.CartItem.product_id == product_id).first()
    if not cartitem:
        raise HTTPException(detail="Cart item not found", status_code=status.HTTP_404_NOT_FOUND)
    else:
        return cartitem

def get_cart(db: Session, user_id: int):
    cart = db.query(models.CartItem.quantity, models.Product.name, models.Product.price, (models.Product.price * models.CartItem.quantity), models.Product.id).join(models.CartItem, models.Product.id == models.CartItem.product_id).filter(models.CartItem.user_id == user_id).all()
    total_cart_value = sum([i[3] for i in cart])
    return JSONResponse({"cart": f'{cart}', "total_cart_value": f'{total_cart_value}'})
    
def update_cart_item(db: Session, cartitem_id: int, quantity: int):
    cartitem = db.query(models.CartItem).filter(models.CartItem.id == cartitem_id).first()
    if not cartitem:
        raise HTTPException(detail="Cart item not found", status_code=status.HTTP_404_NOT_FOUND)
    else:
        cartitem.quantity = quantity
        db.commit()
        db.refresh(cartitem)
        return cartitem
    
def delete_cart_item(db: Session, cartitem_id: int):
    cartitem = db.query(models.CartItem).filter(models.CartItem.id == cartitem_id).first()
    if not cartitem:
        raise HTTPException(detail="Cart item not found", status_code=status.HTTP_404_NOT_FOUND)
    else:
        db.delete(cartitem)
        db.commit()
        return cartitem
    
# ----------------------------------------------------------------------------------------------

def create_order_item(db: Session, order_id: int, product_id, quantity: int, price: float):
    db_orderitem = models.OrderItem(
        order_id = order_id,
        product_id = product_id,
        quantity = quantity,
        price = price
    )
    db.add(db_orderitem)
    db.commit()
    db.refresh(db_orderitem)
    return db_orderitem
    

def create_order(db: Session, user_id: int):
    response = get_cart(db, user_id)
    response_str = response.body.decode()
    response_dict = json.loads(response_str)
    print(response_dict)
    
    total_cart_value = response_dict["total_cart_value"]
    
    cart = ast.literal_eval(response_dict["cart"])
    cart_lists = [list(i) for i in cart]
    
    db_order = models.Order(
        user_id = user_id,
        total_amount = total_cart_value
    )

    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    order_item_list = []
    for cart_list in cart_lists:
        db_cart_order_item = create_order_item(db, db_order.id, cart_list[4], cart_list[0], cart_list[2])
        order_item_list.append(db_cart_order_item)
    
    cart_items = db.query(models.CartItem).filter(models.CartItem.user_id == user_id).all()
    for cart_item in cart_items:
        db.delete(cart_item)
        db.commit()
    
    print(db_order.id, db_order.user_id, order_item_list)
    return {"order_id": db_order.id}


def read_order(db: Session, user_id: int, order_id: int):
    order_details = (db.query(
        models.Order.id.label('order_id'),
        models.Order.user_id,
        models.Order.total_amount,
        models.Order.created_at,
        models.OrderItem.id.label('orderitem_id'),
        models.OrderItem.order_id,        
        models.OrderItem.quantity,
        models.OrderItem.price,
        (models.OrderItem.price * models.OrderItem.quantity).label("subtotal"),
        models.Product.name,
    ).join(models.OrderItem, models.Order.id == models.OrderItem.order_id)
    .join(models.Product, models.Product.id == models.OrderItem.product_id)
    .filter(models.Order.user_id == user_id, models.Order.id == order_id).all())
    
    
    order_dict = {}
    for row in order_details:
        order_id = row[0]
        if order_id not in order_dict:
            order_dict["order"] = {
                "order_id": order_id,
                "user_id": row[1],
                "total_amount": row[2],
                "created_at": row[3].isoformat(),
                "order_items": []
            }
            
    for row in order_details:
            order_dict["order"]["order_items"].append({
                "orderitem_id": row[4],
                "quantity": row[6],
                "price": row[7],
                "subtotal": row[8],
                "product_name": row[9]
            })
    
    print(order_dict)
    return order_dict