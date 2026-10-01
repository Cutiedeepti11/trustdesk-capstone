from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
# Using SQLite for zero-config persistence
engine = create_engine("sqlite:///trustdesk.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String)
    order_id = Column(String)
    text = Column(Text)
    created_at = Column(String)

class ToolAction(Base):
    __tablename__ = "tool_actions"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String, index=True)
    action_name = Column(String) # e.g., 'start_refund_review'
    status = Column(String, default="PENDING_APPROVAL")
    idempotency_key = Column(String, unique=True, index=True)

class AITrace(Base):
    __tablename__ = "ai_traces"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String, index=True)
    run_type = Column(String)
    retrieved_doc_ids = Column(String)
    recommended_action = Column(String)
    guardrail_result = Column(String)
    final_status = Column(String)

# Generate the database tables
Base.metadata.create_all(bind=engine)