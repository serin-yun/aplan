"""
파일 업로드 라우터

엑셀 파일 업로드 및 검증 기능 제공
"""

import pandas as pd
import logging
import io
import re
import tempfile
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.database import get_session, engine, init_db
from app.models import IntegrationObject, IntegrationRelation
from load_mapping import load_objects, load_relations

router = APIRouter(prefix="/upload", tags=["upload"])

# 로깅 설정
logger = logging.getLogger(__name__)

OBJECTS_COLUMNS = [
    "object_key",
    "name",
    "system_type",
    "object_type",
    "layer",
    "description",
    "owner_team",
    "owner",
    "module",
    "status",
    "tags",
    "environment",
    "source_doc",
    "source_sheet",
    "source_row",
]

RELATIONS_COLUMNS = [
    "from_key",
    "to_key",
    "relation_type",
    "description",
    "status",
    "source_doc",
    "source_sheet",
    "source_row",
]

INTERFACE_STAGE_DEFS = [
    {
        "name": "프로그램명",
        "object_type": "JOB",
        "layer": "Legacy",
        "system_source": "row",
    },
    {
        "name": "집계테이블",
        "object_type": "TABLE",
        "layer": "Legacy",
        "system_source": "row",
    },
    {
        "name": "I/F테이블",
        "object_type": "TABLE",
        "layer": "Legacy",
        "system_source": "row",
    },
    {
        "name": "LOG테이블",
        "object_type": "TABLE",
        "layer": "Legacy",
        "system_source": "row",
    },
    {
        "name": "Aplan I/F Table",
        "object_type": "TABLE",
        "layer": "In",
        "system_source": "APLAN",
    },
    {
        "name": "Aplan STG Table(표준화)",
        "object_type": "TABLE",
        "layer": "Staging",
        "system_source": "APLAN",
    },
]

# 템플릿 디렉토리 설정
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


def validate_excel_file(file: UploadFile) -> list[str]:
    """
    엑셀 파일 검증
    
    Returns:
        list[str]: 오류 메시지 리스트 (빈 리스트면 검증 통과)
    """
    errors = []
    
    # 파일명 검증
    if not file.filename.endswith('.xlsx'):
        errors.append("엑셀 파일(.xlsx)만 업로드 가능합니다.")
    
    # 파일 크기 검증 (10MB 제한)
    if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
        file.file.seek(0, 2)  # 파일 끝으로 이동
        size = file.file.tell()
        file.file.seek(0)  # 파일 시작으로 복귀
        
        if size > 10 * 1024 * 1024:  # 10MB
            errors.append("파일 크기는 10MB 이하여야 합니다.")
    
    return errors


def validate_excel_structure(file_path: Path) -> tuple[bool, list[str], dict]:
    """
    엑셀 파일 구조 검증
    
    Returns:
        tuple[bool, list[str], dict]: (성공 여부, 오류 메시지 리스트, 검증 결과 딕셔너리)
    """
    errors = []
    validation_result = {
        "has_objects_sheet": False,
        "has_relations_sheet": False,
        "objects_columns": [],
        "relations_columns": [],
        "objects_count": 0,
        "relations_count": 0,
        "missing_required_columns": [],
        "invalid_keys": []
    }
    
    excel_file = None
    try:
        # 시트 존재 확인
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        if 'objects' not in sheet_names:
            errors.append("'objects' 시트가 없습니다.")
        else:
            validation_result["has_objects_sheet"] = True
            df_objects = pd.read_excel(excel_file, sheet_name='objects')
            validation_result["objects_columns"] = list(df_objects.columns)
            validation_result["objects_count"] = len(df_objects)
            
            # 필수 컬럼 확인
            required_columns = ['object_key', 'name', 'system_type', 'object_type', 'layer']
            missing = [col for col in required_columns if col not in df_objects.columns]
            if missing:
                errors.append(f"objects 시트에 필수 컬럼이 없습니다: {missing}")
                validation_result["missing_required_columns"].extend(missing)
            
            # object_key 중복 확인
            if 'object_key' in df_objects.columns:
                duplicates = df_objects[df_objects['object_key'].duplicated()]
                if len(duplicates) > 0:
                    dup_keys = duplicates['object_key'].tolist()
                    errors.append(f"object_key 중복: {dup_keys[:5]}")
                    validation_result["invalid_keys"].extend(dup_keys[:5])
        
        if 'relations' not in sheet_names:
            errors.append("'relations' 시트가 없습니다.")
        else:
            validation_result["has_relations_sheet"] = True
            df_relations = pd.read_excel(excel_file, sheet_name='relations')
            validation_result["relations_columns"] = list(df_relations.columns)
            validation_result["relations_count"] = len(df_relations)
            
            # 필수 컬럼 확인
            required_columns = ['from_key', 'to_key']
            missing = [col for col in required_columns if col not in df_relations.columns]
            if missing:
                errors.append(f"relations 시트에 필수 컬럼이 없습니다: {missing}")
                validation_result["missing_required_columns"].extend(missing)
        
    except Exception as e:
        errors.append(f"엑셀 파일 읽기 오류: {str(e)}")
    finally:
        if excel_file is not None:
            excel_file.close()
    
    return len(errors) == 0, errors, validation_result


