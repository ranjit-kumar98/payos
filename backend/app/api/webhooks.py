from fastapi import APIRouter, Request, Header, HTTPException
from razorpay.utility.utility import Utility
from app.core.config import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(...)
):
    # Raw body exactly as Razorpay sent it
    body = await request.body()

    utility = Utility()

    try:
        utility.verify_webhook_signature(
            body.decode(),
            x_razorpay_signature,
            settings.RAZORPAY_WEBHOOK_SECRET
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )

    print("Webhook signature verified successfully")

    return {
        "message": "Webhook received"
    }