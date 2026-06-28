from typing import Optional, Tuple
from app.models import PaymentRoute, PaymentMethod
from sqlalchemy.orm import Session

class PaymentRoutingService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def route_payment(self, payment_method: PaymentMethod) -> Optional[dict]:
        """
        Routes payment to the best and backup gateways.
        :param payment_method: PaymentMethod enum
        :return: dict with keys 'selected_gateway', 'backup_gateway', 'success_rate', 'estimated_fee', 'reason'
        """
        # Query active payment routes with given payment_method ordered by success_rate descending
        routes = (
            self.db.query(PaymentRoute)
            .filter(PaymentRoute.payment_method == payment_method)
            # Assuming active gateways - here I assume all in table are active unless a boolean column active exists (not shown in the search)
            # This code can be updated if active column exists
            .order_by(PaymentRoute.success_rate.desc())
            .all()
        )
        if not routes:
            return None
        selected = routes[0]
        backup = routes[1] if len(routes) > 1 else None

        # For simplicity, we estimate fee as 2% of amount (will be replaced with actual fee calculation per gateway)
        estimated_fee = None  # fee calculation will be done in service that calls this with amount

        reason = f"Selected gateway {selected.gateway_name} has highest success rate {selected.success_rate} for payment method {payment_method.name}"
        result = {
            "selected_gateway": selected.gateway_name,
            "backup_gateway": backup.gateway_name if backup else None,
            "success_rate": selected.success_rate,
            "estimated_fee": estimated_fee,
            "reason": reason,
        }
        return result