from sqlalchemy.orm import Session, with_loader_criteria
from sqlalchemy import event
from models.users import User
from models.products import Product
from models.categories import Category
from models.orders import Order
from models.cart_items import CartItem
from models.addresses import Address
from models.processed_webhook_events import ProcessedWebhookEvent

TENANT_SCOPED_MODELS = frozenset({
    User,
    Product,
    Category,
    Order,
    CartItem,
    Address,
    ProcessedWebhookEvent,
})

def register_tenant_scoping():
    """Register the do_orm_execute listener that auto-filters all SELECT queries by tenant_id."""
    @event.listens_for(Session, "do_orm_execute")
    def apply_tenant_filter(execute_state):
        if(
            execute_state.is_select
            and not execute_state.is_column_load
            and not execute_state.is_relationship_load
        ):
            tenant_id = execute_state.session.info.get("tenant_id")
            if tenant_id is None:
                return
            execute_state.statement = execute_state.statement.options(
                *[
                    with_loader_criteria(model, model.tenant_id == tenant_id, include_aliases=True)
                    for model in TENANT_SCOPED_MODELS
                ]
            )