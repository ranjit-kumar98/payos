from fastapi import APIRouter

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"]
)

@router.post("/razorpay")
async def razorpay_webhook():
    return {
        "message": "Webhook received"
    }