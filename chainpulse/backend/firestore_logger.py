"""
ChainPulse — Firestore Audit Logger
Logs disruptions and reroute decisions to Google Cloud Firestore.
Works without Firestore too — gracefully degrades if not configured.
"""

import os
import asyncio
from datetime import datetime, timezone

# Firestore client (lazy init)
_db = None
_enabled = False


def init_firestore():
    """Initialize Firestore. Call once at startup. Safe to fail."""
    global _db, _enabled
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        project_id = os.environ.get("PROJECT_ID", "")
        cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")

        if cred_json:
            import json
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {"projectId": project_id})
        elif cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {"projectId": project_id})
        elif project_id:
            # Running on Cloud Run — uses default credentials
            firebase_admin.initialize_app(options={"projectId": project_id})
        else:
            print("⚠️  Firestore: No credentials found. Audit logging disabled.")
            return

        _db = firestore.client()
        _enabled = True
        print("✅ Firestore: Connected. Audit logging enabled.")
    except Exception as e:
        print(f"⚠️  Firestore: Init failed ({e}). Audit logging disabled (app continues).")
        _enabled = False


async def log_disruption(data: dict):
    """Log a disruption event to Firestore. Non-blocking, fire-and-forget."""
    if not _enabled or not _db:
        return
    try:
        doc = {
            "disruption_id": data.get("disruption_id", ""),
            "node": data.get("node", ""),
            "event_type": data.get("event_type", ""),
            "severity": data.get("severity", 0),
            "affected_count": len(data.get("affected_shipments", [])),
            "total_exposure_inr": data.get("total_exposure_inr", 0),
            "gemini_brief": data.get("gemini_brief", ""),
            "cascade_depth": data.get("cascade_depth", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await asyncio.to_thread(
            _db.collection("disruptions").document(doc["disruption_id"]).set, doc
        )
    except Exception as e:
        print(f"⚠️  Firestore log_disruption failed: {e}")


async def log_reroute(disruption_id: str, data: dict):
    """Log a reroute decision to Firestore. Non-blocking, fire-and-forget."""
    if not _enabled or not _db:
        return
    try:
        doc = {
            "disruption_id": disruption_id,
            "rerouted_count": data.get("rerouted_count", 0),
            "shipment_ids": data.get("rerouted_shipment_ids", []),
            "total_cost_delta": data.get("total_cost_delta", 0),
            "time_saved_hours": data.get("total_time_saved_hours", 0),
            "net_saving_inr": data.get("net_saving_inr", 0),
            "auto_executed": data.get("auto", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await asyncio.to_thread(
            _db.collection("reroutes").add, doc
        )
    except Exception as e:
        print(f"⚠️  Firestore log_reroute failed: {e}")


async def get_audit_log(limit: int = 20) -> list:
    """Retrieve recent disruption audit log from Firestore."""
    if not _enabled or not _db:
        return []
    try:
        def _query():
            docs = (
                _db.collection("disruptions")
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
                .stream()
            )
            return [doc.to_dict() for doc in docs]
        return await asyncio.to_thread(_query)
    except Exception as e:
        print(f"⚠️  Firestore get_audit_log failed: {e}")
        return []
