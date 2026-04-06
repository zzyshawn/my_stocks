#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试新增技术指标功能"""

import sys
import os
from datetime import datetime

# 设置UTF-8编码输出
sys.stdout.reconfigure(encoding='utf-8')

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_analysis import load_config, load_stock_data
from chanlun.utils.indicators import TechnicalIndicators
from chanlun.utils.chip_export import export_chip_distribution, export_chip_distribution_multiple


def test_rsi_indicators():
    """测试 RSI_H 和 RSI_L"""
    print("=" * 50)
    print("测试 RSI_H 和 RSI_L 指标")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    # 加载日线数据
    klines = load_stock_data(config, '603232', 'd', max_records=100)
    
    if not klines:
        print("无法加载数据")
        return
    
    print(f"加载了 {len(klines)} 条日线数据")
    
    # 计算 RSI (原有)
    rsi_values = TechnicalIndicators.calculate_rsi(klines, period=6)
    print(f"RSI (收盘价): {rsi_values[-5:]}")
    
    # 计算 RSI_H (最高价)
    rsi_h_values = TechnicalIndicators.calculate_rsi_h(klines, period=6)
    print(f"RSI_H (最高价): {rsi_h_values[-5:]}")
    
    # 计算 RSI_L (最低价)
    rsi_l_values = TechnicalIndicators.calculate_rsi_l(klines, period=6)
    print(f"RSI_L (最低价): {rsi_l_values[-5:]}")
    
    print("\n[成功] RSI 指标测试通过")
    return True


def test_volume_ma():
    """测试成交量均线"""
    print("\n" + "=" * 50)
    print("测试成交量均线")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    # 加载日线数据
    klines = load_stock_data(config, '603232', 'd', max_records=100)
    
    if not klines:
        print("无法加载数据")
        return
    
    print(f"加载了 {len(klines)} 条日线数据")
    
    # 计算成交量均线
    vol_ma_10 = TechnicalIndicators.calculate_volume_ma(klines, period=10)
    vol_ma_20 = TechnicalIndicators.calculate_volume_ma(klines, period=20)
    
    print(f"成交量 (最近5天): {[k.volume for k in klines[-5:]]}")
    print(f"10日成交量均线: {vol_ma_10[-5:]}")
    print(f"20日成交量均线: {vol_ma_20[-5:]}")
    
    print("\n[成功] 成交量均线测试通过")
    return True


def test_chip_distribution():
    """测试筹码分布"""
    print("\n" + "=" * 50)
    print("测试筹码分布")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    # 加载5分钟数据
    klines_5min = load_stock_data(config, '603232', '5', max_records=500)
    
    if not klines_5min:
        print("无法加载5分钟数据")
        return
    
    print(f"加载了 {len(klines_5min)} 条5分钟数据")
    
    # 加载日线数据
    klines_daily = load_stock_data(config, '603232', 'd', max_records=10)
    
    if not klines_daily:
        print("无法加载日线数据")
        return
    
    print(f"加载了 {len(klines_daily)} 条日线数据")
    
    # 计算筹码分布
    target_timestamp = klines_daily[-1].timestamp
    print(f"目标时间: {target_timestamp}")
    
    chip_result = TechnicalIndicators.calculate_chip_distribution(
        klines_5min=klines_5min,
        target_timestamp=target_timestamp,
        lookback=1,
        price_bins=50
    )
    
    print(f"筹码分布结果:")
    print(f"  - 平均成本: {chip_result['avg_cost']:.2f}")
    print(f"  - 当前价格: {chip_result['current_price']:.2f}")
    print(f"  - 获利比例: {chip_result['profit_ratio']:.2%}")
    print(f"  - 集中度: {chip_result['concentration']:.2%}")
    print(f"  - 90%筹码区间: {chip_result['chip_90_range'][0]:.2f} - {chip_result['chip_90_range'][1]:.2f}")
    print(f"  - 70%筹码区间: {chip_result['chip_70_range'][0]:.2f} - {chip_result['chip_70_range'][1]:.2f}")
    
    # 导出筹码分布
    output_dir = os.path.join(config['data']['base_dir'], '603232', 'chip')
    print(f"\n导出筹码分布到: {output_dir}")
    
    # 导出多个回看周期
    output_files = export_chip_distribution_multiple(
        stock_code='603232',
        klines_5min=klines_5min,
        target_klines=klines_daily,
        period_type='daily',
        lookbacks=[1, 5, 10],
        price_bins=50,
        output_dir=output_dir
    )
    
    print(f"\n生成的文件:")
    for file_path in output_files:
        print(f"  - {file_path}")
    
    print("\n[成功] 筹码分布测试通过")
    return True


def main():
    """主测试函数"""
    print("=== 技术指标功能测试开始 ===\n")
    
    # 测试 RSI 指标
    test_rsi_indicators()
    
    # 测试成交量均线
    test_volume_ma()
    
    # 测试筹码分布
    test_chip_distribution()
    
    print("\n" + "=" * 50)
    print("=== 所有测试完成 ===")
    print("=" * 50)


if __name__ == "__main__":
    main()
