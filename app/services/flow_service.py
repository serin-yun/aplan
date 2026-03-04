from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select, or_

from app.models import Flow
from app.services.flow_loader import split_names


SOURCE_Y = 120
IF_Y = 260
APLAN_Y = 400
X0 = 150
X1 = 450
X2 = 750
X3 = 1050


def build_flow_key(*, flow_type: str, item_id: str, if_id: str) -> str:
    return f"{flow_type}|{item_id}|{if_id}".strip()


def parse_stg_tables(flow: Flow) -> list[str]:
    raw = flow.aplan_stg_tables_raw or ""
    parsed = split_names(raw)
    if parsed:
        return parsed
    return split_names(flow.aplan_stg_tables or "")


def flow_display_name(flow: Flow) -> str:
    item_id = flow.item_id or ""
    name = flow.name or ""
    if item_id and name:
        return f"[{item_id}] {name}"
    return name or item_id or flow.flow_key


def build_flow_summary_line(flow: Flow) -> str:
    stg_list = parse_stg_tables(flow)
    stg_label = stg_list[0] if stg_list else "표준화 결과"
    system = flow.system or "원천 시스템"
    name = flow.name or flow.flow_key
    return f"{system}에서 {name} 데이터를 APlan으로 전송하여 {stg_label}로 표준화합니다."


def build_flow_search_query(
    *,
    q: Optional[str],
    flow_type: Optional[str],
    system: Optional[str],
    module: Optional[str],
) -> list:
    filters = []
    if q:
        search = f"%{q}%"
        filters.append(
            or_(
                Flow.item_id.ilike(search),
                Flow.name.ilike(search),
                Flow.program_name.ilike(search),
                Flow.program_desc.ilike(search),
                Flow.tcode.ilike(search),
                Flow.if_id.ilike(search),
                Flow.if_fm.ilike(search),
                Flow.agg_table.ilike(search),
                Flow.if_table.ilike(search),
                Flow.log_table.ilike(search),
                Flow.aplan_if_table.ilike(search),
                Flow.aplan_stg_tables_raw.ilike(search),
            )
        )
    if flow_type:
        filters.append(Flow.flow_type == flow_type)
    if system:
        filters.append(Flow.system == system)
    if module:
        filters.append(Flow.module == module)
    return filters


def list_flows(
    *,
    session: Session,
    q: Optional[str],
    flow_type: Optional[str],
    system: Optional[str],
    module: Optional[str],
) -> list[Flow]:
    statement = select(Flow)
    for condition in build_flow_search_query(q=q, flow_type=flow_type, system=system, module=module):
        statement = statement.where(condition)
    statement = statement.order_by(Flow.item_id, Flow.name, Flow.flow_key)
    return session.exec(statement).all()


def get_flow_by_key(*, session: Session, flow_key: str) -> Flow | None:
    return session.exec(select(Flow).where(Flow.flow_key == flow_key)).first()


def build_flow_cards(flows: list[Flow]) -> list[dict]:
    cards = []
    for flow in flows:
        cards.append(
            {
                "flow_key": flow.flow_key,
                "display_name": flow_display_name(flow),
                "program_desc": flow.program_desc,
                "system": flow.system,
                "module": flow.module,
                "flow_type": flow.flow_type,
            }
        )
    return cards


def node_label(*, title: str, detail: str) -> str:
    detail_text = detail or "-"
    return f"<b>{title}</b>\\n<small>{detail_text}</small>"


def build_panel_data(*, flow: Flow) -> dict:
    return {
        "summary": build_flow_summary_line(flow),
        "execution": {
            "program": flow.program_name,
            "tcode": flow.tcode,
            "if_fm": flow.if_fm,
        },
        "data_objects": {
            "agg_table": flow.agg_table,
            "if_table": flow.if_table,
            "log_table": flow.log_table,
            "aplan_if_table": flow.aplan_if_table,
            "aplan_stg_tables": parse_stg_tables(flow),
        },
        "identifiers": {
            "flow_key": flow.flow_key,
            "if_id": flow.if_id,
        },
    }


