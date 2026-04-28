# ChainPulse: 48-Hour Risk Mitigation Checklist

**Project:** Smart Supply Chain Disruption Detection  
**Track:** Solution Challenge 2026  
**Build Duration:** 48 hours  
**Last Updated:** April 28, 2026

---

## 🎯 Pre-Build Phase (Hour -2 to Hour 0)

### Team & Setup
- [ ] **Team roles assigned clearly**
  - Backend lead: FastAPI + NetworkX + Graph engine
  - Frontend lead: React + Cytoscape.js visualization
  - AI/Product: Claude integration + demo narrative
  - DevOps/QA: Testing + deployment + demo resets
  - Time: 15 min | Severity: 🔴 Critical

- [ ] **Dev environment standardized**
  - Python 3.11+, Node.js 18+, Git repo initialized
  - All team members can run backend in <2 minutes
  - Frontend builds without warnings
  - Time: 30 min | Severity: 🟠 High

- [ ] **GitHub/GitLab repo set up with CI**
  - Backend auto-tests on push
  - Frontend linting + build check
  - Protected main branch (no direct pushes)
  - Time: 20 min | Severity: 🟠 High

- [ ] **API keys secured (Claude, Weather, etc.)**
  - Environment variables (.env) created
  - Never commit secrets to repo
  - Fallback keys ready if rate limit hit
  - Time: 10 min | Severity: 🔴 Critical

---

## 🏗️ Architecture & Infrastructure Phase (Hour 0–6)

### Data Schema & Mocking
- [ ] **Shipment fixture schema defined & locked**
  ```json
  {
    "id": "SHIP-001",
    "origin": "Surat",
    "destination": "Rotterdam",
    "current_leg": "Mumbai→Singapore",
    "value_inr": 2500000,
    "sla_deadline_hours": 168,
    "criticality": "high|medium|low",
    "status": "in_transit",
    "carrier": "Maersk"
  }
  ```
  - Approved by backend + frontend leads
  - 50 shipments pre-generated in JSON
  - Time: 45 min | Severity: 🔴 Critical | Blocker: YES

- [ ] **Edge weight structure finalized**
  ```json
  {
    "from": "Mumbai",
    "to": "Singapore",
    "transit_hours": 96,
    "cost_per_shipment": 12000,
    "reliability_score": 0.92,
    "congestion_factor": 1.0,
    "disruption_probability": 0.05
  }
  ```
  - All edges pre-calculated
  - Backup edges (alternative routes) defined
  - Time: 30 min | Severity: 🔴 Critical | Blocker: YES

- [ ] **Disruption injection payloads mocked**
  - Weather events (JSON matching OpenWeatherMap structure)
  - Port congestion (0–200% slider → multiplier on cost/time)
  - Carrier delay (random seed reproducible)
  - Time: 20 min | Severity: 🟠 High

- [ ] **Maintenance window calendar created**
  - 3–5 known maintenance windows in demo data
  - Rules: suppresses alerts or downgrades severity
  - Time: 15 min | Severity: 🟡 Medium

### API & Backend Skeleton
- [ ] **FastAPI project structure initialized**
  - `/api/graph` endpoints
  - `/api/disruptions` for injection
  - `/api/reroute` for calculation
  - `/api/reset` for demo reset (critical!)
  - Time: 20 min | Severity: 🟠 High

- [ ] **NetworkX graph initialized with fixtures**
  - 15–20 nodes, 25–30 edges
  - All weights loaded from fixtures
  - Dijkstra + BFS tested in isolation
  - Time: 30 min | Severity: 🔴 Critical

- [ ] **Claude API integration scaffolded**
  - System prompt finalized (tone: brief, actionable)
  - Input/output format locked
  - Timeout hardcoded: 1.5 seconds
  - Fallback brief template ready (fires if timeout)
  - Time: 45 min | Severity: 🔴 Critical | Risk: API rate limit

- [ ] **WebSocket connection tested (localhost)**
  - Backend → Frontend message passing works
  - No packet loss on local network
  - Connection test passed
  - Time: 30 min | Severity: 🟠 High

### Frontend Skeleton
- [ ] **React project set up with dependencies**
  - Cytoscape.js or Reagraph installed
  - Tailwind CSS configured
  - State management (React Context) initialized
  - Time: 20 min | Severity: 🟡 Medium

