from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from sqlmodel import Session, select

from app.models import IntegrationObject, IntegrationRelation


VIEW_MODES = {"business", "leader", "ops"}


def normalize_view_mode(view_mode: str | None) -> str:
    if view_mode in VIEW_MODES:
        return view_mode
    return "business"


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
