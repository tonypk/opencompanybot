import os
import httpx
import uuid
from datetime import datetime


class CCPaymentService:
    API_URL = "https://api.ccpayment.com"
    API_KEY = os.getenv("CCPAYMENT_API_KEY", "")
    MERCHANT_ID = os.getenv("CCPAYMENT_MERCHANT_ID", "")

    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def create_payment(
        self,
        amount: float,
        currency: str,
        network: str,
        order_id: str,
        description: str | None = None,
    ) -> dict:
        payload = {
            "merchant_id": self.MERCHANT_ID,
            "order_id": order_id,
            "amount": str(amount),
            "currency": currency,
            "network": network,
            "description": description or "OpenCompanyBot Payment",
            "callback_url": os.getenv("PAYMENT_WEBHOOK_URL", ""),
        }

        response = await self.client.post(
            f"{self.API_URL}/v1/payment/create",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "network": network,
            "status": "pending",
            "address": data.get("pay_address", ""),
            "tx_hash": None,
            "created_at": datetime.utcnow().isoformat(),
        }

    async def get_payment_status(self, order_id: str) -> dict:
        response = await self.client.get(
            f"{self.API_URL}/v1/payment/status",
            params={"order_id": order_id},
        )
        response.raise_for_status()
        data = response.json()

        return {
            "order_id": order_id,
            "amount": float(data.get("amount", 0)),
            "currency": data.get("currency", "USDT"),
            "network": data.get("network", "ERC20"),
            "status": data.get("status", "pending"),
            "address": data.get("pay_address", ""),
            "tx_hash": data.get("tx_hash"),
            "created_at": data.get("create_time", ""),
        }

    async def handle_webhook(self, data: dict) -> dict:
        order_id = data.get("order_id")
        status = data.get("status")

        if status == "success":
            return {"order_id": order_id, "status": "paid"}
        return {"order_id": order_id, "status": status}

    async def close(self):
        await self.client.aclose()