- [ ] **Cytoscape.js prototype (static graph)**
  - 15–20 nodes rendered
  - No animation (static only)
  - Click/hover interactions working
  - Fallback: if animation impossible, use this
  - Time: 1 hour | Severity: 🔴 Critical | Risk: Learning curve

---

## 🔧 Core Feature Implementation (Hour 6–36)

### Phase 1: Risk Detection Engine (Hours 6–12)
- [ ] **Disruption risk scoring implemented**
  - Formula: `risk_score = (congestion_factor × reliability_score) + disruption_prob`
  - Thresholds defined: red >0.75, orange >0.5, green <0.5
  - Test: manual scoring of 5 disruptions matches expected output
  - Time: 2 hours | Severity: 🔴 Critical

- [ ] 
- [ ] **Claude API brief generation working**
  - Sample input → brief output tested
  - Timeout fallback verified (deliberately trigger timeout, verify fallback)
  - Deterministic behavior confirmed
  - Time: 1.5 hours | Severity: 🔴 Critical | Risk: API responsiveness

### Phase 2: Cascade Simulator (Hours 12–20)
- [ ] **BFS cascade propagation implemented**
  - Forward-propagation algorithm runs correctly
  - Decay factor: 0.6^n applied
  - Output: shipments affected at each level (L1, L2, L3)
  - Test: manual trace of 3 disruptions
  - Time: 2 hours | Severity: 🔴 Critical

- [ ] **Decay factor validates correctly**
  - L0 (direct): 100% affected
  - L1 (1 hop): 60% affected
  - L2 (2 hops): 36% affected
  - Verify: typical disruption affects 10–14 shipments total (not entire graph)
  - Time: 30 min | Severity: 🔴 Critical | Red Flag: If >20 shipments affected, reduce decay

- [ ] **Cascade endpoint tested**
  - POST `/api/disruptions/cascade` with disruption payload
  - Response includes: affected_shipments, cascade_levels, total_delay_hours
  - WebSocket push to frontend verified
  - Time: 1.5 hours | Severity: 🔴 Critical

- [ ] **Consequence quantification implemented**
  - Formula: `exposure = affected_shipments × (delay_hours × hourly_penalty + shipment_value × sla_breach_rate)`
  - All 3 affected shipments in demo scenario = ₹1.8Cr exposure
  - Test: manual calculation matches system output
  - Time: 1.5 hours | Severity: 🔴 Critical

### Phase 3: Autonomous Rerouting (Hours 20–28)
- [ ] **Bounded autonomy logic fully specified**
  - Auto-execute if: `(reroute_cost_delta < ₹50K) AND (criticality == "high") AND (toggle == "on")`
  - Recommend & wait if: cost between ₹50K–₹150K
  - Escalate & notify if: cost >₹150K OR no viable reroute
  - Override timeout: 15 minutes → escalate to next in chain
  - Time: 1 hour | Severity: 🔴 Critical | Blocker: YES

- [ ] **Dijkstra rerouting engine implemented**
  - Shortest-path calculation works
  - Alternative routes ranked by (cost, time) Pareto front
  - Test: Chennai disruption → 2 reroute options with correct costs/times
  - Time: 2 hours | Severity: 🔴 Critical

- [ ] **Rerouting decision execution tested**
  - Threshold logic triggers correctly
  - Autonomous execution: edge weights update, shipment paths change
  - Recommendation mode: returns ranked options (no auto-execute)
  - Escalation: logged and tracked
  - Time: 1.5 hours | Severity: 🔴 Critical

- [ ] **POST /reset endpoint fully functional**
  - Resets all graph weights to baseline
  - Clears all disruption state
  - Response time: <500ms (measured)
  - Test: run 3 times consecutively, graph fully clean each time
  - Time: 45 min | Severity: 🔴 Critical | Risk: Demo blocker if slow

### Phase 4: Frontend Visualization (Hours 28–36)
- [ ] **Graph renders with all shipments visible**
  - Nodes: origin, destination, intermediate ports, warehouses
  - Edges: routes with weight labels (hours, cost)
  - Color coding: green (normal), orange (stressed), red (disrupted)
  - Interaction: hover shows shipment details
  - Time: 2 hours | Severity: 🟠 High

