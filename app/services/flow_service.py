from __future__ import annotations

from collections import Counter, defaultdict

from sqlmodel import Session, select

from app.models import IntegrationObject
from app.services.overview_service import split_flow_tags


def parse_flow_key_parts(flow_key: str) -> dict:
    parts = [part.strip() for part in flow_key.split("|") if part and part.strip()]
    if len(parts) >= 3:
        return {"flow_type": parts[0], "item_id": parts[1], "if_id": parts[2]}
    if len(parts) == 2:
        return {"flow_type": parts[0], "item_id": parts[1], "if_id": ""}
    if len(parts) == 1:
        return {"flow_type": "", "item_id": parts[0], "if_id": ""}
    return {"flow_type": "", "item_id": "", "if_id": ""}


def choose_most_common(values: list[str]) -> str:
    filtered = [value.strip() for value in values if value and value.strip()]
    if not filtered:
        return ""
    return Counter(filtered).most_common(1)[0][0]


def collect_unique_names(objects: list[IntegrationObject]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for obj in objects:
        name = (obj.name or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ordered


def pick_program_description(objects: list[IntegrationObject]) -> str:
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


def detect_transfer_tables(objects: list[IntegrationObject]) -> list[IntegrationObject]:
    transfer_candidates = []
    for obj in objects:
        if obj.layer != "Legacy" or obj.object_type != "TABLE":
            continue
        name = (obj.name or "").upper()
        description = (obj.description or "").upper()
        if "IF" in name or "I/F" in name or "LOG" in name or "IF" in description or "LOG" in description:
            transfer_candidates.append(obj)
    return transfer_candidates


def build_flow_groups(objects: list[IntegrationObject]) -> dict:
    legacy_jobs = [obj for obj in objects if obj.layer == "Legacy" and obj.object_type == "JOB"]
    legacy_tables = [obj for obj in objects if obj.layer == "Legacy" and obj.object_type == "TABLE"]
    transfer_tables = detect_transfer_tables(legacy_tables)
    source_tables = [obj for obj in legacy_tables if obj not in transfer_tables]
    log_tables = [obj for obj in legacy_tables if "LOG" in (obj.name or "").upper()]
    aplan_if_tables = [obj for obj in objects if obj.layer == "In" and obj.system_type == "APLAN"]
    stg_tables = [obj for obj in objects if obj.layer == "Staging" and obj.system_type == "APLAN"]

    return {
        "legacy_jobs": legacy_jobs,
        "legacy_tables": legacy_tables,
        "source_tables": source_tables,
        "transfer_tables": transfer_tables,
        "log_tables": log_tables,
        "aplan_if_tables": aplan_if_tables,
        "stg_tables": stg_tables,
    }


def build_flow_summary(*, flow_key: str, objects: list[IntegrationObject]) -> dict:
    parts = parse_flow_key_parts(flow_key)
    system_candidates = [obj.system_type for obj in objects if obj.layer == "Legacy"] or [obj.system_type for obj in objects]
    source_system = choose_most_common(system_candidates)
    module = choose_most_common([obj.module for obj in objects if obj.module])
    program_description = pick_program_description(objects)

    groups = build_flow_groups(objects)
    stg_tables = collect_unique_names(groups["stg_tables"])
    legacy_programs = collect_unique_names(groups["legacy_jobs"])
    transfer_tables = collect_unique_names(groups["transfer_tables"])
    aplan_if_tables = collect_unique_names(groups["aplan_if_tables"])
    legacy_tables = collect_unique_names(groups["legacy_tables"])
    log_tables = collect_unique_names(groups["log_tables"])

    stg_label = stg_tables[0] if stg_tables else "표준화 테이블"
    if source_system:
        summary_line = f"{source_system}에서 {flow_key} 데이터를 APlan으로 전송하여 {stg_label}로 표준화합니다."
    else:
        summary_line = f"{flow_key} 데이터를 APlan으로 전송하여 {stg_label}로 표준화합니다."

    stages = [
        {
            "title": "원천(Source)",
            "description": f"{source_system or '원천 시스템'}에서 데이터를 생성합니다.",
            "items": legacy_programs + collect_unique_names(groups["source_tables"]),
        },
        {
            "title": "전송(Transfer)",
            "description": "중계/전송 구간을 통해 데이터를 전달합니다.",
            "items": transfer_tables or log_tables,
        },
        {
            "title": "APlan 수신(Landing)",
            "description": "APlan I/F 테이블로 수신합니다.",
            "items": aplan_if_tables,
        },
        {
            "title": "표준화(Standardize)",
            "description": "STG 테이블로 표준화합니다.",
            "items": stg_tables,
        },
    ]

    return {
        "flow_key": flow_key,
        "interface_name": flow_key,
        "program_description": program_description,
        "summary_line": summary_line,
        "module": module,
        "system_type": source_system,
        "flow_type": parts["flow_type"],
        "item_id": parts["item_id"],
        "if_id": parts["if_id"],
        "stg_tables": stg_tables,
        "stages": stages,
        "ops_details": {
            "execution": {
                "programs": legacy_programs,
                "transfer_tables": transfer_tables,
            },
            "data_objects": {
                "legacy_tables": legacy_tables,
                "aplan_if_tables": aplan_if_tables,
                "stg_tables": stg_tables,
            },
            "logs": {
                "log_tables": log_tables,
            },
        },
    }


def collect_flows(*, session: Session) -> dict[str, list[IntegrationObject]]:
    objects = session.exec(select(IntegrationObject).where(IntegrationObject.status == "ACTIVE")).all()
    flows: dict[str, list[IntegrationObject]] = defaultdict(list)
    for obj in objects:
        for tag in split_flow_tags(obj.tags):
            flows[tag].append(obj)
    return flows


def build_flow_index(*, session: Session) -> dict:
    flows = collect_flows(session=session)
    primary_flow_key: str | None = None
    primary_source_row = None

    cards = []
    for flow_key, objects in flows.items():
        min_source_row = min(
            [obj.source_row for obj in objects if obj.source_row is not None],
            default=None,
        )
        if min_source_row is not None and (primary_source_row is None or min_source_row < primary_source_row):
            primary_source_row = min_source_row
            primary_flow_key = flow_key

        summary = build_flow_summary(flow_key=flow_key, objects=objects)
        cards.append(
            {
                "flow_key": flow_key,
                "interface_name": summary["interface_name"],
                "program_description": summary["program_description"],
                "system_type": summary["system_type"],
                "module": summary["module"],
                "stg_tables": summary["stg_tables"],
                "min_source_row": min_source_row,
            }
        )

    def sort_key(card: dict) -> tuple:
        is_primary = primary_flow_key and card["flow_key"] == primary_flow_key
        return (0 if is_primary else 1, card["min_source_row"] or 999999, card["flow_key"])

    cards.sort(key=sort_key)
    return {"cards": cards, "primary_flow_key": primary_flow_key}


def filter_flow_cards(*, cards: list[dict], q: str | None, system_type: str | None, module: str | None) -> list[dict]:
    filtered = cards
    if q:
        lowered = q.strip().lower()
        filtered = [
            card
            for card in filtered
            if lowered in (card["flow_key"] or "").lower()
            or lowered in (card["interface_name"] or "").lower()
            or lowered in (card["program_description"] or "").lower()
            or any(lowered in table.lower() for table in card.get("stg_tables") or [])
        ]
    if system_type:
        filtered = [card for card in filtered if (card.get("system_type") or "").lower() == system_type.lower()]
    if module:
        filtered = [card for card in filtered if (card.get("module") or "").lower() == module.lower()]
    return filtered


