#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试脚本 - 验证配置和数据加载"""

import sys
import os

# 设置UTF-8编码输出
sys.stdout.reconfigure(encoding='utf-8')

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_analysis import load_config, read_stock_list, get_stock_list_path, load_stock_data

def main():
    print("=" * 50)
    print("测试配置加载")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    if config is None:
        print("配置加载失败!")
        return
    
    print("\n[成功] 配置文件加载成功")
    print(f"  - 数据目录: {config['data']['base_dir']}")
    
    # 获取清单路径
    stock_list_path = get_stock_list_path(config)
    print(f"  - 清单文件: {stock_list_path}")
    print(f"  - 文件存在: {os.path.exists(stock_list_path)}")
    
    print("\n" + "=" * 50)
    print("测试股票清单读取")
    print("=" * 50)
    
    # 读取股票清单
    stock_codes = read_stock_list(stock_list_path)
    print(f"\n[成功] 找到 {len(stock_codes)} 个股票代码")
    print(f"  - 前5个: {stock_codes[:5]}")
    
    print("\n" + "=" * 50)
    print("测试K线数据加载")
    print("=" * 50)
    
    # 测试加载数据
    test_code = stock_codes[0] if stock_codes else '603906'
    print(f"\n正在加载股票 {test_code} 的日线数据...")
    
    klines = load_stock_data(config, test_code, 'd', max_records=10)
    
    if klines:
        print(f"\n[成功] 加载了 {len(klines)} 条K线数据")
        print(f"  - 第一条: 时间={klines[0].timestamp}, 开盘={klines[0].open}, 收盘={klines[0].close}")
        print(f"  - 最后一条: 时间={klines[-1].timestamp}, 开盘={klines[-1].open}, 收盘={klines[-1].close}")
    else:
        print(f"\n[失败] 未能加载股票 {test_code} 的数据")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
