"""
筹码分布导出模块

提供筹码分布计算和导出到 Excel 的功能
"""

import os
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime

from ..core.kline import KLine
from .indicators import TechnicalIndicators


def export_chip_distribution(
    stock_code: str,
    klines_5min: List[KLine],
    target_klines: List[KLine],
    period_type: str,
    lookback: int = 1,
    price_bins: int = 50,
    output_dir: str = None
) -> str:
    """
    导出筹码分布到 Excel 文件
    
    Args:
        stock_code: 股票代码
        klines_5min: 5分钟K线数据
        target_klines: 目标周期K线（日线或30分钟）
        period_type: 周期类型 ("daily" 或 "min30")
        lookback: 回看周期数（1-100）
        price_bins: 价格区间数量
        output_dir: 输出目录
        
    Returns:
        输出文件路径
    """
    if not target_klines:
        print(f"股票 {stock_code} 没有目标周期数据")
        return None
    
    # 获取最后一个目标K线的时间戳作为目标时间
    target_timestamp = target_klines[-1].timestamp
    
    # 计算筹码分布
    chip_result = TechnicalIndicators.calculate_chip_distribution(
        klines_5min=klines_5min,
        target_timestamp=target_timestamp,
        lookback=lookback,
        price_bins=price_bins
    )
    
    # 创建输出目录
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "chip_output")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名
    filename = f"{stock_code}_{period_type}_chip_lookback{lookback}.xlsx"
    file_path = os.path.join(output_dir, filename)
    
    # 创建 Excel writer
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # Sheet 1: 筹码分布明细
        chip_data = []
        total_volume = sum(chip_result['volumes'])
        
        for price, volume in zip(chip_result['prices'], chip_result['volumes']):
            ratio = volume / total_volume if total_volume > 0 else 0
            chip_data.append({
                '价格区间': round(price, 2),
                '成交量': round(volume, 0),
                '成交占比': f"{ratio:.2%}",
                '累计占比': 0  # 后面计算
            })
        
        # 计算累计占比
        cumulative = 0
        for item in chip_data:
            ratio = float(item['成交占比'].strip('%')) / 100
            cumulative += ratio
            item['累计占比'] = f"{cumulative:.2%}"
        
        df_chip = pd.DataFrame(chip_data)
        df_chip.to_excel(writer, sheet_name='筹码分布', index=False)
        
        # Sheet 2: 统计指标
        stats_data = [
            {'指标': '平均成本', '值': round(chip_result['avg_cost'], 2)},
            {'指标': '当前价格', '值': round(chip_result['current_price'], 2)},
            {'指标': '获利比例', '值': f"{chip_result['profit_ratio']:.2%}"},
            {'指标': '集中度', '值': f"{chip_result['concentration']:.2%}"},
            {'指标': '90%筹码区间-低', '值': round(chip_result['chip_90_range'][0], 2)},
            {'指标': '90%筹码区间-高', '值': round(chip_result['chip_90_range'][1], 2)},
            {'指标': '70%筹码区间-低', '值': round(chip_result['chip_70_range'][0], 2)},
            {'指标': '70%筹码区间-高', '值': round(chip_result['chip_70_range'][1], 2)},
            {'指标': '回看周期数', '值': lookback},
            {'指标': '目标时间', '值': target_timestamp.strftime('%Y-%m-%d %H:%M:%S')},
            {'指标': '5分钟K线数量', '值': len(klines_5min)},
        ]
        
        df_stats = pd.DataFrame(stats_data)
        df_stats.to_excel(writer, sheet_name='统计指标', index=False)
    
    print(f"筹码分布已导出: {file_path}")
    return file_path


def export_chip_distribution_multiple(
    stock_code: str,
    klines_5min: List[KLine],
    target_klines: List[KLine],
    period_type: str,
    lookbacks: List[int] = None,
    price_bins: int = 50,
    output_dir: str = None
) -> List[str]:
    """
    导出多个回看周期的筹码分布
    
    Args:
        stock_code: 股票代码
        klines_5min: 5分钟K线数据
        target_klines: 目标周期K线
        period_type: 周期类型
        lookbacks: 回看周期数列表，默认[1, 5, 10]
        price_bins: 价格区间数量
        output_dir: 输出目录
        
    Returns:
        输出文件路径列表
    """
    if lookbacks is None:
        lookbacks = [1, 5, 10]
    
    output_files = []
    for lookback in lookbacks:
        file_path = export_chip_distribution(
            stock_code=stock_code,
            klines_5min=klines_5min,
            target_klines=target_klines,
            period_type=period_type,
            lookback=lookback,
            price_bins=price_bins,
            output_dir=output_dir
        )
        if file_path:
            output_files.append(file_path)
    
    return output_files