- [ ] **Disruption animation works smoothly**
  - Nodes light up red (disrupted) → orange (cascade L1) → yellow (cascade L2)
  - Timing: 200ms per level (total animation 2 seconds)
  - Performance: 60 FPS on demo laptop (test on actual machine!)
  - Time: 1.5 hours | Severity: 🔴 Critical | Risk: Might require fallback

- [ ] **Rerouting animation plays correctly**
  - Old routes fade (opacity 0.3)
  - New routes highlight in green
  - Timing: 1 second total
  - Smooth performance confirmed
  - Time: 1.5 hours | Severity: 🟠 High

- [ ] **Consequence card displays prominently**
  - Shipments affected: 12
  - Hours delayed: 96
  - SLA exposure: ₹1.8Cr (largest font)
  - Reroute cost: ₹12K vs ₹40K (ranked)
  - Claude brief: readable, actionable
  - Time: 1 hour | Severity: 🟠 High

- [ ] **Audit trail visible**
  - Shows: timestamp, disruption type, reroutes executed, cost saved
  - Searchable/filterable
  - Time: 45 min | Severity: 🟡 Medium (nice-to-have but good for judges)

---

## 🧪 Testing & Integration (Hour 36–42)

### End-to-End Demo Scenarios
- [ ] **Scenario 1: Chennai Cyclone (primary demo)**
  - Trigger: "Cyclone alert near Chennai Port"
  - Expected cascade: 12 shipments affected
  - Expected reroute: Option A (Colombo) saves 31 hrs, ₹40K extra per shipment
  - Expected time to resolution: 45 seconds
  - Test iterations: 5 clean runs without errors
  - Time: 1.5 hours | Severity: 🔴 Critical

- [ ] **Scenario 2: Minor disruption (backup)**
  - Trigger: "5% congestion at Mumbai warehouse"
  - Expected: 2–3 shipments affected, minor reroute, auto-execute
  - Purpose: if Chennai demo glitches, run this backup
  - Test: 3 clean runs
  - Time: 45 min | Severity: 🟠 High

- [ ] **Scenario 3: No-viable-reroute edge case**
  - Trigger: Multiple simultaneous disruptions (Chennai + Mumbai)
  - Expected: System alerts "escalate to procurement," no auto-execute
  - Purpose: show bounded autonomy limits
  - Test: 2 runs
  - Time: 30 min | Severity: 🟡 Medium

- [ ] **All scenarios tested on demo hardware**
  - Demo laptop (same machine used for presentation)
  - Network: WiFi (confirm signal strength >-60dBm)
  - Performance: No lag, smooth animations
  - Time: 30 min | Severity: 🔴 Critical | Risk: Demo day laptop differs from dev laptop

### Error Handling & Fallbacks
- [ ] **Claude API timeout (>1.5s) → fallback brief**
  - Manually delay Claude response: verify fallback triggers
  - Fallback brief is readable and professional
  - User never sees API error
  - Time: 30 min | Severity: 🔴 Critical

- [ ] **Graph mutation error handling**
  - Try to update non-existent edge: graceful error, no crash
  - Invalid disruption payload: rejected with clear message
  - Time: 20 min | Severity: 🟠 High

- [ ] **WebSocket connection loss**
  - Backend disconnects: frontend shows "reconnecting..."
  - Reconnects: updates are replayed
  - Time: 30 min | Severity: 🟠 High

- [ ] **No valid reroute scenario**
  - All alternative paths disrupted: system escalates instead of crashing
  - Message: clear, professional, actionable
  - Time: 20 min | Severity: 🟠 High

### Performance Profiling
- [ ] **Backend response time <500ms for all endpoints**
  - Test: Disruption trigger → cascade calculation → response
  - Measure on demo laptop
  - If >500ms: optimize graph size or decay calculation
  - Time: 30 min | Severity: 🟠 High

- [ ] **Frontend re-render smooth (60 FPS during animation)**
  - Use browser DevTools Performance tab
  - Monitor during graph animation
  - If drops below 30 FPS: simplify animation or reduce node count
  - Time: 20 min | Severity: 🟠 High

---

## 📊 Demo Preparation (Hour 42–46)

