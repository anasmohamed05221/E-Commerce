import asyncio
from sqlalchemy import select
from celery import shared_task
from models.orders import Order
from models.enums import PaymentMethod, PaymentStatus, OrderStatus
from services.payments import WebhookService
from core.database import async_sessionmaker
from datetime import datetime, timedelta, timezone
import stripe
from utils.logger import get_logger

logger = get_logger(__name__)

@shared_task(ignore_result=True)
def sweep_stale_stripe_orders():
    async def _run():
        async with async_sessionmaker() as db:
            orders = (await db.scalars(
                select(Order)
                .where(
                    Order.payment_method == PaymentMethod.STRIPE,
                    Order.payment_status == PaymentStatus.UNPAID,
                    Order.created_at < datetime.now(timezone.utc) - timedelta(minutes=30)
                )
            )).all()

            for order in orders:
                try:
                    session = stripe.checkout.Session.retrieve(order.stripe_checkout_session_id)
                except stripe.StripeError as e:
                    logger.warning("Failed to retrieve Stripe session during reconciliation", extra={"order_id": order.id, "error": str(e)})
                    continue

                if session.status == "complete":
                    await WebhookService._handle_checkout_completed(db, session)
                    logger.info("Lost webhook recovered via reconciliation", extra={"order_id": order.id})
                    try:
                        await db.commit()
                    except Exception:
                        logger.error("Reconciliation commit failed for confirmed order", extra={"order_id": order.id})
                        await db.rollback()
                elif session.status == "expired":
                    order.payment_status = PaymentStatus.EXPIRED
                    order.status = OrderStatus.CANCELLED
                    logger.info("Stale order marked expired via reconciliation", extra={"order_id": order.id})
                    try:
                        await db.commit()
                    except Exception:
                        logger.error("Reconciliation commit failed for expired order", extra={"order_id": order.id})
                        await db.rollback()
            

    asyncio.run(_run())