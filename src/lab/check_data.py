import pandas as pd

# 데이터 파일 읽기
file_path = '주택종류별+주택-+읍면동(연도+끝자리+0,5),+시군구(그+외+연도)_20251028224837.xlsx'
df = pd.read_excel(file_path, nrows=10)

print('=== 데이터 기본 정보 ===')
print(f'Shape: {df.shape}')
print(f'\n컬럼 목록:')
for i, col in enumerate(df.columns, 1):
    print(f'{i}. {col}')

print(f'\n처음 3행:')
print(df.head(3).to_string())

print(f'\n데이터 타입:')
print(df.dtypes)
