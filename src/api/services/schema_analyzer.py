import duckdb
import logging
from fastapi import HTTPException
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def quote_identifier(identifier: str) -> str:
    """Safely quote a SQL identifier (e.g., column name)"""
    if not identifier:
        return '""'
    return f'"{identifier.replace('"', '""')}"'

def _get_df(conn, query: str):
    """Helper to get a dataframe from a query."""
    return conn.execute(query).df()

class SchemaAnalyzerService:
    @staticmethod
    def analyze_workflow_schema(request: Any):
        """
        Dry-run the workflow using DUMMY schemas to infer resulting column types for every node.
        Does NOT read actual data (uses WHERE 1=0).
        """
        logger.info(f"Analyzing schema for {len(request.nodes)} nodes...")
        conn = duckdb.connect(database=':memory:')

        adj = {str(node["id"]): [] for node in request.nodes}
        predecessors = {str(node["id"]): [] for node in request.nodes}
        for edge in request.edges:
            src = str(edge.get("source", ""))
            target = str(edge.get("target", ""))
            if src in adj and target in adj:
                adj[src].append(target)
                predecessors[target].append(src)

        sorted_nodes: list = []
        visited: set = set()
        def _sort(nid: str):
            nid_str = str(nid)
            if nid_str in visited: return
            for p in predecessors.get(nid_str, []): _sort(p)
            visited.add(nid_str)
            obj = next((n for n in request.nodes if str(n["id"]) == nid_str), None)
            if obj: sorted_nodes.append(obj)
        for n in request.nodes: _sort(str(n["id"]))

        node_schemas = {}
        node_to_table = {}

        try:
            for node in sorted_nodes:
                node_id = str(node["id"])
                safe_id = node_id.replace("-", "_")
                tname = f"node_{safe_id}"
                node_data = node.get("data", {})
                subtype = node_data.get("subtype")
                config = node_data.get("config", {})
                preds = predecessors.get(node_id, [])
                prev_table = node_to_table.get(preds[0]) if preds else None

                try:
                    if node["type"] == "input":
                        if subtype == "remote_file":
                            url = config.get("url")
                            if url:
                                try:
                                    conn.execute("INSTALL httpfs; LOAD httpfs;")
                                    if url.lower().endswith('.parquet'):
                                        conn.execute(f"CREATE OR REPLACE TEMP TABLE {tname} AS SELECT * FROM read_parquet('{url}') WHERE 1=0")
                                    else:
                                        # Treat empty strings as NULL during CSV load
                                        conn.execute(f"CREATE OR REPLACE TEMP TABLE {tname} AS SELECT * FROM read_csv_auto('{url}', ALL_VARCHAR=TRUE, nullstr='') WHERE 1=0")
                                except Exception:
                                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {tname} (dummy VARCHAR)")
                            else:
                                conn.execute(f"CREATE OR REPLACE TEMP TABLE {tname} (dummy VARCHAR)")
                            node_to_table[node_id] = tname

                            continue

                        fp = config.get("file_path") or ""
                        # Create dummy empty table from CSV schema with type inference
                        from src.api.routes.workflows import get_or_infer_csv_schema
                        if fp:
                            infer_result = get_or_infer_csv_schema(fp)
                            schema = infer_result["schema"]
                            if schema:
                                # Build CREATE TABLE with proper types
                                columns_def = ', '.join([f'"{col}" {dtype}' for col, dtype in schema.items()])
                                conn.execute(f"CREATE OR REPLACE TEMP TABLE {tname} ({columns_def})")
                            else:
                                # Fallback to ALL_VARCHAR if schema inference fails
                                # Treat empty strings as NULL during CSV load
                                conn.execute(f"CREATE OR REPLACE TEMP TABLE {tname} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE, nullstr='') WHERE 1=0", [fp])
                        else:
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {tname} (dummy VARCHAR)")
                        node_to_table[node_id] = tname

                    elif prev_table:
                        # Simplified transformation logic for schema analysis
                        if subtype == "filter":
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {tname} AS SELECT * FROM {prev_table} WHERE 1=0")
                        elif subtype == "select":
                            cols = [quote_identifier(c.strip()) for c in config.get("columns", "").split(',') if c.strip()]
                            sel = ", ".join(cols) if cols else "*"
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {tname} AS SELECT {sel} FROM {prev_table} WHERE 1=0")
                        elif subtype == "aggregate":
                            # Aggregation changes schema dramatically
                            aggs = config.get("aggregations", []) or []
                            if not aggs: aggs = [{"column": config.get("column"), "operation": config.get("operation", "sum").upper(), "alias": config.get("alias")}]
                            agg_parts = []
                            for a in aggs:
                                c, f = a.get("column"), a.get("operation", "sum").upper()
                                al = a.get("alias") or f"{f.lower()}_{c}"
                                if c: agg_parts.append(f"CAST(NULL AS DOUBLE) AS {quote_identifier(al)}")
                                else: agg_parts.append(f"CAST(0 AS BIGINT) AS {quote_identifier(al)}")

                            group_by = [quote_identifier(c.strip()) for c in config.get("groupBy", "").split(',') if c.strip()]
                            sel = ", ".join(agg_parts)
                            if group_by: sel = f"{', '.join(group_by)}, {sel}"
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {tname} AS SELECT {sel} FROM {prev_table} WHERE 1=0")
                        else:
                            # Default: carry over schema
                            node_to_table[node_id] = prev_table
                            continue
                        node_to_table[node_id] = tname


                    # Get schema
                    if node_id in node_to_table:
                        desc = _get_df(conn, f"DESCRIBE {node_to_table[node_id]}")
                        node_schemas[node_id] = desc[['column_name', 'column_type']].to_dict(orient='records')
                except Exception as e:
                    logger.warning(f"Analyze failed for node {node_id}: {e}")

            return {"status": "success", "node_schemas": node_schemas}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
