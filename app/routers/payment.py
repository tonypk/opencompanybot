from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.ccpayment import CCPaymentService

router = APIRouter()
cc_service = CCPaymentService()


class CreatePaymentRequest(BaseModel):
    amount: float
    currency: str = "USDT"
    network: str = "ERC20"
    order_id: str
    description: str | None = None


class PaymentStatusResponse(BaseModel):
    order_id: str
    amount: float
    currency: str
    network: str
    status: str
    address: str
    tx_hash: str | None
    created_at: str


@router.post("/create")
async def create_payment(request: CreatePaymentRequest):
    try:
        result = await cc_service.create_payment(
            amount=request.amount,
            currency=request.currency,
            network=request.network,
            order_id=request.order_id,
            description=request.description,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def get_payment_status(order_id: str):
    try:
        payment_status = await cc_service.get_payment_status(order_id)
        return payment_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/webhook")
async def payment_webhook(data: dict):
    try:
        await cc_service.handle_webhook(data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
