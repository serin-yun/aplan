from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from sqlmodel import Session, select

from app.models import Flow, IntegrationObject, IntegrationRelation
from app.services.flow_loader import split_names


VIEW_MODES = {"business", "executive", "ops"}


def normalize_view_mode(view_mode: str | None) -> str:
    if view_mode in VIEW_MODES:
        return view_mode
    return "business"


def normalize_text(value: object | None) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text


def extract_domain_prefix(*, item_id: str) -> str:
    normalized = normalize_text(item_id).upper()
    if normalized.startswith("CP"):
        return "CP"
    if normalized.startswith("SP"):
        return "SP"
    if normalized.startswith("DP"):
        return "DP"
    return ""


def detect_stg_type(*, stg_name: str) -> str:
    normalized = normalize_text(stg_name).upper()
    if normalized.startswith("ALCDCM"):
        return "ALCDCM"
    if normalized.startswith("ALCDCA"):
        return "ALCDCA"
    return ""


def detect_update_only(*, stg_raw: str) -> bool:
    normalized = normalize_text(stg_raw).lower()
    if not normalized:
        return False
    if "update" in normalized and "only" in normalized:
        return True
    if "업데이트" in normalized and "only" in normalized:
        return True
    if "업데이트" in normalized and "전용" in normalized:
        return True
    return False