def ensure_mapping_schema(*, df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    extra_columns = [column for column in df.columns if column not in columns]
    return df[columns + extra_columns]


def write_mapping_excel(*, df_objects: pd.DataFrame, df_relations: pd.DataFrame, output_path: Path) -> None:
    temp_path = output_path.with_suffix(".tmp.xlsx")
    with pd.ExcelWriter(temp_path, engine="openpyxl") as writer:
        df_objects.to_excel(writer, sheet_name="objects", index=False)
        df_relations.to_excel(writer, sheet_name="relations", index=False)
    temp_path.replace(output_path)


def normalize_header(value: object) -> str:
    return normalize_cell_value(value).replace("\n", " ").strip()


def find_sheet_name(*, sheet_names: list[str], candidates: list[str]) -> str | None:
    normalized = {name: normalize_header(name).lower() for name in sheet_names}
    for candidate in candidates:
        target = normalize_header(candidate).lower()
        for name, normalized_name in normalized.items():
            if target == normalized_name:
                return name
    for candidate in candidates:
        target = normalize_header(candidate).lower()
        for name, normalized_name in normalized.items():
            if target in normalized_name:
                return name
    return None


def find_column_name(*, columns: list[str], token_groups: list[list[str]]) -> str | None:
    normalized = {name: normalize_header(name).lower() for name in columns}
    for tokens in token_groups:
        token_list = [t.lower() for t in tokens]
        for name, normalized_name in normalized.items():
            if all(token in normalized_name for token in token_list):
                return name
    return None


def build_mapping_from_interface_file(*, interface_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    interface_xls = None
    try:
        interface_xls = pd.ExcelFile(interface_path)
        interface_sheet = find_sheet_name(
            sheet_names=interface_xls.sheet_names,
            candidates=["인터페이스", "interface"],
        )
        if interface_sheet is None:
            raise ValueError("Interface.xlsx에 '인터페이스' 시트를 찾을 수 없습니다.")

        owner_sheet = find_sheet_name(
            sheet_names=interface_xls.sheet_names,
            candidates=["담당자", "owner"],
        )

        df_interface = pd.read_excel(interface_xls, sheet_name=interface_sheet, header=0, dtype=object)
        owner_by_module: dict[str, str] = {}
        if owner_sheet:
            df_owner = pd.read_excel(interface_xls, sheet_name=owner_sheet, header=0, dtype=object)
            owner_module_col = find_column_name(columns=list(df_owner.columns), token_groups=[["모듈"]])
            owner_name_col = find_column_name(columns=list(df_owner.columns), token_groups=[["담당자"]])
            if owner_module_col and owner_name_col:
                for _, row in df_owner.iterrows():
                    module_name = normalize_cell_value(row.get(owner_module_col))
                    owner_name = normalize_cell_value(row.get(owner_name_col))
                    if module_name and owner_name:
                        owner_by_module[module_name] = owner_name

        columns = list(df_interface.columns)
        type_col = find_column_name(columns=columns, token_groups=[["type"]])
        item_col = find_column_name(columns=columns, token_groups=[["항목", "id"], ["항목id"]])
        interface_col = find_column_name(columns=columns, token_groups=[["인터페이스", "명"], ["인터페이스명"]])
        program_col = find_column_name(columns=columns, token_groups=[["프로그램", "명"], ["프로그램명"]])
        program_desc_col = find_column_name(columns=columns, token_groups=[["프로그램", "설명"]])
        system_col = find_column_name(columns=columns, token_groups=[["시스템"]])
        module_col = find_column_name(columns=columns, token_groups=[["모듈"]])

        stage_column_map: dict[str, str] = {}
        for stage in INTERFACE_STAGE_DEFS:
            col_name = find_column_name(columns=columns, token_groups=[[stage["name"]]])
            if col_name:
                stage_column_map[stage["name"]] = col_name

        objects_by_key: dict[str, dict] = {}
        flow_sequences: list[tuple[str, list[str]]] = []
        relations_records: list[dict] = []

        for row_idx, row in df_interface.iterrows():
            row_type = normalize_cell_value(row.get(type_col)) if type_col else ""
            if not row_type:
                continue
            direction = "inbound" if "inbound" in row_type.lower() else "outbound" if "outbound" in row_type.lower() else ""
            if not direction:
                continue

            item_id = normalize_cell_value(row.get(item_col)) if item_col else ""
            interface_name = normalize_cell_value(row.get(interface_col)) if interface_col else ""
            flow_key = " ".join([p for p in [item_id, interface_name] if p]).strip()
            if not flow_key:
                flow_key = normalize_cell_value(row.get("IF ID")) if "IF ID" in columns else f"ROW_{row_idx + 2}"

            program_desc = normalize_cell_value(row.get(program_desc_col)) if program_desc_col else ""
            module_value = normalize_cell_value(row.get(module_col)) if module_col else ""
            owner_value = owner_by_module.get(module_value) if module_value else None
            system_value = normalize_cell_value(row.get(system_col)).upper() if system_col else ""

            stage_keys: list[list[str]] = []
            ordered_object_keys: list[str] = []

            for stage in INTERFACE_STAGE_DEFS:
                col_name = stage_column_map.get(stage["name"])
                if not col_name:
                    continue
                raw_value = row.get(col_name)
                values = split_names(raw_value)
                if not values:
                    continue

                system_type = system_value if stage["system_source"] == "row" else stage["system_source"]
                if not system_type:
                    system_type = "UNKNOWN"

                current_keys: list[str] = []
                for value in values:
                    object_key = make_object_key(system_type, value)
                    current_keys.append(object_key)
                    ordered_object_keys.append(object_key)

                    description = f"[Interface] {flow_key}"
                    if program_desc:
                        description = f"{description} / {program_desc}"
                    if stage["layer"] in ["In", "Staging"]:
                        description = f"{description} ({stage['name']})"

                    upsert_object_record(
                        objects_by_key=objects_by_key,
                        object_key=object_key,
                        tags=flow_key,
                        record={
                            "object_key": object_key,
                            "name": value,
                            "system_type": system_type,
                            "object_type": stage["object_type"],
                            "layer": stage["layer"],
                            "description": description,
                            "owner_team": None,
                            "owner": owner_value,
                            "module": module_value or None,
                            "status": "ACTIVE",
                            "tags": flow_key,
                            "environment": "PRD",
                            "source_doc": interface_path.name,
                            "source_sheet": interface_sheet,
                            "source_row": row_idx + 2,
                        },
                    )

                stage_keys.append(current_keys)

            if len(stage_keys) < 2:
                continue

            if direction == "outbound":
                stage_keys = list(reversed(stage_keys))

            for current_keys, next_keys in zip(stage_keys, stage_keys[1:]):
                for from_key in current_keys:
                    for to_key in next_keys:
                        relations_records.append(
                            {
                                "from_key": from_key,
                                "to_key": to_key,
                                "relation_type": "FLOWS_TO",
                                "description": f"[Interface] {flow_key}",
                                "status": "ACTIVE",
                            }
                        )

            flow_sequences.append((flow_key, ordered_object_keys))

        # objects: 등장 순서 유지
        ordered_keys: list[str] = []
        seen = set()
        for _, seq in flow_sequences:
            for key in seq:
                if key in seen:
                    continue
                seen.add(key)
                ordered_keys.append(key)
        for key in objects_by_key.keys():
            if key in seen:
                continue
            ordered_keys.append(key)

        df_objects = pd.DataFrame([objects_by_key[key] for key in ordered_keys])
        df_relations = pd.DataFrame(relations_records)
        return df_objects, df_relations

    finally:
        if interface_xls is not None:
            interface_xls.close()


@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def upload_page(request: Request):
    """파일 업로드 페이지"""
    # 현재 파일 존재 여부 확인
    mapping_file = Path("mapping.xlsx")
    file_exists = mapping_file.exists()
    
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "file_exists": file_exists
        }
    )


