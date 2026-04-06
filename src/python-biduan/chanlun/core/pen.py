"""
缠论笔数据结构
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from .kline import KLine


@dataclass
class Pen:
    """缠论笔对象"""
    
    start_kline: KLine  # 笔的起点K线
    end_kline: KLine    # 笔的终点K线
    direction: str      # 方向: 'up' 或 'down'
    klines: List[KLine] # 包含的所有K线
    
    def __post_init__(self):
        if self.direction not in ['up', 'down']:
            raise ValueError("方向必须是 'up' 或 'down'")
    
    @property
    def start_price(self) -> float:
        """笔的起始价格"""
        return self.start_kline.low if self.direction == 'up' else self.start_kline.high
    
    @property
    def end_price(self) -> float:
        """笔的结束价格"""
        return self.end_kline.high if self.direction == 'up' else self.end_kline.low
    
    @property
    def length(self) -> float:
        """笔的长度（价格差）"""
        return abs(self.end_price - self.start_price)
    
    @property
    def duration(self) -> float:
        """笔的持续时间（K线数量）"""
        return len(self.klines)
    
    def is_valid(self) -> bool:
        """验证笔的有效性"""
        if len(self.klines) < 5:
            return False
        
        if self.direction == 'up':
            return self.end_price > self.start_price
        else:
            return self.end_price < self.start_price
    
    def contains_kline(self, kline: KLine) -> bool:
        """判断是否包含指定K线"""
        return kline in self.klines
    
    def get_extreme_price(self) -> float:
        """获取极值价格"""
        if self.direction == 'up':
            return max(k.high for k in self.klines)
        else:
            return min(k.low for k in self.klines)


class PenSeries:
    """笔序列"""
    
    def __init__(self, pens: List[Pen]):
        self.pens = pens
    
    def __len__(self) -> int:
        return len(self.pens)
    
    def __getitem__(self, index: int) -> Pen:
        return self.pens[index]
    
    def get_high_pens(self) -> List[Pen]:
        """获取所有向上笔"""
        return [pen for pen in self.pens if pen.direction == 'up']
    
    def get_low_pens(self) -> List[Pen]:
        """获取所有向下笔"""
        return [pen for pen in self.pens if pen.direction == 'down']
    
    def get_peaks(self) -> List[float]:
        """获取所有笔的高点"""
        peaks = []
        for pen in self.pens:
            if pen.direction == 'up':
                peaks.append(pen.end_price)
            else:
                peaks.append(pen.start_price)
        return peaks
    
    def get_valleys(self) -> List[float]:
        """获取所有笔的低点"""
        valleys = []
        for pen in self.pens:
            if pen.direction == 'up':
                valleys.append(pen.start_price)
            else:
                valleys.append(pen.end_price)
        return valleys
    
    def find_pen_by_kline(self, kline: KLine) -> Optional[Pen]:
        """根据K线查找所属的笔"""
        for pen in self.pens:
            if pen.contains_kline(kline):
                return pen
        return None