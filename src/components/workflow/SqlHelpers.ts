export function buildSql(subtype: string, cfg: any): string {
  const T = '<prev_table>';
  switch (subtype) {
    case 'filter': {
      if (cfg?.isAdvanced && cfg?.customWhere) {
        return `SELECT *\nFROM ${T}\nWHERE ${cfg.customWhere}`;
      }
      const col = cfg?.column ? `"${cfg.column}"` : '/* column */';
      const op = cfg?.operator || '==';
      const val = String(cfg?.value || '');
      const opMap: Record<string, string> = {
        '==': `${col} = '${val}'`, '!=': `${col} != '${val}'`,
        '>': `${col} > ${val}`, '<': `${col} < ${val}`,
        '>=': `${col} >= ${val}`, '<=': `${col} <= ${val}`,
        'contains': `${col} ILIKE '%${val}%'`,
        'not_contains': `${col} NOT ILIKE '%${val}%'`,
        'starts_with': `${col} ILIKE '${val}%'`,
        'ends_with': `${col} ILIKE '%${val}'`,
        'is_null': `${col} IS NULL`, 'is_not_null': `${col} IS NOT NULL`,
        'in': `${col} IN (${val})`, 'not_in': `${col} NOT IN (${val})`,
      };
      return `SELECT *\nFROM ${T}\nWHERE ${opMap[op] ?? `${col} ${op} '${val}'`}`;
    }
    case 'combine': {
      const jt = (cfg?.joinType || 'inner').toUpperCase();
      if (['UNION', 'UNION ALL', 'APPEND'].includes(jt)) {
        return `SELECT * FROM <left_table>\nUNION ALL\nSELECT * FROM <right_table>`;
      }
      const lc = cfg?.leftColumn ? `"${cfg.leftColumn}"` : '/* left_key */';
      const rc = cfg?.rightColumn ? `"${cfg.rightColumn}"` : '/* right_key */';
      return `SELECT *\nFROM <left_table>\n${jt} JOIN <right_table>\n  ON <left_table>.${lc} = <right_table>.${rc}`;
    }
    case 'clean': {
      const col = cfg?.column || '/* column */';
      const op = cfg?.operation || 'trim';
      const exprMap: Record<string, string> = {
        trim: `TRIM(CAST("${col}" AS VARCHAR))`,
        upper: `UPPER(CAST("${col}" AS VARCHAR))`,
        lower: `LOWER(CAST("${col}" AS VARCHAR))`,
        numeric: `REGEXP_REPLACE(CAST("${col}" AS VARCHAR), '[^0-9.]', '', 'g')`,
        replace_null: `COALESCE(NULLIF(CAST("${col}" AS VARCHAR), ''), '${cfg?.newValue || ''}')`,
        to_date: `TRY_CAST("${col}" AS DATE)`,
      };
      return `SELECT * REPLACE (\n  ${exprMap[op] ?? `"${col}"`} AS "${col}"\n)\nFROM ${T}`;
    }
    case 'aggregate': {
      const groups = (cfg?.groupBy || '').split(',').map((c: string) => c.trim()).filter(Boolean);
      const aggs: any[] = cfg?.aggregations || [];
      const aggParts = aggs.length
        ? aggs.map((a: any) => `${(a.operation || 'COUNT').toUpperCase()}("${a.column || '*'}") AS "${a.alias || 'agg'}"`)
        : ['COUNT(*) AS count_all'];
      const sel = [...groups.map((c: string) => `"${c}"`), ...aggParts].join(',\n  ');
      const gb = groups.length ? `\nGROUP BY ${groups.map((c: string) => `"${c}"`).join(', ')}` : '';
      return `SELECT\n  ${sel}\nFROM ${T}${gb}`;
    }
    case 'sort': {
      const col = cfg?.column ? `"${cfg.column}"` : '/* column */';
      const dir = (cfg?.direction || 'asc').toUpperCase();
      return `SELECT *\nFROM ${T}\nORDER BY ${col} ${dir}`;
    }
    case 'limit':
      return `SELECT *\nFROM ${T}\nLIMIT ${cfg?.count || 100}`;
    case 'select': {
      const cols = (cfg?.columns || '').split(',').map((c: string) => `"${c.trim()}"`).filter((c: string) => c !== '""');
      return `SELECT ${cols.length ? cols.join(', ') : '*'}\nFROM ${T}`;
    }
    case 'computed': {
      const expr = cfg?.expression || '/* expression */';
      const alias = cfg?.alias || 'new_column';
      return `SELECT *,\n  ${expr} AS "${alias}"\nFROM ${T}`;
    }
    case 'rename': {
      const maps: any[] = cfg?.mappings || [];
      const items = maps.filter((m: any) => m.old && m.new).map((m: any) => `"${m.old}" AS "${m.new}"`);
      return `SELECT * REPLACE (\n  ${items.length ? items.join(',\n  ') : '/* add mappings */'}\n)\nFROM ${T}`;
    }
    case 'distinct': {
      const cols = (cfg?.columns || '').split(',').map((c: string) => `"${c.trim()}"`).filter((c: string) => c !== '""');
      return `SELECT DISTINCT ${cols.length ? cols.join(', ') : '*'}\nFROM ${T}`;
    }
    case 'case_when': {
      const conds: any[] = cfg?.conditions || [];
      const alias = cfg?.alias || 'case_result';
      const elsePart = cfg?.elseValue || 'NULL';
      const whenLines = conds.filter((c: any) => c.when && c.then)
        .map((c: any) => `  WHEN ${c.when} THEN '${c.then}'`).join('\n') || '  WHEN /* condition */ THEN /* value */';
      return `SELECT *,\n  CASE\n${whenLines}\n  ELSE ${elsePart}\n  END AS "${alias}"\nFROM ${T}`;
    }
    case 'window': {
      const fn = cfg?.function || 'ROW_NUMBER()';
      const partition = cfg?.partitionBy ? `PARTITION BY ${cfg.partitionBy.split(',').map((c: string) => `"${c.trim()}"`).join(', ')}` : '';
      const order = cfg?.orderBy ? `ORDER BY ${cfg.orderBy.split(',').map((c: string) => `"${c.trim()}"`).join(', ')}` : '';
      const over = [partition, order].filter(Boolean).join(' ');
      const alias = cfg?.alias || 'window_result';
      return `SELECT *,\n  ${fn} OVER (${over}) AS "${alias}"\nFROM ${T}`;
    }
    case 'pivot': {
      const on = cfg?.on ? `"${cfg.on}"` : '/* column to pivot */';
      const using = cfg?.using || 'sum(/* value_column */)';
      const groupBy = cfg?.groupBy ? cfg.groupBy.split(',').map((c: string) => `"${c.trim()}"`).join(', ') : '/* columns to keep */';
      return `PIVOT ${T}\nON ${on}\nUSING ${using}\nGROUP BY ${groupBy}`;
    }
    case 'unpivot': {
      const on = cfg?.on ? cfg.on.split(',').map((c: string) => `"${c.trim()}"`).join(', ') : '/* columns to unpivot */';
      const name = cfg?.intoName ? `"${cfg.intoName}"` : '"name"';
      const value = cfg?.intoValue ? `"${cfg.intoValue}"` : '"value"';
      return `UNPIVOT ${T}\nON ${on}\nINTO\n  NAME ${name}\n  VALUE ${value}`;
    }
    case 'sample': {
      const method = cfg?.method || 'PERCENT';
      const value = cfg?.value || 10;
      return `SELECT *\nFROM ${T}\nUSING SAMPLE ${value} ${method}`;
    }
    case 'unnest': {
      const col = cfg?.column ? `"${cfg.column}"` : '/* column */';
      return `SELECT * EXCLUDE (${col}), UNNEST(${col}) AS "${cfg?.alias || 'unnested_value'}"\nFROM ${T}`;
    }
    case 'raw_sql':
      return cfg?.sql ? cfg.sql.replace(/\{\{input\}\}/g, T) : `SELECT * FROM ${T}`;
    default:
      return '';
  }
}

export function getConditionSql(col: string, op: string, val: string): string {
  const column = col ? `"${col}"` : '/* column */';
  const value = val || '';
  const opMap: Record<string, string> = {
    '==': `${column} = '${value}'`,
    '!=': `${column} != '${value}'`,
    '>': `${column} > ${value}`,
    '<': `${column} < ${value}`,
    '>=': `${column} >= ${value}`,
    '<=': `${column} <= ${value}`,
    'contains': `${column} ILIKE '%${value}%'`,
    'not_contains': `${column} NOT ILIKE '%${value}%'`,
    'starts_with': `${column} ILIKE '${value}%'`,
    'ends_with': `${column} ILIKE '%${value}'`,
    'is_null': `${column} IS NULL`,
    'is_not_null': `${column} IS NOT NULL`,
    'in': `${column} IN (${value})`,
    'not_in': `${column} NOT IN (${value})`,
  };
  return opMap[op] ?? `${column} ${op} '${value}'`;
}
