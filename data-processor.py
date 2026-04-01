"""
DuckDB CSV Processor
====================
Handles: file / stdin  ×  with/without header  ×  with/without key:value pairs

Usage:
    python duckdb_processor.py data.csv
    python duckdb_processor.py data.csv --no-header
    python duckdb_processor.py data.csv --no-kv
    python duckdb_processor.py data.csv --no-header --no-kv
    cat data.csv | python duckdb_processor.py
    cat data.csv | python duckdb_processor.py --no-header --no-kv

    # Manual column naming (when no header)
    python duckdb_processor.py data.csv --no-header --col-names id,name,amount,region,timestamp
"""

import argparse
import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import duckdb

# ══════════════════════════════════════════════════════════════
#  DETECTION
# ══════════════════════════════════════════════════════════════

def detect_header(rows: list[list[str]]) -> bool:
    """
    Heuristic: first row is a header if its values are non-numeric
    and subsequent rows contain numeric values in the same positions.
    """
    if len(rows) < 2:
        return False

    first = rows[0]
    rest  = rows[1:min(6, len(rows))]

    numeric_in_first = sum(1 for v in first if _is_numeric(v))
    numeric_in_rest  = [sum(1 for v in row if _is_numeric(v)) for row in rest]

    avg_rest_numeric = sum(numeric_in_rest) / len(numeric_in_rest) if numeric_in_rest else 0

    # Header likely if: first row has fewer numerics than data rows
    return numeric_in_first < avg_rest_numeric * 0.5


def detect_kv(rows: list[list[str]], skip_first: bool = False) -> bool:
    """
    Heuristic: k:v format if >50% of middle tokens (not first, not last)
    contain a colon across sampled rows.
    """
    sample     = rows[1:] if skip_first else rows
    sample     = sample[:20]
    total      = 0
    kv_count   = 0

    for row in sample:
        middle = row[1:-1]
        for item in middle:
            if item.strip():
                total += 1
                if ':' in item:
                    kv_count += 1

    return (kv_count / total) > 0.5 if total > 0 else False


def _is_numeric(v: str) -> bool:
    try:
        float(v.strip())
        return True
    except ValueError:
        return False


# ══════════════════════════════════════════════════════════════
#  PARSING
# ══════════════════════════════════════════════════════════════

def parse_kv_row(row: list[str], has_header: bool = False,
                 header: list[str] | None = None) -> dict:
    """
    Format: id, key1:val1, ..., keyN:valN, timestamp
    Fixed anchors: first = id, last = timestamp, middle = k:v pairs.
    """
    row = [v.strip() for v in row]
    if len(row) < 2:
        return {'_raw': ','.join(row), '_error': 'too short'}

    record = {'id': row[0], 'timestamp': row[-1]}

    for item in row[1:-1]:
        if ':' in item:
            key, _, val = item.partition(':')
            record[key.strip()] = val.strip()
        elif item:
            record.setdefault('_unparsed', []).append(item)

    return record


def parse_flat_row(row: list[str], header: list[str]) -> dict:
    """Standard flat CSV — zip row values against header."""
    row = [v.strip() for v in row]
    # Pad short rows, truncate long rows
    row += [''] * max(0, len(header) - len(row))
    row  = row[:len(header)]
    return dict(zip(header, row))


def read_input(source: str | None) -> list[list[str]]:
    """Read from file path or stdin, return raw rows."""
    if source and Path(source).exists():
        text = Path(source).read_text()
    else:
        text = sys.stdin.read()

    reader = csv.reader(io.StringIO(text))
    return [row for row in reader if any(v.strip() for v in row)]


def build_header(raw_rows: list[list[str]], has_header: bool,
                 col_names: list[str] | None, is_kv: bool) -> list[str]:
    """
    Resolve column names for the final table.
    Priority: --col-names > first-row header > auto-generated.
    """
    if col_names:
        return col_names

    if has_header:
        return [v.strip() for v in raw_rows[0]]

    if is_kv:
        return []  # dynamic — discovered per row

    # Flat, no header — generate positional names
    max_cols = max(len(r) for r in raw_rows)
    return [f'col_{i}' for i in range(max_cols)]


# ══════════════════════════════════════════════════════════════
#  NORMALISER — produces list[dict] from raw rows
# ══════════════════════════════════════════════════════════════

def normalise(raw_rows: list[list[str]], has_header: bool,
              is_kv: bool, col_names: list[str] | None) -> list[dict]:

    header = build_header(raw_rows, has_header, col_names, is_kv)
    data_rows = raw_rows[1:] if has_header else raw_rows

    records = []
    for i, row in enumerate(data_rows, start=2 if has_header else 1):
        if is_kv:
            rec = parse_kv_row(row)
        else:
            rec = parse_flat_row(row, header)

        rec['_row'] = i
        records.append(rec)

    return records


