"""
K线数据模型
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class KLine:
    """K线数据对象"""
    
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    
    def is_positive(self) -> bool:
        """判断是否为阳线"""
        return self.close > self.open
    
    def is_negative(self) -> bool:
        """判断是否为阴线"""
        return self.close < self.open
    
    def get_body(self) -> float:
        """获取实体长度"""
        return abs(self.close - self.open)
    
    def get_upper_shadow(self) -> float:
        """获取上影线长度"""
        return self.high - max(self.open, self.close)
    
    def get_lower_shadow(self) -> float:
        """获取下影线长度"""
        return min(self.open, self.close) - self.low
    
    def get_total_length(self) -> float:
        """获取总长度"""
        return self.high - self.low


class KLineSeries:
    """K线序列"""
    
    def __init__(self, klines: list[KLine]):
        self.klines = klines
        self._sorted_klines = sorted(klines, key=lambda x: x.timestamp)
    
    def __len__(self) -> int:
        return len(self.klines)
    
    def __getitem__(self, index: int) -> KLine:
        return self._sorted_klines[index]
    
    def get_highs(self) -> list[float]:
        """获取所有高点"""
        return [k.high for k in self._sorted_klines]
    
    def get_lows(self) -> list[float]:
        """获取所有低点"""
        return [k.low for k in self._sorted_klines]
    
    def get_timestamps(self) -> list[datetime]:
        """获取所有时间戳"""
        return [k.timestamp for k in self._sorted_klines]
    
    def slice(self, start: int, end: int) -> 'KLineSeries':
        """切片操作"""
        return KLineSeries(self._sorted_klines[start:end])
    
    def find_peak(self, window: int = 3) -> list[int]:
        """寻找局部高点"""
        peaks = []
        n = len(self._sorted_klines)
        
        for i in range(window, n - window):
            is_peak = True
            for j in range(1, window + 1):
                if self._sorted_klines[i].high <= self._sorted_klines[i - j].high or \
                   self._sorted_klines[i].high <= self._sorted_klines[i + j].high:
                    is_peak = False
                    break
            if is_peak:
                peaks.append(i)
        
        return peaks
    
    def find_valley(self, window: int = 3) -> list[int]:
        """寻找局部低点"""
        valleys = []
        n = len(self._sorted_klines)
        
        for i in range(window, n - window):
            is_valley = True
            for j in range(1, window + 1):
                if self._sorted_klines[i].low >= self._sorted_klines[i - j].low or \
                   self._sorted_klines[i].low >= self._sorted_klines[i + j].low:
                    is_valley = False
                    break
            if is_valley:
                valleys.append(i)
        
        return valleys