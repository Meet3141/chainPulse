"""
ChainPulse — FastAPI Application
All endpoints, WebSocket manager, CORS configuration.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from graph_engine import GraphEngine
from gemini_client import generate_brief
from models import DisruptRequest, RerouteRequest
from firestore_logger import init_firestore, log_disruption, log_reroute, get_audit_log

# ── Globals ──────────────────────────────────────────────────

engine = GraphEngine()


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ── App ──────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_firestore()
    print(f"ChainPulse started — {engine.get_counts()['nodes']} nodes, "
          f"{engine.get_counts()['edges']} edges, "
          f"{engine.get_counts()['shipments']} shipments")
    yield
    print("ChainPulse shutting down")


app = FastAPI(
    title="ChainPulse API",
    description="Smart Supply Chain Disruption Detection & Autonomous Rerouting",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper ───────────────────────────────────────────────────

async def _broadcast_state(alert: dict | None = None):
    state = engine.get_state()
    msg = {"type": "graph_update", "data": {**state, "alert": alert}}
    await manager.broadcast(msg)


# ── Endpoints ────────────────────────────────────────────────

@app.get("/health")
@app.head("/health")
async def health():
    c = engine.get_counts()
    return {
        "status": "ok",
        "nodes": c["nodes"],
        "edges": c["edges"],
        "shipments": c["shipments"],
    }

@app.get("/")
@app.head("/")
async def root():
    return {"status": "ChainPulse API is running"}


@app.get("/graph")
async def get_graph():
    return engine.get_state()


@app.post("/disrupt")
async def disrupt(req: DisruptRequest):
    result = engine.disrupt(req.node, req.severity, req.event_type)

    # Build Gemini prompt data
    reroute_opt_a = ""
    time_saving = 0
    cost_delta = 0
    net_saving = 0
    if result["reroute_options"]:
        opt = result["reroute_options"][0]
        reroute_opt_a = opt["via_node_label"]
        time_saving = opt["time_saving_hours"]
        cost_delta = opt["cost_delta"]
        net_saving = result["total_exposure_inr"] - cost_delta

    # Get node label
    node_label = req.node
    for n in engine.get_state()["nodes"]:
        if n["id"] == req.node:
            node_label = n["label"]
            break

    gemini_data = {
        "event_type": req.event_type,
        "node_name": node_label,
        "severity": req.severity,
        "count": len(result["affected_shipments"]),
        "exposure_inr": result["total_exposure_inr"],
        "reroute_option_a": reroute_opt_a,
        "time_saving": time_saving,
        "cost_delta": cost_delta,
        "net_saving": net_saving,
    }

    # Generate brief (async with 2s timeout)
    brief = await generate_brief(gemini_data)
    result["gemini_brief"] = brief

    # Log to Firestore (fire-and-forget)
    asyncio.create_task(log_disruption(result))

    # Broadcast to all WebSocket clients
    await _broadcast_state(alert={
        "type": "disruption",
        "disruption_id": result["disruption_id"],
        "node": req.node,
        "event_type": req.event_type,
        "severity": req.severity,
        "affected_count": len(result["affected_shipments"]),
        "total_exposure_inr": result["total_exposure_inr"],
    })

    return result


@app.post("/reroute")
async def reroute(req: RerouteRequest):
    result = engine.reroute(req.shipment_ids, req.option_index)
    result["auto"] = req.auto

    # Log to Firestore (fire-and-forget)
    asyncio.create_task(log_reroute("latest", result))

    await _broadcast_state(alert={
        "type": "reroute",
        "rerouted_count": result["rerouted_count"],
        "total_time_saved_hours": result["total_time_saved_hours"],
        "net_saving_inr": result["net_saving_inr"],
        "auto": req.auto,
    })

    return result


@app.post("/reset")
async def reset():
    engine.reset()

    await _broadcast_state(alert={"type": "reset"})

    return {"status": "reset", "message": "Graph restored to green state"}


@app.get("/audit")
async def audit_log():
    """Retrieve recent disruption and reroute audit log from Firestore."""
    logs = await get_audit_log(limit=20)
    return {"audit_log": logs, "count": len(logs)}


# ── WebSocket ────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        # Send current state on connect
        state = engine.get_state()
        await ws.send_json({"type": "graph_update", "data": {**state, "alert": None}})

        # Keep connection alive, listen for pings
        while True:
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=30)
                if data == "ping":
                    await ws.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await ws.send_text("pong")
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(ws)


# ── Run ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
