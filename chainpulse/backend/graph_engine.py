"""
ChainPulse — Graph Engine
NetworkX-based supply chain graph with disruption, cascade BFS, Dijkstra rerouting.
"""

import networkx as nx
import copy
import uuid
from fixtures import NODES, EDGES, SHIPMENTS


class GraphEngine:
    def __init__(self):
        self.G = nx.DiGraph()
        self.shipments = []
        self.disrupted_nodes = {}
        self.cascade_map = {}
        self.reroute_store = {}
        self._build_graph()
        self._load_shipments()

    def _build_graph(self):
        for node in NODES:
            self.G.add_node(
                node["id"],
                label=node["label"],
                type=node["type"],
                lat=node["lat"],
                lng=node["lng"],
                status="normal",
            )
        for edge in EDGES:
            self.G.add_edge(
                edge["source"],
                edge["target"],
                time=edge["base_time"],
                cost=edge["base_cost"],
                reliability=edge["base_reliability"],
                base_time=edge["base_time"],
                base_cost=edge["base_cost"],
                base_reliability=edge["base_reliability"],
                status="normal",
            )

    def _load_shipments(self):
        self.shipments = copy.deepcopy(SHIPMENTS)

    # ── State Export ─────────────────────────────────────────

    def get_state(self) -> dict:
        nodes = []
        for nid, data in self.G.nodes(data=True):
            sc = sum(
                1
                for s in self.shipments
                if nid in s["route"] and s["status"] == "active"
            )
            nodes.append(
                {
                    "id": nid,
                    "label": data.get("label", nid),
                    "type": data.get("type", ""),
                    "lat": data.get("lat", 0),
                    "lng": data.get("lng", 0),
                    "status": data.get("status", "normal"),
                    "shipment_count": sc,
                }
            )
        edges = []
        for u, v, data in self.G.edges(data=True):
            edges.append(
                {
                    "source": u,
                    "target": v,
                    "time": round(data["time"], 1),
                    "cost": round(data["cost"], 0),
                    "reliability": round(data["reliability"], 3),
                    "status": data.get("status", "normal"),
                }
            )
        ship_out = []
        for s in self.shipments:
            ship_out.append(
                {
                    "id": s["id"],
                    "origin": s["origin"],
                    "destination": s["destination"],
                    "current_leg": list(s["current_leg"]),
                    "route": s["route"],
                    "value_inr": s["value_inr"],
                    "sla_deadline_hours": s["sla_deadline_hours"],
                    "criticality": s["criticality"],
                    "client_name": s["client_name"],
                    "status": s["status"],
                }
            )
        return {"nodes": nodes, "edges": edges, "shipments": ship_out}

    def get_counts(self) -> dict:
        active = sum(1 for s in self.shipments if s["status"] == "active")
        at_risk = sum(1 for s in self.shipments if s["status"] == "at_risk")
        rerouted = sum(1 for s in self.shipments if s["status"] == "rerouted")
        return {
            "nodes": self.G.number_of_nodes(),
            "edges": self.G.number_of_edges(),
            "shipments": len(self.shipments),
            "active": active,
            "at_risk": at_risk,
            "rerouted": rerouted,
        }

    # ── Disruption ───────────────────────────────────────────

    def disrupt(self, node_id: str, severity: float, event_type: str) -> dict:
        if node_id not in self.G.nodes:
            raise ValueError(f"Node '{node_id}' not found in graph")

        disruption_id = f"DISRUPT-{uuid.uuid4().hex[:8].upper()}"
        self.disrupted_nodes[node_id] = severity

        # 1. Update edge weights for all edges touching this node
        time_increase = severity * 48
        affected_edges = []
        for u, v, data in self.G.edges(data=True):
            if u == node_id or v == node_id:
                data["reliability"] = data["base_reliability"] * (1 - severity)
                data["time"] = data["base_time"] + time_increase
                data["status"] = "disrupted"
                affected_edges.append((u, v))

        # Mark node as disrupted
        self.G.nodes[node_id]["status"] = "disrupted"

        # 2. Run cascade BFS
        cascade = self._cascade_bfs(node_id, max_depth=3, decay=0.6)
        self.cascade_map = cascade

        # Mark cascade nodes
        for cn, level in cascade.items():
            if cn != node_id and level > 0:
                if self.G.nodes[cn]["status"] != "disrupted":
                    self.G.nodes[cn]["status"] = "at_risk"

        # 3. Mark affected shipments
        affected_shipments = []
        for s in self.shipments:
            if s["status"] == "rerouted":
                continue
            route_nodes = set(s["route"])
            overlap = route_nodes & set(cascade.keys())
            if overlap:
                s["status"] = "at_risk"
                min_level = min(cascade[n] for n in overlap)
                cascade_factor = 0.6 ** min_level

                # 4. Compute consequence
                delay_hours = time_increase * cascade_factor
                hourly_rate = s["value_inr"] / s["sla_deadline_hours"]
                exposure_inr = delay_hours * hourly_rate * 0.15

                # 5. Find reroute options
                reroute_opts = self._find_reroute_options(s, node_id)
                self.reroute_store[s["id"]] = reroute_opts

                affected_shipments.append(
                    {
                        "shipment": {
                            "id": s["id"],
                            "origin": s["origin"],
                            "destination": s["destination"],
                            "current_leg": list(s["current_leg"]),
                            "route": s["route"],
                            "value_inr": s["value_inr"],
                            "sla_deadline_hours": s["sla_deadline_hours"],
                            "criticality": s["criticality"],
                            "client_name": s["client_name"],
                            "status": s["status"],
                        },
                        "delay_hours": round(delay_hours, 1),
                        "exposure_inr": round(exposure_inr, 0),
                        "cascade_level": min_level,
                        "reroute_options": reroute_opts,
                    }
                )

        total_exposure = sum(a["exposure_inr"] for a in affected_shipments)
        max_depth = max((a["cascade_level"] for a in affected_shipments), default=0)

        # Consolidate global reroute options (top 2 unique via-nodes)
        all_opts = []
        via_seen = set()
        for a in affected_shipments:
            for opt in a["reroute_options"]:
                if opt["via_node"] not in via_seen:
                    via_seen.add(opt["via_node"])
                    all_opts.append(opt)
        global_reroute = all_opts[:2]

        # Mark disrupted edges on edges not touching the node (cascade edges)
        for cn, level in cascade.items():
            if level > 0:
                for u, v, data in self.G.edges(data=True):
                    if (u == cn or v == cn) and data["status"] == "normal":
                        data["status"] = "at_risk"

        return {
            "disruption_id": disruption_id,
            "node": node_id,
            "event_type": event_type,
            "severity": severity,
            "affected_shipments": affected_shipments,
            "cascade_depth": max_depth,
            "total_exposure_inr": round(total_exposure, 0),
            "reroute_options": global_reroute,
            "gemini_brief": None,
        }

    def _cascade_bfs(self, start: str, max_depth: int = 3, decay: float = 0.6) -> dict:
        cascade = {start: 0}
        queue = [(start, 0)]
        visited = {start}
        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            neighbors = set(self.G.successors(current)) | set(
                self.G.predecessors(current)
            )
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    cascade[neighbor] = depth + 1
                    queue.append((neighbor, depth + 1))
        return cascade

    def _find_reroute_options(self, shipment: dict, disrupted_node: str) -> list:
        options = []
        route = shipment["route"]
        dest = shipment["destination"]

        # Find the divergence point: last node before the disrupted node in route
        if disrupted_node not in route:
            return options
        disrupt_idx = route.index(disrupted_node)
        if disrupt_idx == 0:
            diverge_node = route[0]
        else:
            diverge_node = route[disrupt_idx - 1]

        # Original remaining cost/time from diverge to destination
        orig_time = self._path_weight(route[route.index(diverge_node) :], "base_time")
        orig_cost = self._path_weight(route[route.index(diverge_node) :], "base_cost")

        # Create a copy with disrupted edges removed for rerouting
        G_alt = self.G.copy()
        edges_to_remove = [
            (u, v)
            for u, v in G_alt.edges()
            if u == disrupted_node or v == disrupted_node
        ]
        G_alt.remove_edges_from(edges_to_remove)

        # Option A: Dijkstra shortest path by time
        try:
            path_a = nx.dijkstra_path(G_alt, diverge_node, dest, weight="time")
            time_a = self._path_weight_on_graph(G_alt, path_a, "time")
            cost_a = self._path_weight_on_graph(G_alt, path_a, "cost")
            via_a = self._find_via_node(route, path_a, disrupted_node)
            via_a_label = self.G.nodes[via_a]["label"] if via_a in self.G.nodes else via_a

            disrupted_time = self._path_weight(
                route[route.index(diverge_node) :], "time"
            )
            time_saving = round(disrupted_time - time_a, 1)
            cost_delta = round(cost_a - orig_cost, 0)

            options.append(
                {
                    "option_index": 0,
                    "via_node": via_a,
                    "via_node_label": via_a_label,
                    "path": path_a,
                    "time_saving_hours": max(time_saving, 0),
                    "cost_delta": cost_delta,
                    "confidence": round(
                        self._path_reliability(G_alt, path_a), 2
                    ),
                }
            )

            # Option B: Remove the key edge of Option A and find another path
            if len(path_a) >= 2:
                G_alt2 = G_alt.copy()
                G_alt2.remove_edge(path_a[0], path_a[1])
                try:
                    path_b = nx.dijkstra_path(
                        G_alt2, diverge_node, dest, weight="time"
                    )
                    time_b = self._path_weight_on_graph(G_alt2, path_b, "time")
                    cost_b = self._path_weight_on_graph(G_alt2, path_b, "cost")
                    via_b = self._find_via_node(route, path_b, disrupted_node)
                    via_b_label = (
                        self.G.nodes[via_b]["label"] if via_b in self.G.nodes else via_b
                    )
                    time_saving_b = round(disrupted_time - time_b, 1)
                    cost_delta_b = round(cost_b - orig_cost, 0)

                    options.append(
                        {
                            "option_index": 1,
                            "via_node": via_b,
                            "via_node_label": via_b_label,
                            "path": path_b,
                            "time_saving_hours": max(time_saving_b, 0),
                            "cost_delta": cost_delta_b,
                            "confidence": round(
                                self._path_reliability(G_alt2, path_b), 2
                            ),
                        }
                    )
                except nx.NetworkXNoPath:
                    pass
        except nx.NetworkXNoPath:
            pass

        return options

    def _find_via_node(self, original_route: list, new_path: list, disrupted: str) -> str:
        for node in new_path:
            if node not in original_route and node != disrupted:
                return node
        if len(new_path) >= 2:
            return new_path[1]
        return new_path[0] if new_path else "unknown"

    def _path_weight(self, path: list, weight_key: str) -> float:
        total = 0
        for i in range(len(path) - 1):
            if self.G.has_edge(path[i], path[i + 1]):
                total += self.G.edges[path[i], path[i + 1]][weight_key]
        return total

    def _path_weight_on_graph(self, G: nx.DiGraph, path: list, weight_key: str) -> float:
        total = 0
        for i in range(len(path) - 1):
            if G.has_edge(path[i], path[i + 1]):
                total += G.edges[path[i], path[i + 1]][weight_key]
        return total

    def _path_reliability(self, G: nx.DiGraph, path: list) -> float:
        reliability = 1.0
        for i in range(len(path) - 1):
            if G.has_edge(path[i], path[i + 1]):
                reliability *= G.edges[path[i], path[i + 1]].get("reliability", 0.9)
        return reliability

    # ── Reroute ──────────────────────────────────────────────

    def reroute(self, shipment_ids: list[str], option_index: int) -> dict:
        rerouted_count = 0
        total_cost_delta = 0
        total_time_saved = 0
        total_exposure_avoided = 0
        rerouted_ids = []
        new_paths = {}

        for sid in shipment_ids:
            ship = next((s for s in self.shipments if s["id"] == sid), None)
            if not ship or ship["status"] == "rerouted":
                continue

            opts = self.reroute_store.get(sid, [])
            idx = min(option_index, len(opts) - 1)
            if idx < 0 or not opts:
                continue

            opt = opts[idx]
            ship["status"] = "rerouted"

            # Build new full route: original route up to diverge, then new path
            old_route = ship["route"]
            new_sub = opt["path"]
            if new_sub and new_sub[0] in old_route:
                merge_idx = old_route.index(new_sub[0])
                ship["route"] = old_route[:merge_idx] + new_sub
            else:
                ship["route"] = new_sub

            total_cost_delta += opt["cost_delta"]
            total_time_saved += opt["time_saving_hours"]
            rerouted_count += 1
            rerouted_ids.append(sid)
            new_paths[sid] = opt["path"]

            # Calculate exposure avoided
            hourly_rate = ship["value_inr"] / ship["sla_deadline_hours"]
            total_exposure_avoided += opt["time_saving_hours"] * hourly_rate * 0.15

        # Mark rerouted edges as green
        for sid, path in new_paths.items():
            for i in range(len(path) - 1):
                if self.G.has_edge(path[i], path[i + 1]):
                    self.G.edges[path[i], path[i + 1]]["status"] = "rerouted"
            # Mark rerouted nodes
            for node in path:
                if self.G.nodes[node]["status"] == "at_risk":
                    self.G.nodes[node]["status"] = "rerouted"

        net_saving = total_exposure_avoided - total_cost_delta

        return {
            "rerouted_count": rerouted_count,
            "total_cost_delta": round(total_cost_delta, 0),
            "total_time_saved_hours": round(total_time_saved, 1),
            "net_saving_inr": round(net_saving, 0),
            "rerouted_shipment_ids": rerouted_ids,
            "new_paths": new_paths,
        }

    # ── Reset ────────────────────────────────────────────────

    def reset(self):
        for u, v, data in self.G.edges(data=True):
            data["time"] = data["base_time"]
            data["cost"] = data["base_cost"]
            data["reliability"] = data["base_reliability"]
            data["status"] = "normal"
        for nid in self.G.nodes:
            self.G.nodes[nid]["status"] = "normal"
        self._load_shipments()
        self.disrupted_nodes = {}
        self.cascade_map = {}
        self.reroute_store = {}


# Quick self-test
if __name__ == "__main__":
    engine = GraphEngine()
    counts = engine.get_counts()
    print(f"Graph: {counts['nodes']} nodes, {counts['edges']} edges, {counts['shipments']} shipments")

    result = engine.disrupt("chennai_port", 0.8, "Cyclone Alert")
    print(f"\nDisruption: {result['disruption_id']}")
    print(f"Affected: {len(result['affected_shipments'])} shipments")
    print(f"Exposure: INR {result['total_exposure_inr']:,.0f}")
    print(f"Cascade depth: {result['cascade_depth']}")
    for opt in result["reroute_options"]:
        print(
            f"  Option {opt['option_index']}: via {opt['via_node_label']}, "
            f"saves {opt['time_saving_hours']}h, costs +INR {opt['cost_delta']:,.0f}"
        )

    at_risk_ids = [a["shipment"]["id"] for a in result["affected_shipments"]]
    rr = engine.reroute(at_risk_ids[:8], 0)
    print(f"\nRerouted: {rr['rerouted_count']} shipments")
    print(f"Net saving: INR {rr['net_saving_inr']:,.0f}")

    engine.reset()
    print(f"\nAfter reset: {engine.get_counts()}")
