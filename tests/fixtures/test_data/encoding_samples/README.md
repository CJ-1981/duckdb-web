# Encoding Test Fixtures

This directory contains sample CSV files in various encodings for testing the encoding detector module.

## Files

- `sample_utf8.csv` - UTF-8 encoded CSV with English content
- `sample_cp949.csv` - CP949 encoded CSV with Korean content
- `sample_euckr.csv` - EUC-KR encoded CSV with Korean content
- `sample_utf8_bom.csv` - UTF-8 with BOM marker

## Encoding Generation

To generate these test files:

```python
# UTF-8
with open('sample_utf8.csv', 'w', encoding='utf-8') as f:
    f.write('name,age,city\n')
    f.write('Alice,30,New York\n')
    f.write('Bob,25,Los Angeles\n')

# CP949
with open('sample_cp949.csv', 'w', encoding='cp949') as f:
    f.write('이름,나이,도시\n')
    f.write('홍길동,30,서울\n')
    f.write('김철수,25,부산\n')

# EUC-KR
with open('sample_euckr.csv', 'w', encoding='euc-kr') as f:
    f.write('이름,나이,도시\n')
    f.write('이영호,30,대전\n')
    f.write('박민수,25,광주\n')

# UTF-8 with BOM
with open('sample_utf8_bom.csv', 'w', encoding='utf-8-sig') as f:
    f.write('name,age,city\n')
    f.write('Charlie,35,Chicago\n')
```