### Demo Narrative & Timing
- [ ] **45-second demo script finalized and timed**
  - 0–5s: Introduce yourself + ChainPulse concept
  - 5–10s: Show normal operations (green graph)
  - 10–15s: Trigger Chennai disruption
  - 15–35s: Graph animation, cascade propagation, consequence card
  - 35–40s: Execute rerouting (animated path change)
  - 40–45s: Closing statement + "decision engine, not dashboard"
  - Dry run: 10 iterations, all within 45–50 seconds
  - Time: 1 hour | Severity: 🔴 Critical

- [ ] **Speaker notes prepared for each section**
  - Why graph-based approach (audience: all tech and biz)
  - What cascade simulation shows (audience: CFOs care about ₹)
  - Why autonomous action matters (audience: ops teams understand pain)
  - How this differs from Blue Yonder (audience: competitive angle)
  - Time: 45 min | Severity: 🟠 High

- [ ] **Visual hierarchy locked**
  - ₹1.8Cr number: 32px, bold, color-highlighted
  - "45-second resolution" is stated & visualized
  - Graph animation is the emotional peak
  - Time: 20 min | Severity: 🟠 High

- [ ] **Backup plan if demo fails**
  - Recorded video of 45-second demo (pre-recorded)
  - Static screenshot walkthrough as fallback
  - Talking points if you show video instead of live demo
  - Have backup video tested and on USB drive
  - Time: 45 min | Severity: 🔴 Critical | Risk: Live demo technical failure

### Hardware & Connectivity
- [ ] **Demo laptop fully charged + tested**
  - Charge to 100% the night before
  - Run full demo 3× on demo day morning
  - Screenshot: confirm graph renders correctly
  - Time: 20 min | Severity: 🔴 Critical

- [ ] **HDMI/presentation cable tested**
  - Connect to projector/monitor: confirm resolution
  - No artifacts, colors accurate
  - Backup cable in bag
  - Time: 10 min | Severity: 🔴 Critical

- [ ] **WiFi connection verified at venue**
  - Connect to event WiFi: confirm upload/download speeds >5 Mbps
  - If WiFi unreliable: use hotspot as backup (cell phone)
  - Test backend API calls over WiFi
  - Time: 15 min | Severity: 🔴 Critical

- [ ] **Microphone & audio tested**
  - Speak through demo narration: confirm heard clearly
  - Backup: have slides with written text (no audio dependency)
  - Time: 10 min | Severity: 🟠 High

---

## 📑 Presentation Finalization (Hour 46–48)

### Slide Deck Polish
- [ ] **All 15 slides have finalized content**
  - Slide 2: Team name, leader name, team member names
  - Slide 13: GitHub link, Demo video link (if available)
  - No placeholders remaining
  - Time: 20 min | Severity: 🟠 High

- [ ] **Fonts & colors consistent**
  - All slides use brand colors (template provided)
  - Text readable from 10 meters away (venue size)
  - No animations that distract from message
  - Time: 15 min | Severity: 🟡 Medium

- [ ] **Speaker notes on every slide**
  - Note card format: 1-line key message per slide
  - Slide 3: "Graph-based disruption = competitive moat"
  - Slide 6: Read Chennai demo narrative word-for-word
  - Slide 14: "8/10 Innovation because execution, not concept"
  - Time: 30 min | Severity: 🟠 High

- [ ] **Slide transitions rehearsed**
  - No accidental auto-advance
  - Presenter can advance with space bar or clicker
  - Backup: know all slide numbers (if clicker fails)
  - Time: 10 min | Severity: 🟡 Medium

### Final Quality Checks
- [ ] **Full end-to-end rehearsal (5 times)**
  - 3-minute presentation (if time-limited)
  - + 2-minute demo (live or video)
  - + Q&A prep (expect 3–5 questions)
  - Record one iteration (for review if needed)
  - Time: 45 min | Severity: 🔴 Critical

- [ ] **FAQ prep: Predict judge questions**
  - Q: "Why is this better than Blue Yonder's rerouting?"
    A: "We're autonomous within bounded thresholds; Blue Yonder is human-orchestrated"
  - Q: "How do you handle Tier-2+ suppliers?"
    A: "Our graph can scale to 10K+ nodes with Neo4j; demo shows regional network"
  - Q: "What if the AI brief is wrong?"
    A: "Bounded autonomy prevents costly auto-executions; recs go to human always"
  - Q: "How is this different from project44?"
    A: "They show disruptions; we execute decisions in seconds"
  - Time: 30 min | Severity: 🟠 High