# ══════════════════════════════════════════════════════════════
#  DUCKDB LOADER
# ══════════════════════════════════════════════════════════════

def load_to_duckdb(records: list[dict], con: duckdb.DuckDBPyConnection,
                   table: str = 'data') -> list[str]:
    """
    Infer schema from all records (union of keys), create table,
    insert rows. All columns are VARCHAR — cast in SQL as needed.
    Returns list of column names.
    """
    structural = {'_row', '_raw', '_error', '_unparsed'}

    # Collect all column names (preserving first-seen order)
    seen = {}
    for rec in records:
        for k in rec:
            if k not in structural and k not in seen:
                seen[k] = True
    columns = list(seen.keys())

    # DDL
    col_defs = ', '.join(f'"{c}" VARCHAR' for c in columns)
    col_defs += ', _row INTEGER'
    con.execute(f'DROP TABLE IF EXISTS {table}')
    con.execute(f'CREATE TABLE {table} ({col_defs})')

    # Insert
    col_list = ', '.join(f'"{c}"' for c in columns) + ', _row'
    placeholders = ', '.join(['?'] * (len(columns) + 1))

    for rec in records:
        vals = [str(rec.get(c, '')) if rec.get(c, '') != '' else None
                for c in columns]
        vals.append(rec.get('_row'))
        con.execute(f'INSERT INTO {table} ({col_list}) VALUES ({placeholders})', vals)

    return columns


# ══════════════════════════════════════════════════════════════
#  BUSINESS LOGIC HELPERS  (analyst-facing API)
# ══════════════════════════════════════════════════════════════

