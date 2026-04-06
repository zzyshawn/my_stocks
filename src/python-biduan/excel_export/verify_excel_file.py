"""
验证导出的Excel文件是否包含"包含起始日期"列
"""

import os
import pandas as pd

def verify_excel_file():
    """
    验证导出的Excel文件是否包含"包含起始日期"列
    """
    stock_code = "603906"
    data_type = "d"
    
    # 导出的Excel文件路径
    excel_file = f"X:\\股票信息\\股票数据库\\daban\\股票数据\\{stock_code}\\{stock_code}_d_analysis.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"Excel文件不存在: {excel_file}")
        return
    
    print(f"验证Excel文件: {excel_file}")
    
    # 读取Excel文件
    df = pd.read_excel(excel_file)
    
    # 检查是否包含"包含起始日期"列
    if '包含起始日期' not in df.columns:
        print("❌ Excel文件中不存在'包含起始日期'列")
        return
    
    print("✅ Excel文件中存在'包含起始日期'列")
    
    # 检查列顺序
    columns = df.columns.tolist()
    print("\n列顺序:")
    for i, col in enumerate(columns):
        print(f"{i+1}. {col}")
    
    # 检查包含起始日期的数据
    print("\n包含起始日期数据检查:")
    
    # 找出包含起始日期不为空的行
    has_start_date = df[df['包含起始日期'].notna()]
    print(f"包含起始日期不为空的行数: {len(has_start_date)}")
    
    # 显示前10行数据
    print("\n前10行数据:")
    print(df.head(10))
    
    # 检查包含起始日期与K线状态的对应关系
    print("\n包含起始日期与K线状态对应关系:")
    for kline_state in ['上升', '下降', '上升包含', '下降包含']:
        if kline_state in df['K线状态'].values:
            state_rows = df[df['K线状态'] == kline_state]
            has_start_date_rows = state_rows[state_rows['包含起始日期'].notna()]
            print(f"{kline_state}: 总{len(state_rows)}行, 包含起始日期{len(has_start_date_rows)}行")
    
    print(f"\n✅ Excel文件验证完成: {excel_file}")


if __name__ == "__main__":
    verify_excel_file()