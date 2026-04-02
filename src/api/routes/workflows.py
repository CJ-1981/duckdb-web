"""
Workflow Routes

FastAPI routes for workflow CRUD operations.
"""

from typing import Optional, List, Dict, Any
import os
import uuid
import json
import logging
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
import duckdb
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table as RLTable, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth.dependencies import get_current_user, get_db
from src.api.auth.decorators import require_permission
from src.api.models.user import User
from src.api.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse
)
from src.api.services.workflow import WorkflowService


router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])

def quote_identifier(name: str) -> str:
    """Quote a SQL identifier and escape internal double quotes for DuckDB/Standard SQL."""
    if not name:
        return '""'
    return f'"{name.replace("\"", "\"\"")}"'


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
@require_permission("workflows:create")
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new workflow.

    Requires permission: workflows:create
    """
    service = WorkflowService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    workflow = await service.create_workflow(workflow_data, owner_id)
    return workflow

class WorkflowExecutionRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    preview_limit: Optional[int] = 50
    report_config: Optional[Dict[str, Any]] = None

@router.post("/save")
async def save_workflow_graph(
    request: WorkflowExecutionRequest,
    name: str = Query(...)
):
    """Save a workflow graph to a JSON file."""
    save_dir = "data/workflows"
    os.makedirs(save_dir, exist_ok=True)
    
    logger.info(f"Saving workflow: {name}")
    # Protect against path traversal
    safe_name = os.path.basename(name).replace(".json", "")
    file_path = os.path.join(save_dir, f"{safe_name}.json")
    with open(file_path, "w") as f:
        json.dump(request.dict(), f)
    
    return {"message": f"Workflow saved as {name}", "filename": f"{name}.json"}

@router.post("/rename")
async def rename_workflow(
    old_name: str = Query(...),
    new_name: str = Query(...)
):
    """Rename a saved workflow file."""
    save_dir = "data/workflows"
    # Protect against path traversal
    old_safe = os.path.basename(old_name).replace(".json", "")
    new_safe = os.path.basename(new_name).replace(".json", "")
    
    old_path = os.path.join(save_dir, f"{old_safe}.json")
    new_path = os.path.join(save_dir, f"{new_safe}.json")
    
    if not os.path.exists(old_path):
        raise HTTPException(status_code=404, detail="Original workflow not found")
    
    if os.path.exists(new_path):
        raise HTTPException(status_code=400, detail="A workflow with the new name already exists")
    
    os.rename(old_path, new_path)
    return {"message": f"Workflow renamed from {old_name} to {new_name}"}

@router.get("/list")
async def list_saved_workflows():
    """List all saved workflow graphs."""
    save_dir = "data/workflows"
    os.makedirs(save_dir, exist_ok=True)
    
    files = [f.replace(".json", "") for f in os.listdir(save_dir) if f.endswith(".json")]
    return {"workflows": sorted(files)}


class SqlValidationRequest(BaseModel):
    sql: str
    input_table: Optional[str] = None
    columns: Optional[List[Any]] = None

@router.post("/validate-sql")
async def validate_sql(
    request: SqlValidationRequest
):
    """Validate a DuckDB SQL query using EXPLAIN with a realistic schema."""
    sql = request.sql
    input_table = request.input_table
    columns = request.columns
    
    logger.info(f">>> [VALIDATE] SQL Request received (Length: {len(sql)})")
    try:
        conn = duckdb.connect(database=':memory:')
        
        # If input_table is provided, we build a dummy table for binder checks
        if input_table:
            cols_def = []
            if columns:
                for col_item in columns:
                    try:
                        # Handle both JSON string and already-parsed dict/list
                        c = col_item
                        if isinstance(col_item, str):
                            try:
                                c = json.loads(col_item)
                            except:
                                pass
                        
                        if isinstance(c, dict):
                            cname = c.get("column_name") or c.get("name")
                            ctype = c.get("column_type") or c.get("type", "VARCHAR")
                            cols_def.append(f"CAST(NULL AS {ctype}) as {quote_identifier(cname)}")
                        else:
                            # Fallback to plain string column name cast to VARCHAR
                            cols_def.append(f"CAST(NULL AS VARCHAR) as {quote_identifier(str(col_item))}")
                    except Exception as e:
                        logger.warning(f"Failed to parse column for validation: {col_item} - {e}")
                        cols_def.append(f"CAST(NULL AS VARCHAR) as {quote_identifier(str(col_item))}")
            
            if not cols_def:
                cols_def = ["1 as id"]
                
            create_sql = f"CREATE TABLE \"{input_table.replace('\"', '\"\"')}\" AS SELECT {', '.join(cols_def)} WHERE 1=0"
            logger.info(f">>> [VALIDATE] Schema SQL: {create_sql}")
            conn.execute(create_sql)
        
        # Replace {{input}} placeholder
        safe_input = f"\"{input_table.replace('\"', '\"\"')}\"" if input_table else "read_csv_auto('')"
        processed_sql = sql.replace("{{input}}", safe_input).replace("`", "\"")
        
        # Validate syntax and binder via EXPLAIN
        conn.execute(f"EXPLAIN {processed_sql}")
        return {"status": "success", "message": "SQL is valid"}
    except Exception as e:
        logger.error(f">>> [VALIDATE] Binder ERROR: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/load/{name}")
async def load_workflow_graph(name: str):
    """Load a specific workflow graph."""
    file_path = os.path.join("data/workflows", f"{name}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

@router.post("/execute", status_code=status.HTTP_200_OK)
async def execute_workflow_graph(
    request: WorkflowExecutionRequest
):
    """
    Execute a raw workflow graph directly using DuckDB.
    """
    logger.info(f"Executing workflow with {len(request.nodes)} nodes and {len(request.edges)} edges.")
    
    # Locate nodes by subtype or label
    output_node = next((n for n in request.nodes if n["type"] == "output"), None)
    
    # 1. Build adjacency list and find predecessors
    adj = {node["id"]: [] for node in request.nodes}
    predecessors = {node["id"]: [] for node in request.nodes}
    for edge in request.edges:
        src = edge.get("source")
        target = edge.get("target")
        if src in adj and target in adj:
            adj[src].append(target)
            predecessors[target].append(src)
            
    # 2. Topological Sort
    sorted_nodes = []
    visited = set()
    def sort_nodes(node_id):
        if node_id in visited: return
        for p_id in predecessors[node_id]:
            sort_nodes(p_id)
        visited.add(node_id)
        node_obj = next((n for n in request.nodes if n["id"] == node_id), None)
        if node_obj:
            sorted_nodes.append(node_obj)
            
    for node in request.nodes:
        sort_nodes(node["id"])
        
    # 3. Build Query node by node
    node_to_table = {} 
    
    logger.info(f"--- Workflow Execution Start: {len(sorted_nodes)} nodes ---")
    
    try:
        conn = duckdb.connect(database=':memory:')
        
        for i, node in enumerate(sorted_nodes):
            node_id = node["id"]
            safe_id = node_id.replace("-", "_")
            table_name = f"node_{safe_id}"
            node_data = node.get("data", {})
            subtype = node_data.get("subtype")
            label = node_data.get("label", "")
            config = node_data.get("config", {})
            
            preds = predecessors[node_id]
            prev_table = node_to_table.get(preds[0]) if preds else None
            
            logger.info(f"Processing node {i+1}/{len(sorted_nodes)}: {label}")
            
            if node["type"] == "input":
                file_path = config.get("file_path")
                if not file_path: continue
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(file_path)
                
                sql = f"CREATE TEMP TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}')"
                conn.execute(sql)
                node_to_table[node_id] = table_name
                
            elif subtype == "filter" or "Filter" in label:
                if not prev_table: continue
                
                is_adv = config.get("isAdvanced", False)
                where = ""
                
                if is_adv:
                    where = config.get("customWhere", "")
                else:
                    col = config.get("column")
                    op = config.get("operator", "==")
                    val = str(config.get("value", "")).strip()
                    
                    if col:
                        clean_val = val.replace("'", "''")
                        qc = quote_identifier(col)
                        if op == "==": where = f"TRIM(CAST({qc} AS VARCHAR)) = '{clean_val}'"
                        elif op == "!=": where = f"(TRIM(CAST({qc} AS VARCHAR)) != '{clean_val}' OR {qc} IS NULL)"
                        elif op == "contains": where = f"CAST({qc} AS VARCHAR) ILIKE '%{clean_val}%'"
                        elif op == "not_contains": where = f"(TRIM(CAST({qc} AS VARCHAR)) NOT ILIKE '%{clean_val}%' OR {qc} IS NULL)"
                        elif op == "starts_with": where = f"CAST({qc} AS VARCHAR) ILIKE '{clean_val}%'"
                        elif op == "ends_with": where = f"CAST({qc} AS VARCHAR) ILIKE '%{clean_val}'"
                        elif op == "is_null": where = f"({qc} IS NULL OR CAST({qc} AS VARCHAR) = '')"
                        elif op == "is_not_null": where = f"({qc} IS NOT NULL AND CAST({qc} AS VARCHAR) != '')"
                        elif op == "in":
                            items = ["'" + v.strip().replace("'", "''") + "'" for v in val.split(',')]
                            where = f"TRIM(CAST({qc} AS VARCHAR)) IN ({', '.join(items)})"
                        elif op == "not_in":
                            items = ["'" + v.strip().replace("'", "''") + "'" for v in val.split(',')]
                            where = f"(TRIM(CAST({qc} AS VARCHAR)) NOT IN ({', '.join(items)}) OR {qc} IS NULL)"
                        elif op in [">", "<", ">=", "<="]:
                            num_val = clean_val.replace(',', '')
                            where = f"TRY_CAST(REPLACE(CAST({qc} AS VARCHAR), ',', '') AS DOUBLE) {op} {num_val}"
                
                if where:
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} WHERE {where}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table
            
            elif subtype == "computed":
                if not prev_table: continue
                expr = config.get("expression")
                alias = config.get("alias", "new_column")
                if expr and alias:
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT *, {expr} AS {quote_identifier(alias)} FROM {prev_table}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "raw_sql":
                raw_sql = config.get("sql", "")
                if raw_sql:
                    input_table = prev_table if prev_table else "read_csv_auto('')"
                    # Auto-convert backticks to double quotes for standard DuckDB support
                    # This helps with AI-generated or user-pasted MySQL-style queries
                    processed_sql = raw_sql.replace("{{input}}", input_table).replace("`", "\"")
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS {processed_sql}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "distinct":
                if not prev_table: continue
                cols_raw = config.get("columns", "")
                if cols_raw:
                    cols = [quote_identifier(c.strip()) for c in cols_raw.split(',') if c.strip()]
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT DISTINCT {', '.join(cols)} FROM {prev_table}")
                else:
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT DISTINCT * FROM {prev_table}")
                node_to_table[node_id] = table_name

            elif subtype == "rename":
                if not prev_table: continue
                mappings = config.get("mappings", [])
                if mappings:
                    all_cols = conn.execute(f"DESCRIBE {prev_table}").df()['column_name'].tolist()
                    renamed_map = {m['old']: m['new'] for m in mappings if m.get('old') and m.get('new')}
                    select_items = [f"{quote_identifier(col)} AS {quote_identifier(renamed_map[col])}" if col in renamed_map else quote_identifier(col) for col in all_cols]
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT {', '.join(select_items)} FROM {prev_table}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "case_when":
                if not prev_table: continue
                conditions = config.get("conditions", [])
                else_val_raw = str(config.get("elseValue", "NULL")).strip()
                alias = config.get("alias", "case_result")
                
                def sql_val(v):
                    if not v or v.upper() == "NULL": return "NULL"
                    if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')): return v
                    try:
                        float(v.replace(',', ''))
                        return v
                    except ValueError:
                        return "'" + v.replace("'", "''") + "'"

                if conditions and alias:
                    case_parts = ["CASE"]
                    for c in conditions:
                        w, t = c.get('when'), c.get('then')
                        if w and t: case_parts.append(f"WHEN {w} THEN {sql_val(t)}")
                    case_parts.append(f"ELSE {sql_val(else_val_raw)} END AS {quote_identifier(alias)}")
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT *, {' '.join(case_parts)} FROM {prev_table}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "window":
                if not prev_table: continue
                func_name = config.get("function", "ROW_NUMBER")
                partition = config.get("partitionBy", "")
                order = config.get("orderBy", "")
                direction = config.get("direction", "ASC")
                alias = config.get("alias", "window_result")
                value_col = config.get("valueColumn", "")

                # Allowlist validation (prevent SQL injection)
                ALLOWED_FUNCS = {
                    "ROW_NUMBER", "RANK", "DENSE_RANK",
                    "LAG", "LEAD",
                    "SUM", "AVG", "MIN", "MAX", "COUNT"
                }
                if func_name not in ALLOWED_FUNCS:
                    logger.warning(f"Invalid window function '{func_name}', falling back to ROW_NUMBER")
                    func_name = "ROW_NUMBER"
                if direction not in ("ASC", "DESC"):
                    direction = "ASC"

                # Build function call: parameterless vs column-based
                PARAMETERLESS_FUNCS = {"ROW_NUMBER", "RANK", "DENSE_RANK"}
                if func_name in PARAMETERLESS_FUNCS:
                    func_call = f"{func_name}()"
                else:
                    if value_col:
                        func_call = f"{func_name}({quote_identifier(value_col)})"
                    else:
                        logger.warning(f"Window function {func_name} requires a valueColumn — skipping node")
                        node_to_table[node_id] = prev_table
                        continue

                over_parts = []
                if partition: over_parts.append(f"PARTITION BY {quote_identifier(partition)}")
                if order: over_parts.append(f"ORDER BY {quote_identifier(order)} {direction}")

                sql = (
                    f"CREATE TEMP TABLE {table_name} AS "
                    f"SELECT *, {func_call} OVER ({' '.join(over_parts)}) AS {quote_identifier(alias)} "
                    f"FROM {prev_table}"
                )
                logger.info(f"Window SQL: {sql}")
                conn.execute(sql)
                node_to_table[node_id] = table_name

            elif subtype == "sort" or "Sort" in label:
                if not prev_table: continue
                col = config.get("column")
                direction = config.get("direction", "asc").upper()
                if col:
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} ORDER BY {quote_identifier(col)} {direction}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table
                    
            elif subtype == "limit" or "Limit" in label:
                if not prev_table: continue
                count = int(config.get("count", 100))
                conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} LIMIT {count}")
                node_to_table[node_id] = table_name
                
            elif subtype == "clean" or "Clean" in label:
                if not prev_table: continue
                col, op = config.get("column"), config.get("operation", "trim")
                if col:
                    expr = quote_identifier(col)
                    if op == "trim": expr = f"TRIM(CAST({quote_identifier(col)} AS VARCHAR))"
                    elif op == "upper": expr = f"UPPER(CAST({quote_identifier(col)} AS VARCHAR))"
                    elif op == "lower": expr = f"LOWER(CAST({quote_identifier(col)} AS VARCHAR))"
                    elif op == "numeric": expr = f"REGEXP_REPLACE(CAST({quote_identifier(col)} AS VARCHAR), '[^0-9.]', '', 'g')"
                    elif op == "replace_null": expr = f"COALESCE(NULLIF(CAST({quote_identifier(col)} AS VARCHAR), ''), '{config.get('newValue', '')}')"
                    elif op == "to_date": expr = f"TRY_CAST({quote_identifier(col)} AS DATE)"
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * REPLACE ({expr} AS {quote_identifier(col)}) FROM {prev_table}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table
                    
            elif subtype == "select" or "Select" in label:
                if not prev_table: continue
                cols = [c.strip() for c in config.get("columns", "").split(',') if c.strip()]
                if cols:
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT {', '.join([quote_identifier(c) for c in cols])} FROM {prev_table}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table
                    
            elif subtype == "combine" or "Combine" in label:
                if len(preds) < 2:
                    node_to_table[node_id] = prev_table
                else:
                    left, right = node_to_table.get(preds[0]), node_to_table.get(preds[1])
                    if left and right:
                        join_type = config.get("joinType", "inner").upper()
                        if join_type in ["UNION", "UNION_ALL", "APPEND"]:
                            # Handle UNION (combining rows)
                            op = "UNION ALL" if join_type in ["UNION_ALL", "APPEND"] else "UNION"
                            conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * FROM {left} {op} SELECT * FROM {right}")
                            node_to_table[node_id] = table_name
                        else:
                            # Handle JOIN (combining columns)
                            lc, rc = config.get("leftColumn"), config.get("rightColumn")
                            if lc and rc:
                                conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * FROM {left} {join_type} JOIN {right} ON {left}.{quote_identifier(lc)} = {right}.{quote_identifier(rc)}")
                                node_to_table[node_id] = table_name
                            else:
                                node_to_table[node_id] = left
                    else:
                        node_to_table[node_id] = prev_table

            elif subtype == "aggregate" or "Aggregate" in label:
                if not prev_table: continue
                group_by = [c.strip() for c in config.get("groupBy", "").split(',') if c.strip()]
                aggs = config.get("aggregations", [])
                if not aggs:
                    aggs = [{"column": config.get("column"), "operation": config.get("operation", "sum").upper(), "alias": config.get("alias")}]

                agg_parts = []
                for a in aggs:
                    c, f = a.get("column"), a.get("operation", "sum").upper()
                    al = a.get("alias") or f"{f.lower()}_{c}"
                    if c:
                        qc = quote_identifier(c)
                        qa = quote_identifier(al)
                        clean = f"TRY_CAST(REPLACE(CAST({qc} AS VARCHAR), ',', '') AS DOUBLE)"
                        agg_parts.append(f"COUNT({qc}) AS {qa}" if f == "COUNT" else f"{f}({clean}) AS {qa}")
                    else:
                        agg_parts.append(f"COUNT(*) AS {quote_identifier(al)}")

                sel = ", ".join(agg_parts)
                if group_by: sel = f"{', '.join([quote_identifier(c) for c in group_by])}, {sel}"
                sql = f"CREATE TEMP TABLE {table_name} AS SELECT {sel} FROM {prev_table}"
                if group_by: sql += f" GROUP BY {', '.join([quote_identifier(c) for c in group_by])}"
                conn.execute(sql)
                node_to_table[node_id] = table_name

            elif node["type"] == "output":
                if prev_table: node_to_table[node_id] = prev_table

            if node_id not in node_to_table and prev_table:
                node_to_table[node_id] = prev_table

        if not sorted_nodes:
            return {
                "status": "success",
                "row_count": 0,
                "preview": [],
                "columns": [],
                "message": "No nodes processed."
            }

        final_node_id = sorted_nodes[-1]["id"]
        final_table = node_to_table.get(final_node_id)
        if not final_table:
            raise HTTPException(status_code=400, detail="No output determined.")
            
        df = conn.execute(f"SELECT * FROM {final_table}").df()
        
        export_url = None
        if output_node:
            os.makedirs("downloads", exist_ok=True)
            config = output_node.get("data", {}).get("config", {})
            filename = config.get("filename", "exported_results.csv")
            if not filename.endswith('.csv'): filename += '.csv'
            export_path = os.path.join("downloads", f"export_{uuid.uuid4()}_{filename}")
            df.to_csv(export_path, index=False)
            export_url = f"/api/v1/data/download/{os.path.basename(export_path)}"

        node_counts, node_columns, node_samples, node_types = {}, {}, {}, {}
        preview_limit = request.preview_limit or 50
        
        for nid, tname in node_to_table.items():
            try:
                node_counts[nid] = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
                desc_df = conn.execute(f"DESCRIBE {tname}").df()
                node_columns[nid] = desc_df['column_name'].tolist()
                node_types[nid] = desc_df[['column_name', 'column_type']].to_dict(orient='records')
                node_samples[nid] = conn.execute(f"SELECT * FROM {tname} LIMIT {preview_limit}").df().fillna("").to_dict(orient="records")
            except:
                pass

        return {
            "status": "success",
            "row_count": len(df),
            "node_counts": node_counts,
            "node_columns": node_columns,
            "node_types": node_types,
            "node_samples": node_samples,
            "preview": df.head(preview_limit).fillna("").to_dict(orient="records"),
            "columns": df.columns.tolist(),
            "export_url": export_url
        }
    except Exception as e:
        logger.error(f"DuckDB Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/report", status_code=status.HTTP_200_OK)
async def generate_workflow_report(
    request: WorkflowExecutionRequest
):
    """Generate a PDF or Markdown report from the workflow results."""
    logger.info(">>> [REPORT] Starting generation...")
    
    # 1. Execute workflow
    try:
        logger.info(f">>> [REPORT] Executing workflow with {len(request.nodes)} nodes...")
        exec_result = await execute_workflow_graph(request)
    except Exception as e:
        logger.error(f">>> [REPORT] Execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")
    
    export_url = exec_result.get("export_url")
    if not export_url:
        logger.error(">>> [REPORT] No export URL found in execution results.")
        raise HTTPException(status_code=400, detail="Workflow must output data to generate a report.")
    
    file_name = os.path.basename(export_url)
    # Check downloads first (since we just moved exports there)
    file_path = os.path.join("downloads", file_name)
    if not os.path.exists(file_path):
        # Fallback to uploads for backward compatibility
        file_path = os.path.join("uploads", file_name)
        
    logger.info(f">>> [REPORT] Reading data from {file_path}...")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Execution result file not found.")
        
    try:
        df = duckdb.read_csv(file_path).df()
        logger.info(f">>> [REPORT] Data loaded: {len(df)} rows.")
    except Exception as e:
        logger.error(f">>> [REPORT] Failed to read CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to read data: {str(e)}")
    
    cfg = request.report_config or {}
    report_format = cfg.get("format", "PDF").upper()
    title = cfg.get("title", "Data Analysis Report")
    description = cfg.get("description", "")
    sections = cfg.get("sections", [])
    font_family = cfg.get("font", "NanumGothic")
    
    # Register font if needed
    font_path = "fonts/NanumGothic.ttf"
    is_korean = os.path.exists(font_path)
    if is_korean:
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
        except:
            is_korean = False
    
    actual_font = font_family if (font_family == 'NanumGothic' and is_korean) else 'Helvetica'
    
    report_filename = f"report_{uuid.uuid4()}"
    
    if report_format == "MARKDOWN":
        os.makedirs("downloads", exist_ok=True)
        md_file = f"{report_filename}.md"
        md_path = os.path.join("downloads", md_file)
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            if description:
                f.write(f"{description}\n\n")
            
            for sec in sections:
                f.write(f"## {sec.get('heading', 'Section')}\n\n")
                sec_type = sec.get("type", "table")
                
                if sec_type == "table":
                    f.write(df.head(20).to_markdown(index=False) + "\n\n")
                    if len(df) > 20:
                        f.write(f"*Note: Showing first 20 rows of {len(df)} total.*\n\n")
                elif sec_type == "stats":
                    f.write(df.describe().reset_index().to_markdown(index=False) + "\n\n")
                elif sec_type == "text":
                    content = sec.get("content", "")
                    content = content.replace("{{row_count}}", str(len(df)))
                    content = content.replace("{{column_count}}", str(len(df.columns)))
                    f.write(f"{content}\n\n")
            
            f.write(f"---\n*Generated by DuckDB Platform on {uuid.uuid1()}*")
            
        return {"status": "success", "report_url": f"/api/v1/data/download/{md_file}"}
        
    else: # PDF
        os.makedirs("downloads", exist_ok=True)
        pdf_file = f"{report_filename}.pdf"
        pdf_path = os.path.join("downloads", pdf_file)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles for Korean support
        title_style = ParagraphStyle(
            'TitleKR',
            parent=styles['Title'],
            fontName=actual_font,
            fontSize=24,
            spaceAfter=20
        )
        heading_style = ParagraphStyle(
            'HeadingKR',
            parent=styles['Heading2'],
            fontName=actual_font,
            fontSize=16,
            spaceAfter=12,
            spaceBefore=12
        )
        body_style = ParagraphStyle(
            'BodyKR',
            parent=styles['Normal'],
            fontName=actual_font,
            fontSize=10,
            leading=14
        )
        
        elements.append(Paragraph(title, title_style))
        if description:
            elements.append(Paragraph(description, body_style))
            elements.append(Spacer(1, 20))
            
        for sec in sections:
            elements.append(Paragraph(sec.get('heading', 'Section'), heading_style))
            sec_type = sec.get("type", "table")
            
            if sec_type == "table":
                # Convert first 15 rows to printable table
                cols = df.columns.tolist()
                data = [cols]
                sample_rows = df.head(15).fillna("").values.tolist()
                data.extend(sample_rows)
                
                # Truncate cell content for PDF display
                clean_data = []
                for row in data:
                    clean_data.append([str(cell)[:20] for cell in row])
                
                t = RLTable(clean_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), actual_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                if len(df) > 15:
                    elements.append(Paragraph(f"(Showing 15 of {len(df)} rows)", body_style))
                elements.append(Spacer(1, 15))
                
            elif sec_type == "stats":
                stats_df = df.describe().reset_index()
                cols = stats_df.columns.tolist()
                data = [cols] + stats_df.fillna("").values.tolist()
                clean_data = [[str(cell)[:20] for cell in row] for row in data]
                
                t = RLTable(clean_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, -1), actual_font),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 15))
                
            elif sec_type == "text":
                content = sec.get("content", "")
                content = content.replace("{{row_count}}", str(len(df)))
                content = content.replace("{{column_count}}", str(len(df.columns)))
                elements.append(Paragraph(content, body_style))
                elements.append(Spacer(1, 15))
        
        doc.build(elements)
        return {"status": "success", "report_url": f"/api/v1/data/download/{pdf_file}"}

class InspectRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    node_id: str

@router.post("/inspect", status_code=status.HTTP_200_OK)
async def inspect_node_dataset(request: InspectRequest):
    """Run full statistical inspection on a specific node's output dataset."""
    target_id = request.node_id
    nodes, edges = request.nodes, request.edges

    adj = {n["id"]: [] for n in nodes}
    predecessors = {n["id"]: [] for n in nodes}
    for edge in edges:
        src, tgt = edge.get("source"), edge.get("target")
        if src in adj and tgt in adj:
            adj[src].append(tgt)
            predecessors[tgt].append(src)

    sorted_nodes: list = []
    visited: set = set()
    def _sort(nid: str):
        if nid in visited: return
        for p in predecessors.get(nid, []):
            _sort(p)
        visited.add(nid)
        obj = next((n for n in nodes if n["id"] == nid), None)
        if obj: sorted_nodes.append(obj)
    _sort(target_id)

    try:
        conn = duckdb.connect(database=':memory:')
        node_to_table: dict = {}

        for node in sorted_nodes:
            node_id = node["id"]
            safe_id = node_id.replace("-", "_")
            table_name = f"node_{safe_id}"
            node_data = node.get("data", {})
            subtype = node_data.get("subtype")
            label = node_data.get("label", "")
            config = node_data.get("config", {})
            preds = predecessors[node_id]
            prev_table = node_to_table.get(preds[0]) if preds else None

            try:
                if node["type"] == "input":
                    fp = config.get("file_path")
                    if not fp: continue
                    if not os.path.isabs(fp): fp = os.path.abspath(fp)
                    conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * FROM read_csv_auto('{fp}')")
                    node_to_table[node_id] = table_name
                elif prev_table:
                    # Pass-through execution for all transformation nodes
                    exec_req = WorkflowExecutionRequest(nodes=nodes, edges=edges, preview_limit=0)
                    # Re-use the single-node logic inline using a simplified pass
                    if subtype == "filter" or "Filter" in label:
                        is_adv = config.get("isAdvanced", False)
                        where = ""
                        if is_adv: where = config.get("customWhere", "")
                        else:
                            col, op = config.get("column"), config.get("operator", "==")
                            val = str(config.get("value", "")).strip()
                            if col:
                                cv = val.replace("'", "''")
                                if op == "==": where = f"TRIM(CAST(\"{col}\" AS VARCHAR)) = '{cv}'"
                                elif op == "!=": where = f"(TRIM(CAST(\"{col}\" AS VARCHAR)) != '{cv}' OR \"{col}\" IS NULL)"
                                elif op == "contains": where = f"CAST(\"{col}\" AS VARCHAR) ILIKE '%{cv}%'"
                                elif op == "is_null": where = f"(\"{col}\" IS NULL OR CAST(\"{col}\" AS VARCHAR) = '')"
                                elif op == "is_not_null": where = f"(\"{col}\" IS NOT NULL AND CAST(\"{col}\" AS VARCHAR) != '')"
                                elif op in [">", "<", ">=", "<="]: where = f"TRY_CAST(REPLACE(CAST(\"{col}\" AS VARCHAR), ',', '') AS DOUBLE) {op} {cv.replace(',', '')}"
                        if where:
                            conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} WHERE {where}")
                            node_to_table[node_id] = table_name
                        else: node_to_table[node_id] = prev_table
                    elif subtype == "select" or "Select" in label:
                        cols = [c.strip() for c in config.get("columns", "").split(',') if c.strip()]
                        if cols:
                            conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT {', '.join([f'\"{c}\"' for c in cols])} FROM {prev_table}")
                            node_to_table[node_id] = table_name
                        else: node_to_table[node_id] = prev_table
                    elif subtype == "aggregate" or "Aggregate" in label:
                        group_by = [c.strip() for c in config.get("groupBy", "").split(',') if c.strip()]
                        aggs = config.get("aggregations", []) or []
                        if not aggs: aggs = [{"column": config.get("column"), "operation": config.get("operation", "sum").upper(), "alias": config.get("alias")}]
                        agg_parts = []
                        for a in aggs:
                            c, f = a.get("column"), a.get("operation", "sum").upper()
                            al = a.get("alias") or f"{f.lower()}_{c}"
                            if c: agg_parts.append(f"COUNT(\"{c}\") AS \"{al}\"" if f == "COUNT" else f"{f}(TRY_CAST(REPLACE(CAST(\"{c}\" AS VARCHAR),',','') AS DOUBLE)) AS \"{al}\"")
                            else: agg_parts.append(f"COUNT(*) AS \"{al}\"")
                        sel = ", ".join(agg_parts)
                        if group_by: sel = f"{', '.join([f'\"{c}\"' for c in group_by])}, {sel}"
                        sql = f"CREATE TEMP TABLE {table_name} AS SELECT {sel} FROM {prev_table}"
                        if group_by: sql += f" GROUP BY {', '.join([f'\"{c}\"' for c in group_by])}"
                        conn.execute(sql); node_to_table[node_id] = table_name
                    elif subtype == "sort" or "Sort" in label:
                        col, direction = config.get("column"), config.get("direction", "asc").upper()
                        if col:
                            conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} ORDER BY \"{col}\" {direction}")
                            node_to_table[node_id] = table_name
                        else: node_to_table[node_id] = prev_table
                    elif subtype == "limit" or "Limit" in label:
                        conn.execute(f"CREATE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} LIMIT {int(config.get('count', 100))}")
                        node_to_table[node_id] = table_name
                    elif subtype == "raw_sql":
                        raw_sql = config.get("sql", "")
                        if raw_sql:
                            # Auto-convert backticks to double quotes for standard DuckDB support
                            processed_sql = raw_sql.replace("{{input}}", prev_table).replace("`", "\"")
                            conn.execute(f"CREATE TEMP TABLE {table_name} AS {processed_sql}")
                            node_to_table[node_id] = table_name
                        else: node_to_table[node_id] = prev_table
                    else:
                        node_to_table[node_id] = prev_table
                elif node["type"] == "output":
                    if prev_table: node_to_table[node_id] = prev_table
            except Exception as node_err:
                logger.warning(f"Inspect: node {node_id} failed: {node_err}")
                if prev_table: node_to_table[node_id] = prev_table

        target_table = node_to_table.get(target_id)
        if not target_table:
            raise HTTPException(status_code=400, detail=f"Could not execute workflow to reach node '{target_id}'.")

        total_rows = conn.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()[0]
        desc_df = conn.execute(f"DESCRIBE {target_table}").df()

        columns = []
        try:
            summarize_df = conn.execute(f"SUMMARIZE {target_table}").df()
            summarize_map = {row['column_name']: row for _, row in summarize_df.iterrows()}
        except Exception:
            summarize_map = {}

        def val_or_none(v):
            if v is None or pd.isna(v): return None
            try:
                fv = float(v)
                if not math.isfinite(fv): return None
                return fv
            except (ValueError, TypeError): pass
            if isinstance(v, (pd.Timestamp, pd.Period)):
                return str(v)
            return v

        for _, drow in desc_df.iterrows():
            col_name = drow['column_name']
            col_type = drow['column_type']
            stat: dict = {"column_name": col_name, "column_type": col_type}
            if col_name in summarize_map:
                s = summarize_map[col_name]
                cnt = int(s.get('count', 0)) if val_or_none(s.get('count')) is not None else 0
                stat.update({
                    "count": cnt,
                    "null_count": total_rows - cnt,
                    "null_pct": round((total_rows - cnt) / total_rows * 100, 1) if total_rows else 0,
                    "distinct": int(s.get('approx_unique', 0)) if val_or_none(s.get('approx_unique')) is not None else 0,
                    "min": str(s['min']) if val_or_none(s.get('min')) is not None else None,
                    "max": str(s['max']) if val_or_none(s.get('max')) is not None else None,
                    "mean": round(float(s['avg']), 4) if val_or_none(s.get('avg')) is not None else None,
                    "std": round(float(s['std']), 4) if val_or_none(s.get('std')) is not None else None,
                    "q25": str(s['q25']) if val_or_none(s.get('q25')) is not None else None,
                    "q50": str(s['q50']) if val_or_none(s.get('q50')) is not None else None,
                    "q75": str(s['q75']) if val_or_none(s.get('q75')) is not None else None,
                })
            else:
                try:
                    qcn = quote_identifier(col_name)
                    cnt = conn.execute(f"SELECT COUNT({qcn}) FROM {target_table}").fetchone()[0]
                    dist = conn.execute(f"SELECT COUNT(DISTINCT {qcn}) FROM {target_table}").fetchone()[0]
                    stat.update({"count": cnt, "null_count": total_rows - cnt,
                                 "null_pct": round((total_rows - cnt) / total_rows * 100, 1) if total_rows else 0,
                                 "distinct": dist})
                except Exception: pass
            columns.append(stat)

        def clean_json(v):
            if isinstance(v, float):
                if not math.isfinite(v): return None
                return v
            if isinstance(v, list): return [clean_json(i) for i in v]
            if isinstance(v, dict): return {ki: clean_json(vi) for ki, vi in v.items()}
            return v

        return clean_json({"status": "success", "total_rows": total_rows, "total_columns": len(columns), "columns": columns})

    except HTTPException: raise
    except Exception as e:
        logger.error(f"Inspect error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inspection error: {str(e)}")


@router.get("", response_model=WorkflowListResponse)
@require_permission("workflows:read")
async def list_workflows(
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WorkflowService(db)
    owner_id = int(current_user["sub"])
    workflows, total = await service.list_workflows(owner_id, is_active=is_active, page=page, page_size=page_size)
    return WorkflowListResponse(workflows=workflows, total=total, page=page, page_size=page_size)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
@require_permission("workflows:read")
async def get_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WorkflowService(db)
    owner_id = int(current_user["sub"])
    workflow = await service.get_workflow(workflow_id, owner_id)
    if not workflow: raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
@require_permission("workflows:write")
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WorkflowService(db)
    owner_id = int(current_user["sub"])
    workflow = await service.update_workflow(workflow_id, workflow_data, owner_id)
    if not workflow: raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
@require_permission("workflows:write")
async def partial_update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WorkflowService(db)
    owner_id = int(current_user["sub"])
    workflow = await service.update_workflow(workflow_id, workflow_data, owner_id)
    if not workflow: raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("workflows:delete")
async def delete_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WorkflowService(db)
    owner_id = int(current_user["sub"])
    success = await service.delete_workflow(workflow_id, owner_id)
    if not success: raise HTTPException(status_code=404, detail="Workflow not found")
    return None
