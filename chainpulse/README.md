# ⚡ ChainPulse

**"We didn't build a dashboard. We built a decision engine."**

Real-time supply chain disruption detection and autonomous rerouting system.
Built for **GDG Solution Challenge 2026**.

---

## Quick Start (3 commands)

```bash
git clone https://github.com/your-team/chainpulse.git && cd chainpulse
cp .env.example .env  # Add your GEMINI_API_KEY
docker-compose up
```

Then open: **http://localhost:3000** (frontend) | **http://localhost:8080/docs** (API docs)

---

## Manual Start (no Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here    # or set in .env
uvicorn main:app --reload --port 8080
```

**Frontend:**
Open `frontend/index.html` in your browser. If backend is not on localhost:8080,
edit the `BACKEND` const in the script.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Vanilla JS/HTML)            │
│  ┌──────────────┐  ┌──────────────────────────────────┐ │
│  │ Control Panel │  │   Leaflet.js Map (Geographic)    │ │
│  │ • Disrupt btn │  │   • Green/Red/Orange/Blue nodes  │ │
│  │ • Severity    │  │   • Animated edge rerouting      │ │
│  │ • Auto-toggle │  │   • Real-time WebSocket updates  │ │
│  │ • Cards       │  │                                  │ │
│  └──────┬───────┘  └───────────────┬──────────────────┘ │
└─────────┼──────────────────────────┼────────────────────┘
          │  HTTP POST               │  WebSocket
          ▼                          ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
│  ┌────────────┐ ┌────────────┐ ┌──────────────────────┐│
│  │ /disrupt   │ │ /reroute   │ │ /reset    /health    ││
│  └─────┬──────┘ └─────┬──────┘ └──────────────────────┘│
│        │              │                                 │
│  ┌─────▼──────────────▼───────────────────────────────┐│
│  │         GraphEngine (NetworkX)                      ││
│  │  • BFS Cascade (0.6^n decay, depth 3)              ││
│  │  • Dijkstra Rerouting (dual options)               ││
│  │  • Consequence Calculator (₹ exposure)             ││
│  └────────────────────┬───────────────────────────────┘│
│                       │                                 │
│  ┌────────────────────▼───────────────────────────────┐│
│  │         Gemini 1.5 Flash (AI Brief)                ││
│  │  • 3-sentence ops brief │ 2s timeout │ Fallback    ││
│  └────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check with node/shipment counts |
| GET | `/graph` | Full graph state (nodes, edges, shipments) |
| POST | `/disrupt` | Inject disruption → cascade → reroute options |
| POST | `/reroute` | Execute rerouting for selected shipments |
| POST | `/reset` | Restore graph to green state |
| WS | `/ws` | Real-time graph state updates |

Interactive docs: http://localhost:8080/docs

---

## Demo Script (45 seconds)

1. **Open ChainPulse** — all 20 shipments green, graph healthy
2. **Select:** Node = Chennai Port, Event = Cyclone Alert, Severity = 80%
3. **Click "Trigger Disruption"** — Chennai flashes red
4. **Watch cascade** — 12 shipments turn orange (at risk)
5. **Read consequence card** — ₹ exposure in large red font
6. **Read Gemini brief** — 3-sentence AI analysis
7. **Compare options** — Option A (Colombo) vs Option B (Dubai)
8. **Click "Execute A"** — rerouted paths animate green
9. **See resolution** — net saving in green, shipments rerouted
10. **Click Reset** — everything fades back to green

**Key line for judges:** *"We don't show dashboards. We show decisions."*

---

## Deployment

- **Frontend:** Deployed on **Vercel**
- **Backend:** Deployed on **Google Cloud Run** (or Render)

See [deploy.sh](./deploy.sh) for backend deployment instructions to Cloud Run.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML + Leaflet.js + Vanilla CSS (Glassmorphism) |
| Backend | Python FastAPI |
| Graph Engine | NetworkX (in-memory) |
| AI | Gemini 1.5 Flash |
| Real-Time | WebSocket |
| Deploy | Vercel (Frontend) + Google Cloud Run (Backend) |

---

**Team:** ChainPulse | Solution Challenge 2026