- [ ] **Presentation outfit & professionalism**
  - Wear something you're comfortable in (not distracting)
  - Avoid busy patterns (they flicker on camera)
  - Have backup shirt (in case spill)
  - Time: 10 min | Severity: 🟡 Medium

- [ ] **Backup files on multiple devices**
  - PPT on laptop + USB drive + cloud (Google Drive)
  - Demo code on GitHub (accessible even if laptop fails)
  - Screenshot of graph + demo video on USB drive
  - Time: 15 min | Severity: 🔴 Critical

---

## 📋 Submission & Delivery

- [ ] **GitHub repo is public and clean**
  - README with setup instructions
  - No API keys in code
  - Deployment instructions for judges (if they want to run it)
  - Time: 20 min | Severity: 🟠 High

- [ ] **All deliverables submitted by deadline**
  - Presentation PPT
  - GitHub repo link
  - Demo video link (if applicable)
  - Technical architecture doc (PDF)
  - Time: 15 min | Severity: 🔴 Critical

- [ ] **Post-submission: double-check all links work**
  - Click every link in submission
  - Confirm judges can access all resources
  - Time: 10 min | Severity: 🔴 Critical

---

## 🚨 Critical Risk Summary

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|-----------|-------|
| Cytoscape.js animation too slow | High | Demo fails | Fallback: static graph, recorded video | Frontend lead |
| Claude API timeout during demo | Medium | Demo breaks | Hardcoded fallback brief (1.5s timeout) | Backend lead |
| Graph decay factor wrong (all graph red) | Medium | Demo confusing | Pre-test BFS with 0.6^n decay | Backend lead |
| POST /reset endpoint missing | High | Can't reset between judges | Build 45-min, test early | DevOps lead |
| WiFi drops during presentation | Low | Live demo fails | Pre-record demo video as backup | All |
| Demo laptop performance differs from dev | Medium | Animations stutter | Test on actual demo machine 2hrs before | DevOps lead |
| Fixture schema incompatible with frontend | High | Integration breaks | Lock schema by Hour 2, no changes | Tech lead |
| Time management slips into Hour 50+ | High | Rushed demo, sloppy presentation | Enforce daily standups, kill scope creep | Tech lead |

---

## ⏰ Timeline Checkpoints

| Hour | Checkpoint | Status |
|------|-----------|--------|
| **Hour 0** | Team synced, env setup, repo initialized | ⏳ |
| **Hour 6** | Fixtures locked, skeleton APIs running, schema validated | ⏳ |
| **Hour 12** | Risk engine + cascade logic working, Claude fallback tested | ⏳ |
| **Hour 20** | Dijkstra rerouting working, bounded autonomy rules locked | ⏳ |
| **Hour 28** | Frontend graph rendering, animations smooth | ⏳ |
| **Hour 36** | E2E scenario works, all fallbacks tested | ⏳ |
| **Hour 42** | Demo narration finalized & timed, backup video recorded | ⏳ |
| **Hour 46** | Slides polished, speaker notes ready, final rehearsal | ⏳ |
| **Hour 48** | Submission complete, all links verified | ✅ |

---

## 📌 Print This Section

**Post this on team Slack 1 hour before demo:**

```
🚨 FINAL PRE-DEMO CHECKLIST (Run 30 mins before walkthrough):

✅ Graph renders: GREEN
✅ Demo laptop charged: 100%
✅ WiFi connected: Speed >5 Mbps
✅ HDMI cable: Works
✅ Microphone: Clear & audible
✅ Demo runs 45-50 seconds: Timed
✅ No error messages visible: Clean UI
✅ Backup video ready: USB drive
✅ Slides open & backed up: 3 locations
✅ Speaker notes reviewed: Mental confidence

🎯 FINAL WORDS:
"We don't show dashboards. We show decisions."
```

---

**Created:** April 28, 2026  
**For:** ChainPulse Hackathon Team  
**Revision:** Final Draft
