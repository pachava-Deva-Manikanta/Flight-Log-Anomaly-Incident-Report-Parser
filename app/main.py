from datetime import datetime, timezone
import uuid
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from src.predict import predict_urgency, model_info

app = FastAPI(
    title="AeroTriage - Aviation Urgency Classifier",
    description="Enterprise AI-powered Flight Log Anomaly & Defect Triage System",
    version="2.5.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# In-memory storage for incident log audit trail
incident_registry: List[Dict[str, Any]] = []


class ReporterProfile(BaseModel):
    name: str = Field(default="Capt. Alex Vance", description="Full name of reporter")
    badge_id: str = Field(default="AME-7492", description="Employee or license badge ID")
    role: str = Field(default="Line Maintenance Engineer", description="Operational role")
    station: str = Field(default="JFK / Terminal 4", description="Station or airport base")
    aircraft_reg: str = Field(default="N789AA (B737-800)", description="Aircraft tail registration")
    flight_number: Optional[str] = Field(default="AA-1042", description="Associated flight number")


class IncidentInput(BaseModel):
    description: str
    component: str = ""
    # Reporter details (optional with smart defaults for backwards compatibility)
    reporter_name: Optional[str] = "Capt. Alex Vance"
    badge_id: Optional[str] = "AME-7492"
    role: Optional[str] = "Line Maintenance Engineer"
    station: Optional[str] = "JFK / Terminal 4"
    aircraft_reg: Optional[str] = "N789AA (B737-800)"
    flight_number: Optional[str] = "AA-1042"


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/predict")
def predict_incident(data: IncidentInput):
    if not data.description or not data.description.strip():
        raise HTTPException(status_code=400, detail="Defect description cannot be empty")

    # Run ML prediction pipeline
    prediction = predict_urgency(data.description, data.component)

    # Generate incident ticket metadata
    ticket_id = f"AERO-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build structured incident report
    incident_record = {
        "ticket_id": ticket_id,
        "timestamp": timestamp_utc,
        "reporter": {
            "name": data.reporter_name or "Anonymous Reporter",
            "badge_id": data.badge_id or "GEN-001",
            "role": data.role or "Maintenance Staff",
            "station": data.station or "HQ",
            "aircraft_reg": data.aircraft_reg or "UNASSIGNED",
            "flight_number": data.flight_number or "N/A"
        },
        "component": data.component or "General / Unspecified",
        "description": data.description,
        **prediction
    }

    # Store in memory registry (keep latest 50 records)
    incident_registry.insert(0, incident_record)
    if len(incident_registry) > 50:
        incident_registry.pop()

    return incident_record


@app.get("/incidents")
def get_incidents():
    return {
        "total": len(incident_registry),
        "incidents": incident_registry
    }


@app.delete("/incidents")
def clear_incidents():
    incident_registry.clear()
    return {"message": "Incident registry cleared"}


@app.get("/model-info")
def get_model_info():
    return {
        **model_info,
        "status": "online",
        "server_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "AeroTriage Aviation Safety Engine",
        "server_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    }
