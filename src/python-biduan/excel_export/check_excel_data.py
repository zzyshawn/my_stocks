"""
查看Excel文件内容
"""
import pandas as pd

file_path = "X:\\股票信息\\股票数据库\\daban\\股票数据\\603906\\603906_d.xlsx"

df = pd.read_excel(file_path)

print("=== Excel文件信息 ===")
print(f"列名: {list(df.columns)}")
print(f"行数: {len(df)}")
print("\n=== 前10行数据 ===")
print(df.head(10))
print("\n=== 后10行数据 ===")
print(df.tail(10))
print("\n=== 日期列数据类型 ===")
print(df['日期'].dtype)
print("\n=== 日期列的前几个值 ===")
for i in range(5):
    print(f"第{i+1}行日期: {df['日期'].iloc[i]}, 类型: {type(df['日期'].iloc[i])}")
