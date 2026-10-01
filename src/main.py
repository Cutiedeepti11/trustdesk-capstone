import os
import uuid
import json
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from src.storage import SessionLocal, TicketModel, CustomerModel, OrderModel, ToolActionModel, AITraceModel, \
    seed_database_from_json
from src.retriever import load_kb
from src.agent import run_agent_triage

app = FastAPI(title="TrustDesk AI Operations")


@app.on_event("startup")
def on_startup():
    seed_database_from_json()
    load_kb()


@app.get("/api/tickets")
def list_tickets():
    db = SessionLocal()
    tickets = db.query(TicketModel).all()
    result = [{"id": t.id, "subject": t.subject, "created_at": t.created_at} for t in tickets]
    db.close()
    return result


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    db = SessionLocal()
    ticket = db.query(TicketModel).filter(TicketModel.id == ticket_id).first()
    if not ticket:
        db.close()
        raise HTTPException(status_code=404, detail="Ticket not found")

    customer = db.query(CustomerModel).filter(CustomerModel.id == ticket.customer_id).first()
    order = db.query(OrderModel).filter(OrderModel.id == ticket.order_id).first()

    res = {
        "ticket": {"id": ticket.id, "subject": ticket.subject, "body": ticket.body, "created_at": ticket.created_at},
        "customer": {"id": customer.id, "name": customer.name, "tier": customer.tier} if customer else {},
        "order": {"id": order.id, "item": order.item, "status": order.status,
                  "delivery_date": order.delivery_date} if order else {}
    }
    db.close()
    return res


class TriageRequest(BaseModel):
    ticket_id: str
    ticket_text: str
    customer_context: dict
    order_context: dict
    created_at: str


@app.post("/api/triage")
def triage_endpoint(req: TriageRequest):
    ai_result, retrieved_ids = run_agent_triage(
        req.ticket_text, req.customer_context, req.order_context, req.created_at
    )

    db = SessionLocal()
    action_key = None
    if ai_result.get("suggested_action") not in ["none", None]:
        action_key = str(uuid.uuid4())
        tool_action = ToolActionModel(
            ticket_id=req.ticket_id,
            action_name=ai_result["suggested_action"],
            status="PENDING_APPROVAL",
            idempotency_key=action_key
        )
        db.add(tool_action)

    # Store minimal trace
    trace = AITraceModel(
        ticket_id=req.ticket_id,
        run_type="triage_and_draft",
        retrieved_doc_ids=json.dumps(retrieved_ids),
        recommended_action=ai_result.get("suggested_action"),
        guardrail_result="ESCALATED_OR_REFUSED" if ai_result.get("needs_escalation") else "PASSED",
        final_status="COMPLETED"
    )
    db.add(trace)
    db.commit()
    db.close()

    return {
        "triage": ai_result,
        "retrieved_docs": retrieved_ids,
        "approval_idempotency_key": action_key
    }


@app.post("/api/tickets/{ticket_id}/approve")
def approve_action(ticket_id: str, idempotency_key: str = Header(...)):
    db = SessionLocal()
    action = db.query(ToolActionModel).filter(ToolActionModel.idempotency_key == idempotency_key).first()
    if not action:
        db.close()
        raise HTTPException(status_code=404, detail="Action not found for this key")

    if action.status == "APPROVED":
        db.close()
        return {"status": "already_approved", "action": action.action_name,
                "message": "Idempotency key matched. Action not re-executed."}

    action.status = "APPROVED"
    db.commit()
    action_name = action.action_name
    db.close()
    return {"status": "success", "executed_action": action_name}


@app.get("/", response_class=HTMLResponse)
def index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()