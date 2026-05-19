from core.database import Base
from models.mixins import CreatedAtMixin
from sqlalchemy import Column, String

class ProcessedWebhookEvent(Base, CreatedAtMixin):
    __tablename__ = "processed_webhook_events"

    #pk
    event_id = Column(String, primary_key=True)