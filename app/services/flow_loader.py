from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlmodel import Session, select

from app.models import Flow


def normalize_cell_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def normalize_header(value: object) -> str:
    return normalize_cell_value(value).replace("\n", " ").strip().lower()


def split_names(value: object) -> list[str]:
    text = normalize_cell_value(value)
    if not text:
        return []
    parts = re.split(r"[,\n\r]+", text)
    return [p.strip() for p in parts if p and p.strip()]


def find_sheet_name(*, sheet_names: list[str], candidates: list[str]) -> str | None:
    normalized = {name: normalize_header(name) for name in sheet_names}
    for candidate in candidates:
        target = normalize_header(candidate)
        for name, normalized_name in normalized.items():
            if target == normalized_name:
                return name
    for candidate in candidates:
        target = normalize_header(candidate)
        for name, normalized_name in normalized.items():
            if target in normalized_name:
                return name
    return None


def find_column_name(*, columns: list[str], token_groups: list[list[str]]) -> str | None:
    normalized = {name: normalize_header(name) for name in columns}
    for tokens in token_groups:
        token_list = [t.lower() for t in tokens]
        for name, normalized_name in normalized.items():
            if all(token in normalized_name for token in token_list):
                return name
    return None


def build_flow_key(*, flow_type: str, item_id: str, if_id: str) -> str:
    return f"{flow_type}|{item_id}|{if_id}".strip()


def load_flows_from_sheet(*, session: Session, df: pd.DataFrame, source_doc: str, source_sheet: str) -> int:
    columns = list(df.columns)
    col_type = find_column_name(columns=columns, token_groups=[["type"]])
    col_item_id = find_column_name(columns=columns, token_groups=[["항목", "id"], ["항목id"]])
    col_name = find_column_name(columns=columns, token_groups=[["인터페이스", "명"], ["인터페이스명"]])
    col_program = find_column_name(columns=columns, token_groups=[["프로그램", "명"], ["프로그램명"]])
    col_program_desc = find_column_name(columns=columns, token_groups=[["프로그램", "설명"]])
    col_tcode = find_column_name(columns=columns, token_groups=[["tcode"]])
    col_agg_table = find_column_name(columns=columns, token_groups=[["집계", "테이블"]])
    col_if_table = find_column_name(columns=columns, token_groups=[["i/f", "테이블"], ["if", "테이블"]])
    col_log_table = find_column_name(columns=columns, token_groups=[["log", "테이블"]])
    col_if_fm = find_column_name(columns=columns, token_groups=[["i/f", "fm"], ["if", "fm"]])
    col_system = find_column_name(columns=columns, token_groups=[["시스템"]])
    col_module = find_column_name(columns=columns, token_groups=[["모듈"]])
    col_if_id = find_column_name(columns=columns, token_groups=[["if", "id"]])
    col_aplan_if = find_column_name(columns=columns, token_groups=[["aplan", "i/f", "table"], ["aplan", "if", "table"]])
    col_aplan_stg = find_column_name(columns=columns, token_groups=[["aplan", "stg"], ["표준화"]])

    loaded = 0
    for row_idx, row in df.iterrows():
        flow_type = normalize_cell_value(row.get(col_type)) if col_type else ""
        item_id = normalize_cell_value(row.get(col_item_id)) if col_item_id else ""
        if_id = normalize_cell_value(row.get(col_if_id)) if col_if_id else ""
        if not flow_type or not item_id:
            continue

        flow_key = build_flow_key(flow_type=flow_type, item_id=item_id, if_id=if_id)
        name = normalize_cell_value(row.get(col_name)) if col_name else ""
        program_name = normalize_cell_value(row.get(col_program)) if col_program else ""
        program_desc = normalize_cell_value(row.get(col_program_desc)) if col_program_desc else ""
        tcode = normalize_cell_value(row.get(col_tcode)) if col_tcode else ""
        agg_table = normalize_cell_value(row.get(col_agg_table)) if col_agg_table else ""
        if_table = normalize_cell_value(row.get(col_if_table)) if col_if_table else ""
        log_table = normalize_cell_value(row.get(col_log_table)) if col_log_table else ""
        if_fm = normalize_cell_value(row.get(col_if_fm)) if col_if_fm else ""
        system = normalize_cell_value(row.get(col_system)) if col_system else ""
        module = normalize_cell_value(row.get(col_module)) if col_module else ""
        aplan_if_table = normalize_cell_value(row.get(col_aplan_if)) if col_aplan_if else ""
        aplan_stg_raw = normalize_cell_value(row.get(col_aplan_stg)) if col_aplan_stg else ""
        aplan_stg_list = split_names(aplan_stg_raw)
        aplan_stg_tables = ", ".join(aplan_stg_list)

        existing = session.exec(select(Flow).where(Flow.flow_key == flow_key)).first()
        flow_data = {
            "flow_key": flow_key,
            "flow_type": flow_type,
            "item_id": item_id,
            "if_id": if_id,
            "name": name,
            "program_desc": program_desc,
            "system": system,
            "module": module,
            "program_name": program_name,
            "tcode": tcode,
            "if_fm": if_fm,
            "agg_table": agg_table,
            "if_table": if_table,
            "log_table": log_table,
            "aplan_if_table": aplan_if_table,
            "aplan_stg_tables_raw": aplan_stg_raw,
            "aplan_stg_tables": aplan_stg_tables,
            "source_doc": source_doc,
            "source_sheet": source_sheet,
            "source_row": row_idx + 2,
        }

        if existing:
            for key, value in flow_data.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            session.add(existing)
        else:
            session.add(Flow(**flow_data))
        loaded += 1

    return loaded


def load_flows_from_file(*, session: Session, file_path: Path) -> int:
    if not file_path.exists():
        return 0
    excel = pd.ExcelFile(file_path)
    sheet = find_sheet_name(
        sheet_names=excel.sheet_names,
        candidates=["인터페이스", "interface", "flows", "flow"],
    )
    if not sheet:
        return 0

    df = pd.read_excel(excel, sheet_name=sheet, header=0, dtype=object)
    return load_flows_from_sheet(session=session, df=df, source_doc=file_path.name, source_sheet=sheet)
