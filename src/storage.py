import os
import json
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///trustdesk.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class TicketModel(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True)
    customer_id = Column(String)
    order_id = Column(String)
    subject = Column(String)
    body = Column(Text)
    created_at = Column(String)

class CustomerModel(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    tier = Column(String)

class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    customer_id = Column(String)
    item = Column(String)
    status = Column(String)
    delivery_date = Column(String)

class ToolActionModel(Base):
    __tablename__ = "tool_actions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String, index=True)
    action_name = Column(String)
    status = Column(String, default="PENDING_APPROVAL")
    idempotency_key = Column(String, unique=True, index=True)

class AITraceModel(Base):
    __tablename__ = "ai_traces"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String, index=True)
    run_type = Column(String)
    retrieved_doc_ids = Column(String)
    recommended_action = Column(String)
    guardrail_result = Column(String)
    final_status = Column(String)

Base.metadata.create_all(bind=engine)

def seed_database_from_json(data_dir="data"):
    db = SessionLocal()
    if db.query(TicketModel).first():
        db.close()
        return

    # Seed Customers (safely checking for 'id' or 'customer_id')
    cust_path = os.path.join(data_dir, "customers.json")
    if os.path.exists(cust_path):
        with open(cust_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                c_id = item.get("id", item.get("customer_id", "unknown_c"))
                db.add(CustomerModel(id=c_id, name=item.get("name"), email=item.get("email"), tier=item.get("tier")))

    # Seed Orders (safely checking for 'id' or 'order_id')
    ord_path = os.path.join(data_dir, "orders.json")
    if os.path.exists(ord_path):
        with open(ord_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                o_id = item.get("id", item.get("order_id", "unknown_o"))
                db.add(OrderModel(id=o_id, customer_id=item.get("customer_id"), item=item.get("item", "General Item"), status=item.get("status"), delivery_date=item.get("delivery_date")))

    # Seed Tickets (safely checking for 'id' or 'ticket_id')
    tkt_path = os.path.join(data_dir, "tickets.json")
    if os.path.exists(tkt_path):
        with open(tkt_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                t_id = item.get("id", item.get("ticket_id", "unknown_t"))
                db.add(TicketModel(id=t_id, customer_id=item.get("customer_id"), order_id=item.get("order_id"), subject=item.get("subject", ""), body=item.get("body", item.get("text", "")), created_at=item.get("created_at", "2023-10-01T00:00:00Z")))

    db.commit()
    db.close()