def build_lineage_graph(*, session: Session, view_mode: str = "business") -> dict:
    flows = session.exec(select(Flow)).all()
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    stg_to_interfaces: dict[str, set[str]] = defaultdict(set)
    system_counts: Counter[str] = Counter()
    prefix_counts: Counter[str] = Counter()
    stg_type_counts: Counter[str] = Counter()
    stg_update_only: set[str] = set()

    def ensure_node(*, node_id: str, payload: dict) -> None:
        if node_id in nodes:
            return
        nodes[node_id] = payload

    include_ops = view_mode == "ops"

    for flow in flows:
        system = normalize_text(flow.system) or "UNKNOWN"
        module = normalize_text(flow.module)
        system_label = f"{system} {module}".strip()
        system_id = f"system:{system}" if not include_ops else f"system:{flow.flow_key}"
        system_counts[system] += 1
        ensure_node(
            node_id=system_id,
            payload={
                "id": system_id,
                "label": system_label or system,
                "type": "system",
                "level": "summary",
                "system": system,
                "module": module,
                "flow_key": flow.flow_key if include_ops else "",
                "search_text": system.lower(),
            },
        )

        item_id = normalize_text(flow.item_id)
        if_id = normalize_text(flow.if_id)
        interface_name = normalize_text(flow.name) or flow.flow_key
        interface_label = f"{item_id} {interface_name}".strip() or interface_name
        interface_id = f"if:{flow.flow_key}"
        domain_prefix = extract_domain_prefix(item_id=item_id)
        if domain_prefix:
            prefix_counts[domain_prefix] += 1

        aplan_if_table = normalize_text(flow.aplan_if_table)
        stg_raw = normalize_text(flow.aplan_stg_tables or flow.aplan_stg_tables_raw)
        stg_list = split_names(stg_raw)
        update_only = detect_update_only(stg_raw=stg_raw)

        ensure_node(
            node_id=interface_id,
            payload={
                "id": interface_id,
                "label": interface_label,
                "type": "interface",
                "level": "interface",
                "flow_key": flow.flow_key,
                "system": system,
                "module": module,
                "item_id": item_id,
                "if_id": if_id,
                "interface_name": interface_name,
                "domain_prefix": domain_prefix,
                "program_name": normalize_text(flow.program_name),
                "program_desc": normalize_text(flow.program_desc),
                "tcode": normalize_text(flow.tcode),
                "if_fm": normalize_text(flow.if_fm),
                "agg_table": normalize_text(flow.agg_table),
                "if_table": normalize_text(flow.if_table),
                "log_table": normalize_text(flow.log_table),
                "aplan_if_table": aplan_if_table,
                "aplan_stg_tables": stg_list,
                "stg_type": "",
                "update_only": update_only,
                "search_text": " ".join(
                    filter(
                        None,
                        [
                            item_id,
                            interface_name,
                            if_id,
                            system,
                            module,
                            aplan_if_table,
                            stg_raw,
                            normalize_text(flow.program_name),
                            normalize_text(flow.tcode),
                            normalize_text(flow.if_fm),
                        ],
                    )
                ).lower(),
            },
        )

        edges.append(
            {
                "from": system_id,
                "to": interface_id,
                "edge_type": "system_to_interface",
            }
        )

        source_for_stg = interface_id

        if include_ops:
            program_name = normalize_text(flow.program_name)
            program_desc = normalize_text(flow.program_desc)
            agg_table = normalize_text(flow.agg_table)
            log_table = normalize_text(flow.log_table)
            if_fm = normalize_text(flow.if_fm)
            eai_id = normalize_text(flow.if_id)

            if program_name:
                program_id = f"program:{flow.flow_key}:{program_name}"
                ensure_node(
                    node_id=program_id,
                    payload={
                        "id": program_id,
                        "label": f"{program_name} {program_desc}".strip() or program_name,
                        "type": "program",
                        "level": "tech",
                        "flow_key": flow.flow_key,
                        "system": system,
                        "module": module,
                        "search_text": " ".join(filter(None, [program_name, program_desc])).lower(),
                    },
                )
                edges.append(
                    {
                        "from": interface_id,
                        "to": program_id,
                        "edge_type": "interface_to_program",
                    }
                )
                source_for_stg = program_id

            if agg_table:
                agg_id = f"agg:{flow.flow_key}:{agg_table}"
                ensure_node(
                    node_id=agg_id,
                    payload={
                        "id": agg_id,
                        "label": agg_table,
                        "type": "agg_table",
                        "level": "tech",
                        "flow_key": flow.flow_key,
                        "system": system,
                        "module": module,
                        "search_text": agg_table.lower(),
                    },
                )
                edges.append(
                    {
                        "from": source_for_stg,
                        "to": agg_id,
                        "edge_type": "program_to_agg",
                    }
                )
                source_for_stg = agg_id

            if log_table:
                log_id = f"log:{flow.flow_key}:{log_table}"
                ensure_node(
                    node_id=log_id,
                    payload={
                        "id": log_id,
                        "label": log_table,
                        "type": "log_table",
                        "level": "tech",
                        "flow_key": flow.flow_key,
                        "system": system,
                        "module": module,
                        "search_text": log_table.lower(),
                    },
                )
                edges.append(
                    {
                        "from": source_for_stg,
                        "to": log_id,
                        "edge_type": "agg_to_log",
                    }
                )
                source_for_stg = log_id

            if if_fm:
                fm_id = f"fm:{flow.flow_key}:{if_fm}"
                ensure_node(
                    node_id=fm_id,
                    payload={
                        "id": fm_id,
                        "label": if_fm,
                        "type": "fm",
                        "level": "tech",
                        "flow_key": flow.flow_key,
                        "system": system,
                        "module": module,
                        "search_text": if_fm.lower(),
                    },
                )
                edges.append(
                    {
                        "from": source_for_stg,
                        "to": fm_id,
                        "edge_type": "log_to_fm",
                    }
                )
                source_for_stg = fm_id

            if eai_id:
                eai_node_id = f"eai:{flow.flow_key}:{eai_id}"
                ensure_node(
                    node_id=eai_node_id,
                    payload={
                        "id": eai_node_id,
                        "label": f"{eai_id} EAI",
                        "type": "eai",
                        "level": "tech",
                        "flow_key": flow.flow_key,
                        "system": "EAI",
                        "module": module,
                        "search_text": eai_id.lower(),
                    },
                )
                edges.append(
                    {
                        "from": source_for_stg,
                        "to": eai_node_id,
                        "edge_type": "fm_to_eai",
                    }
                )
                source_for_stg = eai_node_id

        if aplan_if_table:
            aplan_if_id = (
                f"aplan_if:{flow.flow_key}:{aplan_if_table}"
                if include_ops
                else f"aplan_if:{aplan_if_table}"
            )
            ensure_node(
                node_id=aplan_if_id,
                payload={
                    "id": aplan_if_id,
                    "label": aplan_if_table,
                    "type": "aplan_if",
                    "level": "table",
                    "system": "APLAN",
                    "flow_key": flow.flow_key,
                    "search_text": aplan_if_table.lower(),
                },
            )
            edges.append(
                {
                    "from": interface_id,
                    "to": aplan_if_id,
                    "edge_type": "interface_to_if",
                }
            )
            source_for_stg = aplan_if_id

        for stg in stg_list:
            stg_type = detect_stg_type(stg_name=stg)
            stg_id = (
                f"aplan_stg:{flow.flow_key}:{stg}"
                if include_ops
                else f"aplan_stg:{stg}"
            )
            if stg_type:
                stg_type_counts[stg_type] += 1
            if update_only:
                stg_update_only.add(stg_id)
            ensure_node(
                node_id=stg_id,
                payload={
                    "id": stg_id,
                    "label": stg,
                    "type": "aplan_stg",
                    "level": "table",
                    "system": "APLAN",
                    "stg_type": stg_type,
                    "update_only": update_only,
                    "flow_key": flow.flow_key,
                    "search_text": " ".join(filter(None, [stg, stg_type])).lower(),
                },
            )
            edges.append(
                {
                    "from": source_for_stg,
                    "to": stg_id,
                    "edge_type": "to_stg",
                }
            )
            stg_to_interfaces[stg_id].add(interface_id)

    stg_fan_in = {key: len(values) for key, values in stg_to_interfaces.items()}
    stg_interfaces = {key: sorted(values) for key, values in stg_to_interfaces.items()}

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "stats": {
            "total_interfaces": sum(1 for node in nodes.values() if node["type"] == "interface"),
            "total_systems": len(system_counts),
            "unique_target_stg": sum(1 for node in nodes.values() if node["type"] == "aplan_stg"),
            "by_system": dict(system_counts),
            "by_prefix": dict(prefix_counts),
            "by_stg_type": dict(stg_type_counts),
            "update_only_stg": len(stg_update_only),
        },
        "meta": {
            "stg_fan_in": stg_fan_in,
            "stg_interfaces": stg_interfaces,
        },
    }


