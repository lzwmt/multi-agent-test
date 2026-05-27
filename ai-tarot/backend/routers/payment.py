"""
Payment router - handles order creation and payment callbacks.
Stub implementation for now.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Order, User

router = APIRouter(prefix="/api/payment", tags=["payment"])


class CreateOrderRequest(BaseModel):
    product_type: str  # "single", "monthly", "deep"
    amount: int  # in fen (分)


class OrderResponse(BaseModel):
    order_no: str
    amount: int
    product_type: str
    status: str
    pay_url: str = ""


# Product pricing (in fen)
PRODUCTS = {
    "single": {"amount": 990, "name": "单次占卜", "desc": "一次完整牌阵解读"},
    "monthly": {"amount": 2990, "name": "月度会员", "desc": "每月30次占卜+专属牌阵"},
    "deep": {"amount": 3990, "name": "深度解读", "desc": "年度运势/感情全盘分析"},
}


@router.get("/products")
async def list_products():
    """List available products and pricing."""
    return [
        {"id": k, "name": v["name"], "amount": v["amount"], "desc": v["desc"]}
        for k, v in PRODUCTS.items()
    ]


@router.post("/create-order", response_model=OrderResponse)
async def create_order(
    req: CreateOrderRequest,
    authorization: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
):
    """Create a payment order."""
    if req.product_type not in PRODUCTS:
        raise HTTPException(status_code=400, detail="未知产品类型")

    product = PRODUCTS[req.product_type]
    order_no = f"TAROT{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

    order = Order(
        user_id=1,  # TODO: get from auth
        order_no=order_no,
        amount=product["amount"],
        product_type=req.product_type,
        status="pending",
    )
    db.add(order)
    await db.flush()

    # TODO: Generate WeChat/Alipay payment URL
    return OrderResponse(
        order_no=order_no,
        amount=product["amount"],
        product_type=req.product_type,
        status="pending",
        pay_url="",  # Will be filled after payment integration
    )


@router.post("/callback")
async def payment_callback(db: AsyncSession = Depends(get_db)):
    """Payment callback from WeChat/Alipay. Stub for now."""
    # TODO: Implement actual payment callback verification
    return {"status": "ok"}


@router.get("/orders")
async def list_orders(
    limit: int = 20,
    authorization: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
):
    """List user's orders."""
    stmt = (
        select(Order)
        .where(Order.user_id == 1)  # TODO: get from auth
        .order_by(desc(Order.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return {
        "items": [
            {
                "order_no": o.order_no,
                "amount": o.amount,
                "product_type": o.product_type,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            }
            for o in orders
        ]
    }