class Processor:
    """
    Thin wrapper around a DuckDB connection.
    Analysts call .sql() for ad-hoc queries and the helper methods
    for common patterns — filter, derive, aggregate, pivot, export.
    """

    def __init__(self, con: duckdb.DuckDBPyConnection, columns: list[str],
                 table: str = 'data'):
        self.con     = con
        self.columns = columns
        self.table   = table

    # ── Core ──────────────────────────────────────────────────

    def sql(self, query: str):
        """Run any SQL. Use `data` as the table name."""
        return self.con.execute(query).df()

    def preview(self, n: int = 10):
        """Show first n rows."""
        return self.sql(f'SELECT * FROM {self.table} LIMIT {n}')

    def schema(self):
        """Show column names and inferred types."""
        return self.sql(f'DESCRIBE {self.table}')

    def coverage(self):
        """How often each column has a non-null value."""
        total = self.con.execute(f'SELECT COUNT(*) FROM {self.table}').fetchone()[0]
        rows  = []
        for c in self.columns:
            count = self.con.execute(
                f'SELECT COUNT(*) FROM {self.table} WHERE "{c}" IS NOT NULL AND "{c}" != \'\''
            ).fetchone()[0]
            rows.append({'column': c, 'present': count,
                         'coverage_%': round(count / total * 100, 1) if total else 0})
        import pandas as pd
        return pd.DataFrame(rows)

    # ── Filter ────────────────────────────────────────────────

    def filter(self, where: str):
        """
        Return filtered rows as DataFrame.

        Example:
            p.filter("status = 'active' AND CAST(amount AS DOUBLE) >= 500")
        """
        return self.sql(f'SELECT * FROM {self.table} WHERE {where}')

    def create_view(self, name: str, where: str):
        """
        Persist a filtered view for chaining.

        Example:
            p.create_view('active', "status = 'active'")
            p.sql('SELECT * FROM active LIMIT 5')
        """
        self.con.execute(f'CREATE OR REPLACE VIEW {name} AS '
                         f'SELECT * FROM {self.table} WHERE {where}')
        print(f"✅ View '{name}' created — use it in subsequent .sql() calls")

    # ── Derive ────────────────────────────────────────────────

    def add_column(self, new_col: str, expr: str, source: str | None = None):
        """
        Add a derived column to the table (or a source view/table).

        Example:
            p.add_column('tier',
                \"\"\"CASE
                    WHEN CAST(amount AS DOUBLE) >= 10000 THEN 'PLATINUM'
                    WHEN CAST(amount AS DOUBLE) >= 5000  THEN 'GOLD'
                    WHEN CAST(amount AS DOUBLE) >= 1000  THEN 'SILVER'
                    ELSE 'BRONZE'
                END\"\"\")
        """
        tbl = source or self.table
        # Check if column already exists
        existing = [r[0] for r in self.con.execute(f'DESCRIBE {tbl}').fetchall()]
        if new_col in existing:
            self.con.execute(f'ALTER TABLE {tbl} DROP COLUMN "{new_col}"')
        self.con.execute(f'ALTER TABLE {tbl} ADD COLUMN "{new_col}" VARCHAR')
        self.con.execute(f'UPDATE {tbl} SET "{new_col}" = CAST(({expr}) AS VARCHAR)')
        self.columns.append(new_col)
        print(f"✅ Column '{new_col}' added")

    # ── Aggregate ─────────────────────────────────────────────

    def aggregate(self, group_by: str | list[str], agg_field: str,
                  func: str = 'SUM', source: str | None = None):
        """
        Group-by aggregation.

        Example:
            p.aggregate('region', 'amount', 'SUM')
            p.aggregate(['region', 'tier'], 'amount', 'AVG')
        """
        tbl = source or self.table
        if isinstance(group_by, list):
            gb = ', '.join(f'"{c}"' for c in group_by)
        else:
            gb = f'"{group_by}"'

        return self.sql(f"""
            SELECT {gb},
                   COUNT(*)                                      AS count,
                   ROUND({func}(TRY_CAST("{agg_field}" AS DOUBLE)), 2) AS {func.lower()}_{agg_field}
            FROM {tbl}
            WHERE "{agg_field}" IS NOT NULL AND "{agg_field}" != ''
            GROUP BY {gb}
            ORDER BY {func.lower()}_{agg_field} DESC
        """)

    def pivot(self, row_key: str, col_key: str, val: str,
              func: str = 'SUM', source: str | None = None):
        """
        Cross-tab two categorical keys.

        Example:
            p.pivot('region', 'tier', 'amount')
        """
        tbl = source or self.table
        col_vals = self.con.execute(
            f'SELECT DISTINCT "{col_key}" FROM {tbl} '
            f'WHERE "{col_key}" IS NOT NULL ORDER BY "{col_key}"'
        ).fetchall()
        col_vals = [r[0] for r in col_vals]

        cases = ', '.join(
            f"ROUND({func}(CASE WHEN \"{col_key}\" = '{v}' "
            f"THEN TRY_CAST(\"{val}\" AS DOUBLE) END), 2) AS \"{v}\""
            for v in col_vals
        )
        return self.sql(f"""
            SELECT "{row_key}", {cases}
            FROM {tbl}
            GROUP BY "{row_key}"
            ORDER BY "{row_key}"
        """)

    # ── Export ────────────────────────────────────────────────

    def export_csv(self, path: str, query: str | None = None):
        """Export query result (or full table) to CSV."""
        q = query or f'SELECT * FROM {self.table}'
        self.con.execute(f"COPY ({q}) TO '{path}' (HEADER, DELIMITER ',')")
        print(f"✅ Exported → {path}")

    def export_json(self, path: str, query: str | None = None):
        """Export query result (or full table) to JSON."""
        q    = query or f'SELECT * FROM {self.table}'
        rows = self.con.execute(q).df().to_dict(orient='records')
        Path(path).write_text(json.dumps(rows, indent=2, default=str))
        print(f"✅ Exported → {path}")

    def export_parquet(self, path: str, query: str | None = None):
        """Export to Parquet (great for large data, reload with DuckDB later)."""
        q = query or f'SELECT * FROM {self.table}'
        self.con.execute(f"COPY ({q}) TO '{path}' (FORMAT PARQUET)")
        print(f"✅ Exported → {path}")


# ══════════════════════════════════════════════════════════════
#  MAIN — ENTRY POINT
# ══════════════════════════════════════════════════════════════

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description='DuckDB CSV processor — handles file/stdin, '
                    'with/without header, with/without k:v pairs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument('file', nargs='?', help='CSV file path (omit to read stdin)')

    # Header options
    hg = ap.add_mutually_exclusive_group()
    hg.add_argument('--header',    dest='header', action='store_true',  default=None,
                    help='Force: first row is a header')
    hg.add_argument('--no-header', dest='header', action='store_false',
                    help='Force: no header row — all rows are data')

    # K:V options
    kg = ap.add_mutually_exclusive_group()
    kg.add_argument('--kv',    dest='kv', action='store_true',  default=None,
                    help='Force: middle columns are key:value pairs')
    kg.add_argument('--no-kv', dest='kv', action='store_false',
                    help='Force: plain flat CSV, no key:value pairs')

    ap.add_argument('--col-names', type=str, default=None,
                    help='Comma-separated column names (used when --no-header and --no-kv)')
    ap.add_argument('--table', default='data',
                    help='DuckDB table name (default: data)')
    ap.add_argument('--run-demo', action='store_true',
                    help='Run built-in demo business logic after loading')
    ap.add_argument('--interactive', action='store_true',
                    help='Drop into interactive SQL REPL after loading')

    return ap


