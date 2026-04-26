#!/usr/bin/env python3
"""Generate test fixture files with various encodings."""

from pathlib import Path

# Create fixtures directory
fixtures_dir = Path(__file__).parent / "test_data" / "encoding_samples"
fixtures_dir.mkdir(parents=True, exist_ok=True)

# UTF-8 sample
utf8_file = fixtures_dir / "sample_utf8.csv"
with open(utf8_file, 'w', encoding='utf-8') as f:
    f.write('name,age,city\n')
    f.write('Alice,30,New York\n')
    f.write('Bob,25,Los Angeles\n')
    f.write('Charlie,35,Chicago\n')
print(f"Created: {utf8_file}")

# CP949 sample (Korean)
cp949_file = fixtures_dir / "sample_cp949.csv"
with open(cp949_file, 'w', encoding='cp949') as f:
    f.write('이름,나이,도시\n')
    f.write('홍길동,30,서울\n')
    f.write('김철수,25,부산\n')
    f.write('이영호,35,대전\n')
print(f"Created: {cp949_file}")

# EUC-KR sample (Korean)
euckr_file = fixtures_dir / "sample_euckr.csv"
with open(euckr_file, 'w', encoding='euc-kr') as f:
    f.write('제품,가격,수량\n')
    f.write('사과,1000,5\n')
    f.write('바나나,2000,3\n')
    f.write('오렌지,1500,4\n')
print(f"Created: {euckr_file}")

# UTF-8 with BOM
utf8_bom_file = fixtures_dir / "sample_utf8_bom.csv"
with open(utf8_bom_file, 'w', encoding='utf-8-sig') as f:
    f.write('name,age,city\n')
    f.write('David,40,Boston\n')
    f.write('Emma,28,Seattle\n')
print(f"Created: {utf8_bom_file}")

print("\nAll encoding test fixtures generated successfully!")