def build_exec_summary(*, session: Session) -> dict:
    graph = build_lineage_graph(session=session)
    flows = session.exec(select(Flow)).all()

    stg_fan_in = graph["meta"]["stg_fan_in"]
    stg_nodes = [node for node in graph["nodes"] if node["type"] == "aplan_stg"]
    update_only_stg = [node["label"] for node in stg_nodes if node.get("update_only")]

    top_fan_in = sorted(
        ((node["label"], stg_fan_in.get(node["id"], 0)) for node in stg_nodes),
        key=lambda item: (-item[1], item[0]),
    )[:5]

    missing_log = [
        flow for flow in flows if not normalize_text(flow.log_table)
    ]
    missing_if = [
        flow for flow in flows if not normalize_text(flow.if_table)
    ]

    detail_rows = []
    for flow in flows:
        stg_raw = normalize_text(flow.aplan_stg_tables or flow.aplan_stg_tables_raw)
        stg_list = split_names(stg_raw)
        fan_in = 0
        for stg in stg_list:
            stg_id = f"aplan_stg:{stg}"
            fan_in = max(fan_in, stg_fan_in.get(stg_id, 0))
        detail_rows.append(
            {
                "item_id": normalize_text(flow.item_id),
                "interface_name": normalize_text(flow.name) or flow.flow_key,
                "system": normalize_text(flow.system),
                "module": normalize_text(flow.module),
                "aplan_if_table": normalize_text(flow.aplan_if_table),
                "aplan_stg_table": ", ".join(stg_list),
                "flow_type": normalize_text(flow.flow_type),
                "fan_in": fan_in,
                "if_id": normalize_text(flow.if_id),
            }
        )

    summary_edges: Counter[tuple[str, str]] = Counter()
    for flow in flows:
        system = normalize_text(flow.system) or "UNKNOWN"
        stg_raw = normalize_text(flow.aplan_stg_tables or flow.aplan_stg_tables_raw)
        stg_list = split_names(stg_raw)
        for stg in stg_list:
            summary_edges[(system, stg)] += 1

    summary_flow = {
        "nodes": sorted({system for system, _ in summary_edges.keys()} | {stg for _, stg in summary_edges.keys()}),
        "edges": [
            {"from": system, "to": stg, "count": count}
            for (system, stg), count in summary_edges.items()
        ],
    }

    return {
        "kpi": {
            "total_interfaces": graph["stats"]["total_interfaces"],
            "total_systems": graph["stats"]["total_systems"],
            "unique_target_stg": graph["stats"]["unique_target_stg"],
            "failures": 0,
        },
        "distribution": {
            "by_system": graph["stats"]["by_system"],
            "by_prefix": graph["stats"]["by_prefix"],
            "by_stg_type": graph["stats"]["by_stg_type"],
        },
        "risks": {
            "top_fan_in": [{"stg": name, "count": count} for name, count in top_fan_in],
            "update_only": update_only_stg[:5],
            "missing_log": [normalize_text(flow.name) or flow.flow_key for flow in missing_log[:5]],
            "missing_if": [normalize_text(flow.name) or flow.flow_key for flow in missing_if[:5]],
        },
        "summary_flow": summary_flow,
        "detail_rows": detail_rows,
    }