@router.post("/validate", response_class=JSONResponse)
async def validate_file(
    file: UploadFile = File(...)
):
    """
    파일 업로드 전 검증 (클라이언트 사이드 검증)
    """
    # 파일 검증
    errors = validate_excel_file(file)
    
    if errors:
        return JSONResponse(
            {"success": False, "errors": errors},
            status_code=400
        )
    
    # 임시 파일로 저장하여 구조 검증
    temp_path = Path(f"temp_{file.filename}")
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        success, validation_errors, validation_result = validate_excel_structure(temp_path)
        
        # 임시 파일 삭제
        temp_path.unlink()
        
        if success:
            return JSONResponse({
                "success": True,
                "message": "파일 검증 성공",
                "validation": validation_result
            })
        else:
            return JSONResponse({
                "success": False,
                "errors": validation_errors,
                "validation": validation_result
            }, status_code=400)
            
    except Exception as e:
        # 임시 파일 정리
        if temp_path.exists():
            temp_path.unlink()
        
        return JSONResponse(
            {"success": False, "errors": [f"파일 처리 오류: {str(e)}"]},
            status_code=500
        )


@router.post("", response_class=JSONResponse)
async def upload_file(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """
    엑셀 파일 업로드 및 데이터베이스 로딩
    """
    # 엑셀 파일 검증
    if not file.filename.endswith('.xlsx'):
        return JSONResponse(
            {"success": False, "errors": ["엑셀 파일(.xlsx)만 업로드 가능합니다."]},
            status_code=400
        )
    
    # 파일 저장
    mapping_path = Path("mapping.xlsx")
    try:
        with open(mapping_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        return JSONResponse(
            {"success": False, "errors": [f"파일 저장 오류: {str(e)}"]},
            status_code=500
        )
    
    # 구조 검증
    success, validation_errors, validation_result = validate_excel_structure(mapping_path)
    
    if not success:
        return JSONResponse(
            {"success": False, "errors": validation_errors, "validation": validation_result},
            status_code=400
        )
    
    # 데이터베이스 로딩
    try:
        # 데이터베이스 초기화
        init_db()
        
        # 엑셀 파일 읽기
        df_objects = pd.read_excel(mapping_path, sheet_name='objects')
        df_relations = pd.read_excel(mapping_path, sheet_name='relations')
        
        source_doc = mapping_path.name
        
        # 데이터베이스 세션 생성
        with Session(engine) as db_session:
            try:
                # Objects 로딩
                object_key_to_id = load_objects(db_session, df_objects, source_doc)
                
                # Relations 로딩
                load_relations(db_session, df_relations, object_key_to_id, source_doc)
                
                # 커밋
                db_session.commit()
                
                return JSONResponse({
                    "success": True,
                    "message": "파일 업로드 및 데이터 로딩 완료",
                    "stats": {
                        "objects_loaded": len(object_key_to_id),
                        "relations_loaded": len(df_relations)
                    }
                })
                
            except Exception as e:
                db_session.rollback()
                logger.error(f"데이터베이스 로딩 오류: {e}")
                return JSONResponse(
                    {"success": False, "errors": [f"데이터베이스 로딩 오류: {str(e)}"]},
                    status_code=500
                )
    
    except Exception as e:
        logger.error(f"파일 처리 오류: {e}")
        return JSONResponse(
            {"success": False, "errors": [f"파일 처리 오류: {str(e)}"]},
            status_code=500
        )


def generate_relations_from_objects(df_objects: pd.DataFrame) -> pd.DataFrame:
    """
    objects 시트를 기반으로 tags별 역순 관계 생성
    """
    relations = []
    
    # tags별로 object_key 그룹화
    tags_groups = {}
    for idx, row in df_objects.iterrows():
        object_key = str(row['object_key']).strip()
        tags = str(row.get('tags', '')).strip() if pd.notna(row.get('tags')) else ''
        
        if tags not in tags_groups:
            tags_groups[tags] = []
        tags_groups[tags].append(object_key)
    
    # 역순으로 관계 생성
    for tags, keys in tags_groups.items():
        if len(keys) < 2:
            continue
        
        for i in range(len(keys) - 1, 0, -1):
            relations.append({
                'from_key': keys[i],
                'to_key': keys[i - 1],
                'relation_type': 'FLOWS_TO',
                'description': f'Auto-generated from tags: {tags}' if tags else 'Auto-generated',
                'status': 'ACTIVE'
            })
    
    return pd.DataFrame(relations)


def safe_unlink(path: Path, *, retries: int = 6, delay_seconds: float = 0.2) -> None:
    if not path.exists():
        return
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            path.unlink()
            return
        except Exception as e:
            last_error = e
            time.sleep(delay_seconds)
    if last_error:
        raise last_error


def normalize_cell_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def split_names(value: object) -> list[str]:
    text = normalize_cell_value(value)
    if not text:
        return []
    parts = re.split(r"[,\n\r]+", text)
    return [p.strip() for p in parts if p and p.strip()]


def find_header_row_index(df_raw: pd.DataFrame, required_tokens: list[str], max_scan_rows: int = 30) -> int | None:
    scan_rows = min(max_scan_rows, len(df_raw))
    for idx in range(scan_rows):
        row_values = [normalize_cell_value(v).replace("\n", " ") for v in df_raw.iloc[idx].tolist()]
        row_joined = " | ".join([v for v in row_values if v])
        if all(token in row_joined for token in required_tokens):
            return idx
    return None


def find_column_index(header_cells: list[object], all_contains: list[str]) -> int | None:
    normalized = [normalize_cell_value(c).replace("\n", " ") for c in header_cells]
    for i, text in enumerate(normalized):
        if not text:
            continue
        if all(part in text for part in all_contains):
            return i
    return None


def make_object_key(system_type: str, raw_name: str) -> str:
    system = normalize_cell_value(system_type).upper() or "UNKNOWN"
    name = normalize_cell_value(raw_name).upper() or "UNKNOWN"
    name = re.sub(r"[^\w]+", "_", name).strip("_")
    return f"{system}_{name}"


def upsert_object_record(
    *,
    objects_by_key: dict[str, dict],
    object_key: str,
    tags: str,
    record: dict,
) -> None:
    existing = objects_by_key.get(object_key)
    if not existing:
        objects_by_key[object_key] = record
        return

    incoming_tags = normalize_cell_value(tags)
    if not incoming_tags:
        return

    existing_tags = normalize_cell_value(existing.get("tags"))
    if not existing_tags:
        existing["tags"] = incoming_tags
        return

    merged = [t.strip() for t in (existing_tags.split(",") + incoming_tags.split(",")) if t and t.strip()]
    deduped: list[str] = []
    seen = set()
    for t in merged:
        if t in seen:
            continue
        seen.add(t)
        deduped.append(t)
    existing["tags"] = ", ".join(deduped)


def build_mapping_from_definition_files(*, inbound_path: Path, legacy_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Inbound.xlsx(List 시트) + Legacy.xlsx(시스템별 시트) 기반으로 mapping(objects/relations) 생성.
    relations는 플로우(tags)별로 역순(D->C, C->B ...)으로 생성.
    """
    inbound_xls = None
    legacy_xls = None
    try:
        inbound_xls = pd.ExcelFile(inbound_path)
        legacy_xls = pd.ExcelFile(legacy_path)

        if "List" not in inbound_xls.sheet_names:
            raise ValueError("Inbound.xlsx에 'List' 시트가 없습니다.")

        df_list_raw = pd.read_excel(inbound_xls, sheet_name="List", header=None, dtype=object)
        header_row_idx = find_header_row_index(df_list_raw, required_tokens=["No.", "IN/OUT"], max_scan_rows=10)
        if header_row_idx is None:
            header_row_idx = 0

        header_cells = df_list_raw.iloc[header_row_idx].tolist()
        idx_no = find_column_index(header_cells, ["No."])
        idx_source_system = find_column_index(header_cells, ["Source", "System"])
        idx_inout = find_column_index(header_cells, ["IN/OUT"])
        idx_flow_key = find_column_index(header_cells, ["업무IF"]) or find_column_index(header_cells, ["업무", "IF"])
        idx_module = find_column_index(header_cells, ["모듈"])
        idx_aplan_if_table = find_column_index(header_cells, ["I/F", "Table"])
        idx_aplan_stg_table = find_column_index(header_cells, ["STG", "Table"])
        idx_import_program = find_column_index(header_cells, ["Import", "Program"])
        idx_program = find_column_index(header_cells, ["Source/Target", "Table", "Name"])
        idx_business_id = find_column_index(header_cells, ["업무", "ID"])
        idx_business_name = find_column_index(header_cells, ["업무", "명"]) or find_column_index(header_cells, ["업무", "이름"])

        if idx_no is None or idx_source_system is None:
            raise ValueError("Inbound List 시트에서 No./Source System 컬럼을 찾을 수 없습니다.")

        data_rows = df_list_raw.iloc[header_row_idx + 1 :].copy()

        # Legacy: 시스템별로 program key 기준 lookup 구성
        legacy_lookup: dict[str, dict[str, dict]] = {}
        for sheet in legacy_xls.sheet_names:
            if sheet.startswith("_"):
                continue
            df_legacy_raw = pd.read_excel(legacy_xls, sheet_name=sheet, header=None, dtype=object)
            if len(df_legacy_raw) < 2:
                continue
            legacy_header_cells = df_legacy_raw.iloc[0].tolist()
            legacy_idx_program = find_column_index(legacy_header_cells, ["Source/Target", "Table", "Name"])
            legacy_idx_program_table = find_column_index(legacy_header_cells, ["프로그램", "테이블"])
            legacy_idx_if_table = find_column_index(legacy_header_cells, ["I/F", "테이블"])
            legacy_idx_log_table = find_column_index(legacy_header_cells, ["LOG", "테이블"])
            legacy_idx_fm = find_column_index(legacy_header_cells, ["FM"])
            if legacy_idx_program is None:
                continue

            sheet_lookup: dict[str, dict] = {}
            for _, r in df_legacy_raw.iloc[1:].iterrows():
                program = normalize_cell_value(r.iloc[legacy_idx_program])
                if not program:
                    continue
                sheet_lookup[program] = {
                    "program": program,
                    "program_table": normalize_cell_value(r.iloc[legacy_idx_program_table]) if legacy_idx_program_table is not None else "",
                    "if_table": normalize_cell_value(r.iloc[legacy_idx_if_table]) if legacy_idx_if_table is not None else "",
                    "log_table": normalize_cell_value(r.iloc[legacy_idx_log_table]) if legacy_idx_log_table is not None else "",
                    "fm": normalize_cell_value(r.iloc[legacy_idx_fm]) if legacy_idx_fm is not None else "",
                }
            legacy_lookup[sheet.upper()] = sheet_lookup

        objects_by_key: dict[str, dict] = {}
        flow_sequences: list[tuple[str, list[str]]] = []

        for _, r in data_rows.iterrows():
            no_value = r.iloc[idx_no]
            if pd.isna(no_value):
                continue

            inout = normalize_cell_value(r.iloc[idx_inout]) if idx_inout is not None else ""
            if inout and "IN" not in inout.upper():
                continue

            source_system = normalize_cell_value(r.iloc[idx_source_system]).upper()
            if not source_system:
                continue

            flow_key = normalize_cell_value(r.iloc[idx_flow_key]) if idx_flow_key is not None else ""
            if not flow_key:
                business_id = normalize_cell_value(r.iloc[idx_business_id]) if idx_business_id is not None else ""
                business_name = normalize_cell_value(r.iloc[idx_business_name]) if idx_business_name is not None else ""
                flow_key = " ".join([p for p in [business_id, business_name] if p]).strip()
            if not flow_key:
                flow_key = f"{source_system}_UNKNOWN_FLOW"

            module = normalize_cell_value(r.iloc[idx_module]) if idx_module is not None else ""
            program = normalize_cell_value(r.iloc[idx_program]) if idx_program is not None else ""
            aplan_if_tables = split_names(r.iloc[idx_aplan_if_table]) if idx_aplan_if_table is not None else []
            aplan_stg_tables = split_names(r.iloc[idx_aplan_stg_table]) if idx_aplan_stg_table is not None else []
            import_programs = split_names(r.iloc[idx_import_program]) if idx_import_program is not None else []

            flow_object_keys: list[str] = []

            legacy_info = legacy_lookup.get(source_system.upper(), {}).get(program, {}) if program else {}

            # Legacy tables (있으면 먼저)
            for table_name in [legacy_info.get("program_table", ""), legacy_info.get("if_table", ""), legacy_info.get("log_table", "")]:
                if not table_name:
                    continue
                object_key = make_object_key(source_system, table_name)
                flow_object_keys.append(object_key)
                upsert_object_record(
                    objects_by_key=objects_by_key,
                    object_key=object_key,
                    tags=flow_key,
                    record={
                        "object_key": object_key,
                        "name": table_name,
                        "system_type": source_system,
                        "object_type": "TABLE",
                        "layer": "Legacy",
                        "description": f"[정의서] {flow_key} (Legacy)",
                        "owner_team": None,
                        "owner": None,
                        "module": module or None,
                        "status": "ACTIVE",
                        "tags": flow_key,
                        "environment": "PRD",
                    },
                )

            # Source program
            if program:
                object_key = make_object_key(source_system, program)
                flow_object_keys.append(object_key)
                desc = f"[정의서] {flow_key} / 프로그램: {program}"
                if legacy_info.get("fm"):
                    desc += f" / FM: {legacy_info.get('fm')}"
                upsert_object_record(
                    objects_by_key=objects_by_key,
                    object_key=object_key,
                    tags=flow_key,
                    record={
                        "object_key": object_key,
                        "name": program,
                        "system_type": source_system,
                        "object_type": "JOB",
                        "layer": "Legacy",
                        "description": desc,
                        "owner_team": None,
                        "owner": None,
                        "module": module or None,
                        "status": "ACTIVE",
                        "tags": flow_key,
                        "environment": "PRD",
                    },
                )

            # APLAN IF tables
            for table_name in aplan_if_tables:
                object_key = make_object_key("APLAN", table_name)
                flow_object_keys.append(object_key)
                upsert_object_record(
                    objects_by_key=objects_by_key,
                    object_key=object_key,
                    tags=flow_key,
                    record={
                        "object_key": object_key,
                        "name": table_name,
                        "system_type": "APLAN",
                        "object_type": "TABLE",
                        "layer": "In",
                        "description": f"[정의서] {flow_key} (APLAN I/F Table)",
                        "owner_team": None,
                        "owner": None,
                        "module": module or None,
                        "status": "ACTIVE",
                        "tags": flow_key,
                        "environment": "PRD",
                    },
                )

            # APLAN STG tables
            for table_name in aplan_stg_tables:
                object_key = make_object_key("APLAN", table_name)
                flow_object_keys.append(object_key)
                upsert_object_record(
                    objects_by_key=objects_by_key,
                    object_key=object_key,
                    tags=flow_key,
                    record={
                        "object_key": object_key,
                        "name": table_name,
                        "system_type": "APLAN",
                        "object_type": "TABLE",
                        "layer": "Staging",
                        "description": f"[정의서] {flow_key} (APLAN STG Table)",
                        "owner_team": None,
                        "owner": None,
                        "module": module or None,
                        "status": "ACTIVE",
                        "tags": flow_key,
                        "environment": "PRD",
                    },
                )

            # Import programs
            for prog_name in import_programs:
                object_key = make_object_key("APLAN", prog_name)
                flow_object_keys.append(object_key)
                upsert_object_record(
                    objects_by_key=objects_by_key,
                    object_key=object_key,
                    tags=flow_key,
                    record={
                        "object_key": object_key,
                        "name": prog_name,
                        "system_type": "APLAN",
                        "object_type": "JOB",
                        "layer": "Staging",
                        "description": f"[정의서] {flow_key} (Import Program)",
                        "owner_team": None,
                        "owner": None,
                        "module": module or None,
                        "status": "ACTIVE",
                        "tags": flow_key,
                        "environment": "PRD",
                    },
                )

            # flow 내 중복 제거(순서 유지)
            seen = set()
            deduped_seq: list[str] = []
            for k in flow_object_keys:
                if k in seen:
                    continue
                seen.add(k)
                deduped_seq.append(k)

            if len(deduped_seq) >= 2:
                flow_sequences.append((flow_key, deduped_seq))

        # objects: flow 등장 순서대로 정렬
        ordered_object_keys: list[str] = []
        seen_obj = set()
        for _, seq in flow_sequences:
            for k in seq:
                if k in seen_obj:
                    continue
                seen_obj.add(k)
                ordered_object_keys.append(k)
        for k in objects_by_key.keys():
            if k in seen_obj:
                continue
            ordered_object_keys.append(k)

        df_objects = pd.DataFrame([objects_by_key[k] for k in ordered_object_keys])

        # relations: tags별 역순
        relations_records: list[dict] = []
        for flow_key, seq in flow_sequences:
            for i in range(len(seq) - 1, 0, -1):
                relations_records.append({
                    "from_key": seq[i],
                    "to_key": seq[i - 1],
                    "relation_type": "FLOWS_TO",
                    "description": f"[정의서 자동생성] {flow_key}",
                    "status": "ACTIVE",
                })
        df_relations = pd.DataFrame(relations_records)
        return df_objects, df_relations

    finally:
        if inbound_xls is not None:
            inbound_xls.close()
        if legacy_xls is not None:
            legacy_xls.close()


@router.post("/generate-relations", response_class=StreamingResponse)
async def generate_relations_file(file: UploadFile = File(...)):
    """
    relations 시트가 비어있는 경우 자동으로 관계를 생성하여 엑셀 파일로 반환
    """
    if not file.filename.endswith('.xlsx'):
        return JSONResponse(
            {"success": False, "errors": ["엑셀 파일(.xlsx)만 업로드 가능합니다."]},
            status_code=400
        )
    
    # 임시 파일로 저장
    temp_path = Path(f"temp_gen_{file.filename}")
    excel_file = None
    
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # 엑셀 파일 읽기
        excel_file = pd.ExcelFile(temp_path)
        df_objects = pd.read_excel(excel_file, sheet_name='objects')
        df_relations = pd.read_excel(excel_file, sheet_name='relations')
        excel_file.close()
        excel_file = None
        
        # relations가 비어있으면 자동 생성
        if df_relations.empty or len(df_relations) == 0:
            df_relations = generate_relations_from_objects(df_objects)
        
        # 새 엑셀 파일 생성
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_objects.to_excel(writer, sheet_name='objects', index=False)
            df_relations.to_excel(writer, sheet_name='relations', index=False)
        
        output.seek(0)
        
        # 임시 파일 삭제
        safe_unlink(temp_path)
        
        # 파일명 생성
        original_name = Path(file.filename).stem
        download_filename = f"{original_name}_with_relations.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={download_filename}"}
        )
        
    except Exception as e:
        if excel_file is not None:
            excel_file.close()
        if temp_path.exists():
            safe_unlink(temp_path)
        
        return JSONResponse(
            {"success": False, "errors": [f"파일 처리 오류: {str(e)}"]},
            status_code=500
        )


@router.post("/generate-mapping-from-definition", response_class=StreamingResponse)
async def generate_mapping_from_definition(
    inbound_file: UploadFile = File(...),
    legacy_file: UploadFile = File(...),
):
    """
    정의서(Inbound.xlsx) + Legacy.xlsx 업로드 → mapping.xlsx(objects/relations) 생성 후 다운로드
    """
    if not inbound_file.filename.endswith(".xlsx"):
        return JSONResponse({"success": False, "errors": ["Inbound.xlsx는 엑셀(.xlsx) 파일이어야 합니다."]}, status_code=400)
    if not legacy_file.filename.endswith(".xlsx"):
        return JSONResponse({"success": False, "errors": ["Legacy.xlsx는 엑셀(.xlsx) 파일이어야 합니다."]}, status_code=400)

    inbound_temp: Path | None = None
    legacy_temp: Path | None = None
    try:
        inbound_bytes = await inbound_file.read()
        legacy_bytes = await legacy_file.read()

        inbound_temp = Path(tempfile.mkstemp(prefix="temp_inbound_", suffix=".xlsx")[1])
        legacy_temp = Path(tempfile.mkstemp(prefix="temp_legacy_", suffix=".xlsx")[1])
        inbound_temp.write_bytes(inbound_bytes)
        legacy_temp.write_bytes(legacy_bytes)

        df_objects, df_relations = build_mapping_from_definition_files(
            inbound_path=inbound_temp,
            legacy_path=legacy_temp,
        )

        df_objects = ensure_mapping_schema(df=df_objects, columns=OBJECTS_COLUMNS)
        df_relations = ensure_mapping_schema(df=df_relations, columns=RELATIONS_COLUMNS)

        mapping_path = Path("mapping.xlsx")
        write_mapping_excel(df_objects=df_objects, df_relations=df_relations, output_path=mapping_path)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_objects.to_excel(writer, sheet_name="objects", index=False)
            df_relations.to_excel(writer, sheet_name="relations", index=False)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=mapping_from_definition.xlsx"},
        )

    except Exception as e:
        logger.exception("정의서 기반 mapping 생성 오류")
        return JSONResponse({"success": False, "errors": [f"정의서 처리 오류: {str(e)}"]}, status_code=500)
    finally:
        if inbound_temp is not None:
            try:
                safe_unlink(inbound_temp)
            except Exception:
                pass
        if legacy_temp is not None:
            try:
                safe_unlink(legacy_temp)
            except Exception:
                pass


@router.post("/generate-mapping-from-interface", response_class=StreamingResponse)
async def generate_mapping_from_interface(file: UploadFile = File(...)):
    """
    Interface.xlsx 업로드 → mapping.xlsx(objects/relations) 생성 후 다운로드
    """
    if not file.filename.endswith(".xlsx"):
        return JSONResponse(
            {"success": False, "errors": ["엑셀(.xlsx) 파일만 업로드 가능합니다."]},
            status_code=400,
        )

    interface_temp: Path | None = None
    try:
        interface_bytes = await file.read()
        interface_temp = Path(tempfile.mkstemp(prefix="temp_interface_", suffix=".xlsx")[1])
        interface_temp.write_bytes(interface_bytes)

        df_objects, df_relations = build_mapping_from_interface_file(interface_path=interface_temp)
        df_objects = ensure_mapping_schema(df=df_objects, columns=OBJECTS_COLUMNS)
        df_relations = ensure_mapping_schema(df=df_relations, columns=RELATIONS_COLUMNS)

        mapping_path = Path("mapping.xlsx")
        write_mapping_excel(df_objects=df_objects, df_relations=df_relations, output_path=mapping_path)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_objects.to_excel(writer, sheet_name="objects", index=False)
            df_relations.to_excel(writer, sheet_name="relations", index=False)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=mapping_from_interface.xlsx"},
        )

    except Exception as e:
        logger.exception("Interface 기반 mapping 생성 오류")
        return JSONResponse(
            {"success": False, "errors": [f"Interface 처리 오류: {str(e)}"]},
            status_code=500,
        )
    finally:
        if interface_temp is not None:
            try:
                safe_unlink(interface_temp)
            except Exception:
                pass