def build_flow_diagram(*, flow: Flow) -> dict:
    stg_tables = parse_stg_tables(flow)
    panel = build_panel_data(flow=flow)

    nodes = []
    edges = []

    def add_node(node_id: str, label: str, x: int, y: int, kind: str, is_spine: bool) -> None:
        nodes.append(
            {
                "id": node_id,
                "label": label,
                "x": x,
                "y": y,
                "fixed": {"x": True, "y": True},
                "shape": "box",
                "shapeProperties": {"borderRadius": 10},
                "font": {"multi": "html", "size": 16},
                "widthConstraint": {"maximum": 240},
                "heightConstraint": {"minimum": 64},
                "is_spine": is_spine,
                "kind": kind,
            }
        )

    def add_edge(from_id: str, to_id: str, is_spine: bool) -> None:
        edges.append(
            {
                "from": from_id,
                "to": to_id,
                "arrows": "to",
                "width": 4 if is_spine else 1,
                "dashes": not is_spine,
            }
        )

    s0_id = "S0_SOURCE"
    s1_id = "S1_TRANSFER"
    s2_id = "S2_APLAN_IF"

    add_node(
        s0_id,
        node_label(title="원천 실행", detail=flow.system or flow.program_name or "-"),
        X0,
        SOURCE_Y,
        "source",
        True,
    )
    add_node(
        s1_id,
        node_label(title="전송 지점", detail=flow.if_fm or flow.if_id or "-"),
        X1,
        IF_Y,
        "transfer",
        True,
    )
    add_node(
        s2_id,
        node_label(title="APlan 수신", detail=flow.aplan_if_table or "-"),
        X2,
        APLAN_Y,
        "aplan_if",
        True,
    )

    add_edge(s0_id, s1_id, True)
    add_edge(s1_id, s2_id, True)

    if len(stg_tables) >= 3:
        s3_id = "S3_APLAN_STG_BUNDLE"
        add_node(
            s3_id,
            node_label(title="표준화 결과", detail=f"{len(stg_tables)}개"),
            X3,
            APLAN_Y,
            "stg_bundle",
            True,
        )
        add_edge(s2_id, s3_id, True)
    else:
        offsets = [0, 60]
        for idx, table in enumerate(stg_tables or ["-"]):
            s3_id = f"S3_APLAN_STG_{idx}"
            add_node(
                s3_id,
                node_label(title="표준화 결과", detail=table),
                X3,
                APLAN_Y + offsets[idx] if idx < len(offsets) else APLAN_Y,
                "stg",
                True,
            )
            add_edge(s2_id, s3_id, True)

    # Satellites
    s0_satellites = split_names(flow.agg_table)
    if s0_satellites:
        add_node(
            "SAT_AGG",
            node_label(title="집계 테이블", detail=", ".join(s0_satellites)),
            X0,
            SOURCE_Y - 90,
            "agg_table",
            False,
        )
        add_edge("SAT_AGG", s0_id, False)

    s1_satellites = []
    if flow.log_table:
        s1_satellites.append(("SAT_LOG", "LOG 테이블", flow.log_table))
    if flow.if_table:
        s1_satellites.append(("SAT_IF_TABLE", "I/F 테이블", flow.if_table))
    if flow.if_id:
        s1_satellites.append(("SAT_IF_ID", "IF ID", flow.if_id))

    y_offsets = [-90, 90, -180, 180]
    for idx, (node_id, title, detail) in enumerate(s1_satellites):
        y = IF_Y + y_offsets[idx] if idx < len(y_offsets) else IF_Y + 180
        add_node(
            node_id,
            node_label(title=title, detail=detail),
            X1,
            y,
            "transfer_satellite",
            False,
        )
        add_edge(node_id, s1_id, False)

    return {"nodes": nodes, "edges": edges, "panel": panel}
