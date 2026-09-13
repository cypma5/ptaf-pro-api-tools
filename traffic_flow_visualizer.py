# traffic_flow_visualizer.py
# Сбор маршрутизации трафика (VIP:port → приложение → бекенды) и сохранение Mermaid в файл.
#
# Альтернативный источник (PTAF 4.5.0+): GET config/snapshot?mode=sync —
# расширенный снапшот может содержать VIP/profiles/backends в одном ответе.
# Пока визуализация строится по отдельным API; разбор mode=sync — TODO.
import datetime
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from base_manager import BaseManager

# Зарезервировано для будущей сборки графа из расширенного снапшота
SNAPSHOT_SYNC_MODE = "sync"
SNAPSHOT_SYNC_MIN_VERSION = "4.5.0"


class TrafficFlowVisualizer(BaseManager):
    def __init__(self, api_client):
        super().__init__(api_client)

    def manage_traffic_flow_diagram(self):
        """Интерактивная генерация диаграммы прохождения трафика."""
        print("\n=== Визуализация прохождения трафика (Mermaid) ===")
        tenant_id = self.api_client.auth_manager.tenant_id
        if not tenant_id:
            print("Тенант не выбран.")
            return None

        tenant_name = tenant_id
        try:
            from tenants import TenantManager
            tm = TenantManager(self.api_client.auth_manager, self.api_client.make_request)
            for t in tm.get_available_tenants() or []:
                if t.get("id") == tenant_id:
                    tenant_name = t.get("name") or tenant_id
                    break
        except Exception:
            pass

        print(f"Сбор данных для тенанта: {tenant_name} ({tenant_id})")
        filepath = self.generate_and_save(tenant_id=tenant_id, tenant_name=tenant_name)
        return filepath

    def fetch_sync_snapshot_if_available(self) -> Optional[Dict[str, Any]]:
        """
        Альтернатива отдельным API: GET config/snapshot?mode=sync (PTAF 4.5.0+).
        Пока только заготовка — разбор и построение графа из sync-снапшота TODO.
        """
        from version_utils import get_release_from_versions_response, version_gte

        release = None
        try:
            response = self.api_client.get_versions()
            if response and response.status_code == 200:
                data = response.json()
                payload = data.get("data") if isinstance(data, dict) else None
                release = get_release_from_versions_response(payload)
        except Exception:
            return None
        if not version_gte(release, SNAPSHOT_SYNC_MIN_VERSION):
            return None
        resp = self.api_client.get_snapshot(mode=SNAPSHOT_SYNC_MODE)
        if resp and resp.status_code == 200:
            return resp.json()
        return None

    def generate_and_save(self, tenant_id: str, tenant_name: Optional[str] = None) -> Optional[str]:
        graph = self.collect_traffic_graph()
        if graph is None:
            print("Не удалось собрать данные для диаграммы.")
            return None

        flowchart = self.build_flowchart_mermaid(graph)
        sankey = self.build_sankey_mermaid(graph)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        label = tenant_name or tenant_id
        content = (
            f"# Traffic flow — {label} — {timestamp}\n\n"
            f"Тенант: `{tenant_id}`\n\n"
            f"- VIP / listen IP: {graph['stats']['listens']}\n"
            f"- Gateways: {graph['stats'].get('gateways', 0)}\n"
            f"- Listen ports: {graph['stats'].get('ports', 0)}\n"
            f"- Веб-приложения: {graph['stats']['apps']}\n"
            f"- Бекенды: {graph['stats']['backends']}\n"
            f"- Рёбра: {graph['stats']['edges']}\n\n"
            f"## Flowchart\n\n"
            f"```mermaid\n{flowchart}\n```\n\n"
            f"## Sankey\n\n"
            f"```mermaid\n{sankey}\n```\n"
        )

        out_dir = os.path.join("traffic_flow", self._ptaf_host_dirname(), tenant_id)
        os.makedirs(out_dir, exist_ok=True)
        filename = f"{timestamp}-traffic-flow.md"
        filepath = os.path.abspath(os.path.join(out_dir, filename))
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Ошибка сохранения файла: {e}")
            return None

        print(
            f"Диаграмма сохранена (flowchart + sankey-beta): {filepath}\n"
            f"  vip={graph['stats']['listens']}, "
            f"ports={graph['stats'].get('ports', 0)}, "
            f"apps={graph['stats']['apps']}, "
            f"backends={graph['stats']['backends']}, "
            f"edges={graph['stats']['edges']}"
        )
        return filepath

    def _ptaf_host_dirname(self) -> str:
        """Имя папки из ptaf_url / base_url без схемы (например m0-96.af.appsec.ptsecurity.ru)."""
        from urllib.parse import urlparse

        raw = getattr(self.api_client.auth_manager, "base_url", None) or ""
        raw = str(raw).strip()
        if not raw:
            return "unknown-host"
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        host = parsed.hostname or parsed.path.split("/")[0] or raw
        host = host.strip().rstrip("/")
        # безопасное имя каталога
        host = re.sub(r'[<>:"/\\|?*]', "_", host)
        return host or "unknown-host"

    def collect_traffic_graph(self) -> Optional[Dict[str, Any]]:
        apps_resp = self.api_client.get_applications()
        backends_resp = self.api_client.get_backends()
        profiles_resp = self.api_client.get_traffic_profiles()
        vips_resp = self.api_client.get_vips()

        applications = self._parse_response_items(apps_resp) or []
        backends = self._parse_response_items(backends_resp) or []
        profiles = self._parse_response_items(profiles_resp) or []
        vips = self._parse_response_items(vips_resp) or []

        if apps_resp is None and backends_resp is None and profiles_resp is None:
            return None

        vip_by_id = {str(v.get("id")): v for v in vips if v.get("id")}
        backend_by_id = {str(b.get("id")): b for b in backends if b.get("id")}

        # app_id -> set(profile_id)
        app_profiles: Dict[str, Set[str]] = {}
        for app in applications:
            app_id = str(app.get("id") or app.get("name") or id(app))
            raw = app.get("traffic_profiles") or []
            if isinstance(raw, list):
                app_profiles[app_id] = {str(x) for x in raw if x}
            else:
                app_profiles[app_id] = set()

        # profile_id -> apps that reference it
        profile_to_apps: Dict[str, List[Dict[str, Any]]] = {}
        for app in applications:
            app_id = str(app.get("id") or app.get("name") or id(app))
            for pid in app_profiles.get(app_id, set()):
                profile_to_apps.setdefault(pid, []).append(app)

        # Ensure we have full profile details (list may already include backends/balancer)
        profiles_full: List[Dict[str, Any]] = []
        for p in profiles:
            pid = p.get("id")
            if p.get("balancer") is not None and p.get("backends") is not None:
                profiles_full.append(p)
                continue
            if not pid:
                continue
            details_resp = self.api_client.get_traffic_profile_details(pid)
            if details_resp and details_resp.status_code == 200:
                profiles_full.append(details_resp.json())
            else:
                profiles_full.append(p)

        # Цвета рёбер: профили, привязанные к приложениям с >1 профилем
        profile_edge_color: Dict[str, str] = {}
        for _app_id, pids in app_profiles.items():
            if len(pids) <= 1:
                continue
            for i, pid in enumerate(sorted(pids)):
                profile_edge_color.setdefault(
                    pid, self.PROFILE_EDGE_COLORS[i % len(self.PROFILE_EDGE_COLORS)]
                )

        vip_nodes: Dict[str, Dict[str, str]] = {}
        gateway_nodes: Dict[str, Dict[str, str]] = {}
        vip_gateways: Dict[str, List[str]] = {}
        port_nodes: Dict[str, Dict[str, str]] = {}
        app_nodes: Dict[str, Dict[str, str]] = {}
        backend_nodes: Dict[str, Dict[str, str]] = {}
        edges: List[Tuple[str, str, Optional[str]]] = []
        edge_seen: Set[Tuple[str, str, str]] = set()
        sankey_links: Set[Tuple[str, str]] = set()

        for profile in profiles_full:
            profile_id = str(profile.get("id") or "")
            edge_color = profile_edge_color.get(profile_id)
            balancer = profile.get("balancer") or {}
            listen_port = balancer.get("listen_port")
            protocol = (balancer.get("protocol_options") or {}).get("type") or ""
            balancer_type = balancer.get("type") or ""

            vip_ids = self._collect_balancer_vip_ids(balancer)

            vip_node_ids = self._ensure_vip_nodes(
                vip_ids=vip_ids,
                balancer_type=balancer_type,
                profile_id=profile_id,
                vip_by_id=vip_by_id,
                vip_nodes=vip_nodes,
                gateway_nodes=gateway_nodes,
                vip_gateways=vip_gateways,
            )

            linked_apps = profile_to_apps.get(profile_id, [])
            if not linked_apps:
                profile_short = profile.get("name") or profile_id[:8]
                targets = [{
                    "app_node_id": f"A_unassigned_{self._safe_id(profile_id)}",
                    "app_label": f"(no application) {profile_short}",
                    "sankey_app": f"(no app) {profile_short}",
                    "locations": ["/"],
                    "protection_mode": "",
                    "style_key": "ORPHAN_PROFILE",
                }]
            else:
                targets = []
                for app in linked_apps:
                    app_node_id, app_label, sankey_app, locations = self._app_node(app)
                    targets.append({
                        "app_node_id": app_node_id,
                        "app_label": app_label,
                        "sankey_app": sankey_app,
                        "locations": locations,
                        "protection_mode": str(app.get("protection_mode") or ""),
                        "style_key": str(app.get("protection_mode") or ""),
                    })

            # Gateway -> VIP address -> VIP port -> App
            vip_port_ids: List[str] = []
            for vip_node_id in vip_node_ids:
                vip_label = (vip_nodes.get(vip_node_id) or {}).get("label") or vip_node_id
                vip_port_id, vip_port_label = self._vip_port_node(
                    listen_port, protocol, unique_key=vip_node_id, vip_label=vip_label
                )
                port_nodes[vip_port_id] = {"id": vip_port_id, "label": vip_port_label}
                vip_port_ids.append(vip_port_id)
                self._add_edge(edges, edge_seen, vip_node_id, vip_port_id, edge_color)
                for gw_id in vip_gateways.get(vip_node_id) or []:
                    # Gateway относится к VIP-адресу, не к порту
                    self._add_edge(edges, edge_seen, gw_id, vip_node_id, None)

            for target in targets:
                app_node_id = target["app_node_id"]
                app_nodes[app_node_id] = {
                    "id": app_node_id,
                    "label": target["app_label"],
                    "protection_mode": target.get("protection_mode") or "",
                    "style_key": target.get("style_key") or "",
                }
                for vip_port_id in vip_port_ids:
                    self._add_edge(edges, edge_seen, vip_port_id, app_node_id, edge_color)
                self._link_profile_backends(
                    profile,
                    backend_by_id,
                    backend_nodes,
                    port_nodes,
                    edges,
                    edge_seen,
                    sankey_links,
                    from_app_id=app_node_id,
                    sankey_app=target["sankey_app"],
                    locations=target["locations"],
                    edge_color=edge_color,
                )

        # Apps without any traffic profile
        for app in applications:
            app_id = str(app.get("id") or app.get("name") or id(app))
            if app_profiles.get(app_id):
                continue
            app_node_id, app_label, _sankey_app, _locations = self._app_node(app)
            app_nodes[app_node_id] = {
                "id": app_node_id,
                "label": app_label,
                "protection_mode": str(app.get("protection_mode") or ""),
                "style_key": "ORPHAN_APP",
            }
            orphan_port = "VP_none"
            port_nodes[orphan_port] = {"id": orphan_port, "label": "no traffic profile"}
            self._add_edge(edges, edge_seen, orphan_port, app_node_id, None)

        return {
            "vip_nodes": vip_nodes,
            "gateway_nodes": gateway_nodes,
            "port_nodes": port_nodes,
            "app_nodes": app_nodes,
            "backend_nodes": backend_nodes,
            "edges": edges,
            "sankey_links": sorted(sankey_links),
            "stats": {
                "listens": len(vip_nodes),
                "gateways": len(gateway_nodes),
                "ports": len(port_nodes),
                "apps": len(app_nodes),
                "backends": len(backend_nodes),
                "edges": len(edges),
            },
        }

    def _collect_balancer_vip_ids(self, balancer: Dict[str, Any]) -> List[str]:
        """INTERNAL_BALANCER: vip_id; STATIC_BALANCER: vips[]."""
        ids: List[str] = []
        seen = set()
        single = balancer.get("vip_id")
        if single:
            key = str(single)
            if key not in seen:
                seen.add(key)
                ids.append(key)
        for vip_id in balancer.get("vips") or []:
            if not vip_id:
                continue
            key = str(vip_id)
            if key not in seen:
                seen.add(key)
                ids.append(key)
        return ids

    def _resolve_vip(self, vip_id: str, vip_by_id: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        cached = vip_by_id.get(str(vip_id))
        # Список VIP может не содержать routes — дотягиваем details при необходимости
        if cached is not None:
            options = cached.get("options")
            if isinstance(options, dict) and "routes" in options:
                return cached
        vip_resp = self.api_client.get_vip_details(vip_id)
        if vip_resp and vip_resp.status_code == 200:
            vip = vip_resp.json()
            vip_by_id[str(vip_id)] = vip
            return vip
        return cached

    def _ensure_vip_nodes(
        self,
        vip_ids: List[str],
        balancer_type: str,
        profile_id: str,
        vip_by_id: Dict[str, Dict[str, Any]],
        vip_nodes: Dict[str, Dict[str, str]],
        gateway_nodes: Dict[str, Dict[str, str]],
        vip_gateways: Dict[str, List[str]],
    ) -> List[str]:
        """Создаёт узлы VIP IP (без порта) и связанные Gateway из routes."""
        node_ids: List[str] = []
        if vip_ids:
            for vip_id in vip_ids:
                vip = self._resolve_vip(vip_id, vip_by_id)
                address = self._vip_address(vip) or f"VIP:{vip_id[:8]}"
                node_id = f"VIP_{self._safe_id(vip_id)}"
                vip_nodes[node_id] = {"id": node_id, "label": address}
                vip_gateways[node_id] = self._ensure_vip_gateway_nodes(vip, gateway_nodes)
                node_ids.append(node_id)
            return node_ids

        # EXTERNAL_BALANCER / без VIP — отдельный узел по профилю
        node_id = f"VIP_{self._safe_id(profile_id)}"
        label = balancer_type or "no VIP"
        vip_nodes[node_id] = {"id": node_id, "label": label}
        vip_gateways[node_id] = []
        node_ids.append(node_id)
        return node_ids

    def _ensure_vip_gateway_nodes(
        self,
        vip: Optional[Dict[str, Any]],
        gateway_nodes: Dict[str, Dict[str, str]],
    ) -> List[str]:
        """Узлы Gateway из options.routes VIP (default = 0.0.0.0/0)."""
        gw_ids: List[str] = []
        for destination, gateway in self._vip_routes(vip):
            gw_id = f"GW_{self._safe_id(gateway)}_{self._safe_id(destination)}"
            label = f"Gateway:\n  {gateway}\nDestination:\n  {destination}"
            gateway_nodes[gw_id] = {"id": gw_id, "label": label}
            gw_ids.append(gw_id)
        return gw_ids

    @staticmethod
    def _vip_routes(vip: Optional[Dict[str, Any]]) -> List[Tuple[str, str]]:
        """[(destination, gateway), ...] из options.routes."""
        if not vip:
            return []
        options = vip.get("options") or {}
        routes = options.get("routes") or []
        result: List[Tuple[str, str]] = []
        seen = set()
        for route in routes:
            if not isinstance(route, dict):
                continue
            gateway = str(route.get("gateway") or "").strip()
            if not gateway:
                continue
            destination = str(route.get("destination") or "").strip()
            dest_norm = destination.lower()
            if dest_norm in ("default", "0.0.0.0/0", "0.0.0.0"):
                destination = "0.0.0.0/0"
            key = (destination, gateway)
            if key in seen:
                continue
            seen.add(key)
            result.append((destination, gateway))
        return result

    def _vip_port_node(
        self,
        listen_port: Any,
        protocol: str = "",
        unique_key: str = "",
        vip_label: str = "",
    ) -> Tuple[str, str]:
        """Порт прослушивания VIP — уникален для каждого Listen VIP."""
        port_part = str(listen_port) if listen_port is not None else "unknown"
        key = unique_key or port_part
        node_id = f"VP_{self._safe_id(str(key))}_{self._safe_id(port_part)}"
        label = f"VIP port {port_part}"
        if protocol:
            label = f"{label} ({protocol})"
        if vip_label:
            label = f"{label} @ {vip_label}"
        return node_id, label

    def _backend_port_node(
        self,
        backend_port: Any,
        protocol: str = "",
        unique_key: str = "",
        backend_label: str = "",
    ) -> Tuple[str, str]:
        """Порт бекенда — уникален для каждого Backend IP."""
        port_part = str(backend_port) if backend_port is not None else "unknown"
        key = unique_key or port_part
        node_id = f"BP_{self._safe_id(str(key))}"
        label = f"backend port {port_part}"
        if protocol:
            label = f"{label} ({protocol})"
        if backend_label:
            label = f"{label} @ {backend_label}"
        return node_id, label

    def _link_profile_backends(
        self,
        profile: Dict[str, Any],
        backend_by_id: Dict[str, Dict[str, Any]],
        backend_nodes: Dict[str, Dict[str, str]],
        port_nodes: Dict[str, Dict[str, str]],
        edges: List[Tuple[str, str, Optional[str]]],
        edge_seen: Set[Tuple[str, str, str]],
        sankey_links: Set[Tuple[str, str]],
        from_app_id: str,
        sankey_app: str,
        locations: List[str],
        edge_color: Optional[str] = None,
    ) -> None:
        """Flowchart: App → backend port → backend IP.
        Sankey: App → Location → backend port → backend IP.
        """
        locs = locations or ["/"]
        for be in profile.get("backends") or []:
            if not isinstance(be, dict):
                continue
            bid = be.get("id")
            if not bid:
                continue
            backend = backend_by_id.get(str(bid))
            backend_port = backend.get("port") if backend else None
            backend_proto = (backend.get("protocol") or "") if backend else ""

            node_id, be_label = self._backend_ip_node(backend, bid, be)
            be_address = str((backend or {}).get("address") or be_label.split()[0])
            bp_id, bp_label = self._backend_port_node(
                backend_port,
                backend_proto,
                unique_key=str(bid),
                backend_label=be_address,
            )
            port_nodes[bp_id] = {"id": bp_id, "label": bp_label}
            self._add_edge(edges, edge_seen, from_app_id, bp_id, edge_color)

            backend_nodes[node_id] = {"id": node_id, "label": be_label}
            self._add_edge(edges, edge_seen, bp_id, node_id, edge_color)

            # Короткие уникальные подписи для sankey (длинные ломают layout)
            port_part = str(backend_port) if backend_port is not None else "?"
            sankey_bp = f"{be_address}:{port_part}"
            sankey_be = be_address
            for loc in locs:
                loc_label = f"{sankey_app}|{loc}"
                sankey_links.add((sankey_app, loc_label))
                sankey_links.add((loc_label, sankey_bp))
                sankey_links.add((sankey_bp, sankey_be))

    @staticmethod
    def _add_edge(
        edges: List[Tuple[str, str, Optional[str]]],
        edge_seen: Set[Tuple[str, str, str]],
        src: str,
        dst: str,
        color: Optional[str] = None,
    ) -> None:
        # Одно ребро src→dst; если позже появляется цвет — обновляем
        for i, (s, d, c) in enumerate(edges):
            if s == src and d == dst:
                if color and not c:
                    old_key = (src, dst, c or "")
                    edge_seen.discard(old_key)
                    edges[i] = (src, dst, color)
                    edge_seen.add((src, dst, color))
                return
        key = (src, dst, color or "")
        if key in edge_seen:
            return
        edge_seen.add(key)
        edges.append((src, dst, color))

    # Цвета рёбер для приложений с несколькими traffic profiles
    PROFILE_EDGE_COLORS = [
        "#e74c3c",
        "#3498db",
        "#8e44ad",
        "#16a085",
        "#d35400",
        "#2c3e50",
        "#c0392b",
        "#2980b9",
    ]

    @staticmethod
    def _vip_address(vip: Optional[Dict[str, Any]]) -> Optional[str]:
        if not vip:
            return None
        options = vip.get("options") or {}
        address = options.get("address")
        if address:
            return str(address)
        name = vip.get("name")
        return str(name) if name else None

    def _app_node(self, app: Dict[str, Any]) -> Tuple[str, str, str, List[str]]:
        """
        Returns: node_id, flowchart_label, sankey_app_label, locations.
        """
        app_id = str(app.get("id") or app.get("name") or "app")
        name = app.get("name") or "unnamed"
        hosts = [str(h) for h in (app.get("hosts") or [])]
        locations = [str(l) for l in (app.get("locations") or [])] or ["/"]
        sankey_app = str(name)

        lines = ["Name:", f"  {name}", "Hosts:"]
        if hosts:
            lines.extend(f"  {h}" for h in hosts)
        else:
            lines.append("  -")
        lines.append("Locations:")
        lines.extend(f"  {loc}" for loc in locations)
        flowchart_label = "\n".join(lines)

        return f"A_{self._safe_id(app_id)}", flowchart_label, sankey_app, locations

    def _backend_ip_node(
        self,
        backend: Optional[Dict[str, Any]],
        backend_id: Any,
        profile_backend: Dict[str, Any],
    ) -> Tuple[str, str]:
        """Узел IP/hostname бекенда; одинаковые address объединяются в один узел."""
        bid = str(backend_id)
        if backend:
            address = str(backend.get("address") or "?")
            label = address
            if backend.get("enabled") is False:
                label += " disabled"
            node_id = f"B_{self._safe_id(address)}"
        else:
            label = f"backend {bid[:8]}"
            node_id = f"B_{self._safe_id(bid)}"
        return node_id, label

    @staticmethod
    def _safe_id(value: str) -> str:
        return re.sub(r"[^0-9A-Za-z_]", "_", value)[:48]

    @staticmethod
    def _escape_label(text: str) -> str:
        return (
            str(text)
            .replace("\\", "\\\\")
            .replace('"', "#quot;")
            .replace("\n", "<br/>")
            .replace("[", "(")
            .replace("]", ")")
        )

    # Цвета узлов: protection_mode + особые случаи (orphan)
    APP_NODE_CLASSES = {
        "ACTIVE_PREVENTION": ("pm_prevention", "fill:#2ecc71,stroke:#1e8449,color:#000"),
        "ACTIVE_DETECTION": ("pm_detection", "fill:#f1c40f,stroke:#b7950b,color:#000"),
        "PASSIVE": ("pm_passive", "fill:#e74c3c,stroke:#922b21,color:#fff"),
        # Профиль трафика без веб-приложения
        "ORPHAN_PROFILE": ("orphan_profile", "fill:#9b59b6,stroke:#6c3483,color:#fff"),
        # Веб-приложение без профиля трафика
        "ORPHAN_APP": ("orphan_app", "fill:#e67e22,stroke:#a04000,color:#fff"),
    }

    def build_flowchart_mermaid(self, graph: Dict[str, Any]) -> str:
        # Gateway -> VIP address -> VIP port -> App -> backend port -> backend IP
        # ELK лучше стыкует рёбра слева→справа (вход в начало фигуры, выход с конца).
        lines = [
            '%%{init: {"flowchart": {"defaultRenderer": "elk", "htmlLabels": true, '
            '"curve": "linear", "nodeSpacing": 40, "rankSpacing": 70}} }%%',
            "flowchart LR",
        ]
        for _key, (class_name, style) in self.APP_NODE_CLASSES.items():
            lines.append(f"  classDef {class_name} {style}")
        lines.append("  classDef gateway fill:#5dade2,stroke:#1a5276,color:#000")

        vip_ports = {
            k: n for k, n in (graph.get("port_nodes") or {}).items() if k.startswith("VP_")
        }
        backend_ports = {
            k: n for k, n in (graph.get("port_nodes") or {}).items() if k.startswith("BP_")
        }
        for node in (graph.get("gateway_nodes") or {}).values():
            lines.append(f'  {node["id"]}["{self._escape_label(node["label"])}"]')
            lines.append(f'  class {node["id"]} gateway')
        for node in (graph.get("vip_nodes") or {}).values():
            lines.append(f'  {node["id"]}["{self._escape_label(node["label"])}"]')

        vip_port_list = list(vip_ports.values())
        if vip_port_list:
            lines.append('  subgraph sg_vip_ports ["VIP PORT"]')
            lines.append("    direction LR")
            for node in vip_port_list:
                lines.append(f'    {node["id"]}["{self._escape_label(node["label"])}"]')
            lines.append("  end")

        app_nodes = list((graph.get("app_nodes") or {}).values())
        if app_nodes:
            lines.append('  subgraph sg_apps ["Web applications"]')
            lines.append("    direction LR")
            for node in app_nodes:
                lines.append(f'    {node["id"]}["{self._escape_label(node["label"])}"]')
                style_key = node.get("style_key") or node.get("protection_mode") or ""
                class_info = self.APP_NODE_CLASSES.get(style_key)
                if class_info:
                    lines.append(f'    class {node["id"]} {class_info[0]}')
            lines.append("  end")

        be_ports = list(backend_ports.values())
        be_ips = list((graph.get("backend_nodes") or {}).values())
        if be_ports or be_ips:
            lines.append('  subgraph sg_backends ["Backend PORT:IP"]')
            lines.append("    direction LR")
            for node in be_ports:
                lines.append(f'    {node["id"]}["{self._escape_label(node["label"])}"]')
            for node in be_ips:
                lines.append(f'    {node["id"]}["{self._escape_label(node["label"])}"]')
            lines.append("  end")

        edge_list = graph.get("edges") or []
        for item in edge_list:
            if len(item) == 3:
                src, dst, _color = item
            else:
                src, dst = item[0], item[1]
            lines.append(f"  {src} --> {dst}")
        for i, item in enumerate(edge_list):
            color = item[2] if len(item) == 3 else None
            if color:
                lines.append(f"  linkStyle {i} stroke:{color},stroke-width:3px")

        if len(edge_list) == 0 and len(lines) == 3 + len(self.APP_NODE_CLASSES):
            lines.append('  empty["No traffic flow data"]')
        return "\n".join(lines)

    # Толщина потоков в sankey-beta (третье поле source,target,value)
    SANKEY_LINK_WEIGHT = 100

    def build_sankey_mermaid(self, graph: Dict[str, Any]) -> str:
        """
        Sankey only: Web application -> Location -> backend listen port -> Backend IP.
        """
        lines = ["sankey-beta", ""]
        sankey_links = graph.get("sankey_links") or []
        weight = self.SANKEY_LINK_WEIGHT
        if not sankey_links:
            lines.append(f"no data,no data,{weight}")
            return "\n".join(lines)

        for src, dst in sankey_links:
            lines.append(
                f"{self._sankey_label(src)},{self._sankey_label(dst)},{weight}"
            )
        return "\n".join(lines)

    @staticmethod
    def _sankey_label(text: str) -> str:
        cleaned = (
            str(text)
            .replace("\n", " ")
            .replace(",", ";")
            .replace('"', "'")
            .strip()
        )
        return cleaned or "unnamed"
