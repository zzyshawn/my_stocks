"""
数据加载和预处理工具
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional
from ..core.kline import KLine


class DataLoader:
    """数据加载器"""
    
    @staticmethod
    def create_sample_data(days: int = 100, start_price: float = 100.0) -> List[KLine]:
        """
        创建示例K线数据
        
        Args:
            days: 数据天数
            start_price: 起始价格
            
        Returns:
            K线数据列表
        """
        klines = []
        current_price = start_price
        
        # 生成随机波动
        np.random.seed(42)  # 固定随机种子确保可重复性
        
        for i in range(days):
            # 生成价格波动
            volatility = 0.02  # 2%波动率
            change = np.random.normal(0, volatility) * current_price
            
            # 生成K线数据
            open_price = current_price
            close_price = open_price + change
            
            # 生成高低点（确保高>低）
            high = max(open_price, close_price) + abs(np.random.normal(0, 0.005)) * current_price
            low = min(open_price, close_price) - abs(np.random.normal(0, 0.005)) * current_price
            
            # 确保高>低
            if high <= low:
                high, low = low + 0.01, high - 0.01
            
            # 生成时间戳
            timestamp = datetime.now() - timedelta(days=days - i)
            
            # 创建K线对象
            kline = KLine(
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=np.random.uniform(1000, 10000)
            )
            
            klines.append(kline)
            current_price = close_price
        
        return klines
    
    @staticmethod
    def load_from_dataframe(df: pd.DataFrame, 
                          timestamp_col: str = 'timestamp',
                          open_col: str = 'open',
                          high_col: str = 'high',
                          low_col: str = 'low',
                          close_col: str = 'close',
                          volume_col: Optional[str] = None) -> List[KLine]:
        """
        从pandas DataFrame加载K线数据
        
        Args:
            df: 包含K线数据的DataFrame
            timestamp_col: 时间戳列名
            open_col: 开盘价列名
            high_col: 最高价列名
            low_col: 最低价列名
            close_col: 收盘价列名
            volume_col: 成交量列名（可选）
            
        Returns:
            K线数据列表
        """
        klines = []
        
        for _, row in df.iterrows():
            # 处理时间戳
            timestamp = row[timestamp_col]
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()
            
            # 处理成交量
            volume = row[volume_col] if volume_col and volume_col in row else None
            
            kline = KLine(
                timestamp=timestamp,
                open=float(row[open_col]),
                high=float(row[high_col]),
                low=float(row[low_col]),
                close=float(row[close_col]),
                volume=volume
            )
            
            klines.append(kline)
        
        return klines
    
    @staticmethod
    def load_from_csv(filepath: str, **kwargs) -> List[KLine]:
        """
        从CSV文件加载K线数据
        
        Args:
            filepath: CSV文件路径
            **kwargs: 传递给load_from_dataframe的参数
            
        Returns:
            K线数据列表
        """
        df = pd.read_csv(filepath)
        return DataLoader.load_from_dataframe(df, **kwargs)
    
    @staticmethod
    def create_trend_data(trend_type: str = 'up', 
                         days: int = 100, 
                         start_price: float = 100.0) -> List[KLine]:
        """
        创建趋势明显的示例数据
        
        Args:
            trend_type: 趋势类型 ('up', 'down', 'consolidation')
            days: 数据天数
            start_price: 起始价格
            
        Returns:
            K线数据列表
        """
        klines = []
        current_price = start_price
        
        np.random.seed(42)
        
        for i in range(days):
            # 根据趋势类型调整波动
            if trend_type == 'up':
                trend_factor = 0.001  # 上升趋势
            elif trend_type == 'down':
                trend_factor = -0.001  # 下降趋势
            else:
                trend_factor = 0  # 震荡
            
            # 生成价格变化
            volatility = 0.015
            trend_change = trend_factor * current_price * (i / days)
            random_change = np.random.normal(0, volatility) * current_price
            change = trend_change + random_change
            
            open_price = current_price
            close_price = open_price + change
            
            # 生成高低点
            high = max(open_price, close_price) + abs(np.random.normal(0, 0.003)) * current_price
            low = min(open_price, close_price) - abs(np.random.normal(0, 0.003)) * current_price
            
            if high <= low:
                high, low = low + 0.01, high - 0.01
            
            timestamp = datetime.now() - timedelta(days=days - i)
            
            kline = KLine(
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=np.random.uniform(1000, 10000)
            )
            
            klines.append(kline)
            current_price = close_price
        
        return klines