def print_banner(has_header: bool, is_kv: bool, source: str,
                 n_records: int, columns: list[str]):
    print()
    print('━' * 58)
    print('  ⚙️  DuckDB CSV Processor')
    print('━' * 58)
    print(f'  Source      : {source}')
    print(f'  Header      : {"yes — first row used as column names" if has_header else "no  — positional / k:v names"}')
    print(f'  Format      : {"key:value pairs (id … k:v … timestamp)" if is_kv else "flat CSV"}')
    print(f'  Rows loaded : {n_records}')
    print(f'  Columns     : {", ".join(columns)}')
    print('━' * 58)
    print()


def demo_business_logic(p: Processor):
    """
    Example business logic — analysts copy, edit, and extend this.
    """
    print('\n── [DEMO] Key coverage ──────────────────────────────────')
    print(p.coverage().to_string(index=False))

    print('\n── [DEMO] Preview ───────────────────────────────────────')
    print(p.preview(5).to_string(index=False))

    print('\n── [DEMO] Add derived column: tier ──────────────────────')
    p.add_column('tier', """
        CASE
            WHEN TRY_CAST(amount AS DOUBLE) >= 10000 THEN 'PLATINUM'
            WHEN TRY_CAST(amount AS DOUBLE) >= 5000  THEN 'GOLD'
            WHEN TRY_CAST(amount AS DOUBLE) >= 1000  THEN 'SILVER'
            ELSE 'BRONZE'
        END
    """)

    print('\n── [DEMO] Filter: active + amount >= 500 ────────────────')
    filtered = p.filter("status = 'active' AND TRY_CAST(amount AS DOUBLE) >= 500")
    print(filtered.to_string(index=False))

    print('\n── [DEMO] Aggregate: SUM(amount) by region ──────────────')
    print(p.aggregate('region', 'amount', 'SUM').to_string(index=False))

    print('\n── [DEMO] Aggregate: AVG(amount) by tier ────────────────')
    print(p.aggregate('tier', 'amount', 'AVG').to_string(index=False))

    print('\n── [DEMO] Pivot: region × tier → SUM(amount) ────────────')
    print(p.pivot('region', 'tier', 'amount').to_string(index=False))

    print('\n── [DEMO] Ad-hoc SQL ────────────────────────────────────')
    result = p.sql("""
        SELECT
            region,
            tier,
            COUNT(*)                                   AS n,
            ROUND(SUM(TRY_CAST(amount AS DOUBLE)), 2)  AS total_amount,
            ROUND(AVG(TRY_CAST(amount AS DOUBLE)), 2)  AS avg_amount
        FROM data
        WHERE status = 'active'
        GROUP BY region, tier
        ORDER BY total_amount DESC
    """)
    print(result.to_string(index=False))


def interactive_repl(p: Processor):
    """Minimal SQL REPL — type EXIT to quit."""
    print('\n── Interactive SQL REPL ─────────────────────────────────')
    print("  Table: 'data'  |  Type EXIT to quit  |  \\schema for columns")
    print('─' * 58)
    while True:
        try:
            query = input('\nsql> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nBye.')
            break

        if not query:
            continue
        if query.upper() in ('EXIT', 'QUIT', '\\Q'):
            print('Bye.')
            break
        if query == '\\schema':
            print(p.schema().to_string(index=False))
            continue
        if query == '\\coverage':
            print(p.coverage().to_string(index=False))
            continue

        try:
            result = p.sql(query)
            print(result.to_string(index=False))
        except Exception as e:
            print(f'  ✗ {e}')


# ══════════════════════════════════════════════════════════════

def main():
    args = build_arg_parser().parse_args()

    # ── 1. Read input ─────────────────────────────────────────
    source    = args.file or 'stdin'
    raw_rows  = read_input(args.file)

    if not raw_rows:
        print('✗ No data found.', file=sys.stderr)
        sys.exit(1)

    # ── 2. Auto-detect or use flags ───────────────────────────
    has_header = args.header if args.header is not None else detect_header(raw_rows)
    is_kv      = args.kv     if args.kv     is not None else detect_kv(raw_rows, skip_first=has_header)

    col_names = [c.strip() for c in args.col_names.split(',')] \
                if args.col_names else None

    # ── 3. Normalise into list[dict] ──────────────────────────
    records = normalise(raw_rows, has_header, is_kv, col_names)

    # ── 4. Load into DuckDB ───────────────────────────────────
    con     = duckdb.connect()
    columns = load_to_duckdb(records, con, args.table)

    # ── 5. Banner ─────────────────────────────────────────────
    print_banner(has_header, is_kv, source, len(records), columns)

    # ── 6. Create Processor (analyst API) ─────────────────────
    p = Processor(con, columns, args.table)

    # ── 7. Optional demo / REPL ───────────────────────────────
    if args.run_demo:
        demo_business_logic(p)

    if args.interactive:
        interactive_repl(p)

    # ── 8. Return processor for import / notebook use ─────────
    return p


if __name__ == '__main__':
    main()