def split_flow_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [tag.strip() for tag in tags.split(",") if tag and tag.strip()]


def pick_program_description(objects: Iterable[IntegrationObject]) -> str:
    for obj in objects:
        if obj.object_type == "JOB" and obj.description:
            return obj.description
    for obj in objects:
        if obj.layer == "Legacy" and obj.description:
            return obj.description
    for obj in objects:
        if obj.description:
            return obj.description
    return ""


def pick_flow_type(flow_key: str) -> str:
    lowered = flow_key.lower()
    if "outbound" in lowered:
        return "Outbound"
    if "inbound" in lowered:
        return "Inbound"
    return ""


def choose_most_common(values: Iterable[str | None]) -> str:
    normalized = [value.strip() for value in values if value and value.strip()]
    if not normalized:
        return ""
    return Counter(normalized).most_common(1)[0][0]


def collect_unique_names(objects: Iterable[IntegrationObject]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for obj in objects:
        name = (obj.name or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ordered


def build_ops_details(objects: list[IntegrationObject]) -> dict:
    legacy_jobs = [obj for obj in objects if obj.layer == "Legacy" and obj.object_type == "JOB"]
    legacy_tables = [obj for obj in objects if obj.layer == "Legacy" and obj.object_type == "TABLE"]
    aplan_if_tables = [obj for obj in objects if obj.layer == "In" and obj.system_type == "APLAN"]
    stg_tables = [obj for obj in objects if obj.layer == "Staging" and obj.system_type == "APLAN"]

    return {
        "legacy_programs": collect_unique_names(legacy_jobs),
        "legacy_tables": collect_unique_names(legacy_tables),
        "aplan_if_tables": collect_unique_names(aplan_if_tables),
        "stg_tables": collect_unique_names(stg_tables),
    }


def build_flow_cards(*, session: Session) -> tuple[list[dict], str | None]:
    flows = session.exec(select(Flow)).all()
    if flows:
        cards = []
        for flow in flows:
            cards.append(
                {
                    "flow_key": flow.flow_key,
                    "interface_name": flow.name or flow.flow_key,
                    "system_type": flow.system or "",
                    "module": flow.module or "",
                    "flow_type": flow.flow_type or "",
                    "program_description": flow.program_desc or "",
                    "ops_details": {
                        "legacy_programs": [flow.program_name] if flow.program_name else [],
                        "legacy_tables": split_names(flow.agg_table),
                        "aplan_if_tables": split_names(flow.aplan_if_table),
                        "stg_tables": split_names(flow.aplan_stg_tables or flow.aplan_stg_tables_raw),
                    },
                    "min_source_row": flow.source_row,
                }
            )
        cards.sort(key=lambda item: (item["min_source_row"] or 999999, item["flow_key"]))
        primary_flow_key = cards[0]["flow_key"] if cards else None
        return cards, primary_flow_key

    statement = select(IntegrationObject).where(IntegrationObject.status == "ACTIVE")
    objects = session.exec(statement).all()

    flows: dict[str, list[IntegrationObject]] = defaultdict(list)
    for obj in objects:
        for tag in split_flow_tags(obj.tags):
            flows[tag].append(obj)

    flow_cards: list[dict] = []
    primary_flow_key: str | None = None
    primary_source_row = None

    for flow_key, flow_objects in flows.items():
        min_source_row = min(
            [obj.source_row for obj in flow_objects if obj.source_row is not None],
            default=None,
        )
        if min_source_row is not None and (primary_source_row is None or min_source_row < primary_source_row):
            primary_source_row = min_source_row
            primary_flow_key = flow_key

        flow_cards.append(
            {
                "flow_key": flow_key,
                "interface_name": flow_key,
                "system_type": choose_most_common(obj.system_type for obj in flow_objects),
                "module": choose_most_common(obj.module for obj in flow_objects),
                "flow_type": pick_flow_type(flow_key),
                "program_description": pick_program_description(flow_objects),
                "ops_details": build_ops_details(flow_objects),
                "min_source_row": min_source_row,
            }
        )

    def sort_key(card: dict) -> tuple:
        is_primary = primary_flow_key and card["flow_key"] == primary_flow_key
        return (0 if is_primary else 1, card["min_source_row"] or 999999, card["flow_key"])

    flow_cards.sort(key=sort_key)
    return flow_cards, primary_flow_key


def build_cluster_key(*, obj: IntegrationObject) -> str:
    module = (obj.module or "").strip()
    if module:
        return f"{obj.system_type}:{module}"
    return obj.system_type or "UNKNOWN"


def build_cluster_label(*, cluster_key: str, count: int) -> str:
    if ":" in cluster_key:
        system, module = cluster_key.split(":", 1)
        return f"{system} - {module} ({count})"
    return f"{cluster_key} ({count})"


def build_cluster_network(*, session: Session, max_clusters: int = 30) -> dict:
    objects = session.exec(select(IntegrationObject).where(IntegrationObject.status == "ACTIVE")).all()
    relations = session.exec(select(IntegrationRelation).where(IntegrationRelation.status == "ACTIVE")).all()

    cluster_counts: Counter[str] = Counter()
    object_cluster: dict[int, str] = {}

    for obj in objects:
        cluster_key = build_cluster_key(obj=obj)
        object_cluster[obj.id] = cluster_key
        cluster_counts[cluster_key] += 1

    cluster_keys = [key for key, _ in cluster_counts.most_common(max_clusters)]
    cluster_set = set(cluster_keys)

    edges_count: Counter[tuple[str, str]] = Counter()
    for rel in relations:
        from_cluster = object_cluster.get(rel.from_object_id)
        to_cluster = object_cluster.get(rel.to_object_id)
        if not from_cluster or not to_cluster:
            continue
        if from_cluster == to_cluster:
            continue
        if from_cluster not in cluster_set or to_cluster not in cluster_set:
            continue
        edge_key = (from_cluster, to_cluster)
        edges_count[edge_key] += 1

    nodes = [
        {
            "id": key,
            "label": build_cluster_label(cluster_key=key, count=cluster_counts[key]),
            "value": cluster_counts[key],
            "count": cluster_counts[key],
        }
        for key in cluster_keys
    ]
    edges = [
        {
            "from": from_key,
            "to": to_key,
            "value": weight,
            "width": min(8, 1 + weight / 3),
        }
        for (from_key, to_key), weight in edges_count.items()
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_clusters": len(nodes),
            "total_edges": len(edges),
            "total_objects": len(objects),
        },
    }
