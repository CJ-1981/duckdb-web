import duckdb
import os

csv_content = """id,age
1,30
2,
3,25
"""

with open('repro.csv', 'w') as f:
    f.write(csv_content)

conn = duckdb.connect(':memory:')
try:
    print("Trying read_csv_auto without options...")
    conn.execute("CREATE TABLE t1 AS SELECT * FROM read_csv_auto('repro.csv')")
    print("Success!")
    print(conn.execute("SELECT * FROM t1").df())
except Exception as e:
    print(f"Failed: {e}")

try:
    print("\nTrying read_csv_auto with nullstr=''...")
    conn.execute("CREATE TABLE t2 AS SELECT * FROM read_csv_auto('repro.csv', nullstr='')")
    print("Success!")
    print(conn.execute("SELECT * FROM t2").df())
except Exception as e:
    print(f"Failed: {e}")

os.remove('repro.csv')
