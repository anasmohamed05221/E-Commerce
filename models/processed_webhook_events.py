from core.database import Base
from models.mixins import CreatedAtMixin
from sqlalchemy import Column, String, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class ProcessedWebhookEvent(Base, CreatedAtMixin):
    __tablename__ = "processed_webhook_events"

    #PK
    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "event_id", name="pk_processed_webhook_events"),
    )

    event_id = Column(String, nullable=False)

    #fk
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    #relationships
    tenant = relationship("Tenant", back_populates="processed_webhook_events")