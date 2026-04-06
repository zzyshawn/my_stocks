"""
缠论中枢数据结构
"""

from dataclasses import dataclass, field
from typing import List, Tuple
from .segment import Segment
from .pen import Pen
from .kline import KLine


@dataclass
class CentralPivot:
    """缠论中枢对象"""
    
    zg: float           # 中枢高点
    zd: float           # 中枢低点
    gg: float           # 中枢最高点
    dd: float           # 中枢最低点
    segments: List[Segment] = field(default_factory=list)  # 构成中枢的线段（传统方法）
    pens: List[Pen] = field(default_factory=list)  # 构成中枢的笔（4.3.4 方法）
    start_kline: KLine = None  # 中枢起始 K 线
    end_kline: KLine = None    # 中枢结束 K 线
    
    def __post_init__(self):
        if self.zg is not None and self.zd is not None and self.zg <= self.zd:
            raise ValueError("中枢高点 (zg) 必须大于中枢低点 (zd)")
        if self.gg is not None and self.zg is not None and self.gg < self.zg:
            raise ValueError("中枢最高点 (gg) 必须大于等于中枢高点 (zg)")
        if self.dd is not None and self.zd is not None and self.dd > self.zd:
            raise ValueError("中枢最低点 (dd) 必须小于等于中枢低点 (zd)")
    
    @property
    def height(self) -> float:
        """中枢高度"""
        return self.zg - self.zd
    
    @property
    def range_height(self) -> float:
        """中枢区间高度"""
        return self.gg - self.dd
    
    @property
    def center(self) -> float:
        """中枢中心价格"""
        return (self.zg + self.zd) / 2
    
    def is_price_in_pivot(self, price: float) -> bool:
        """判断价格是否在中枢内"""
        return self.zd <= price <= self.zg
    
    def is_price_above_pivot(self, price: float) -> bool:
        """判断价格是否在中枢上方"""
        return price > self.zg
    
    def is_price_below_pivot(self, price: float) -> bool:
        """判断价格是否在中枢下方"""
        return price < self.zd
    
    def get_pivot_range(self) -> Tuple[float, float]:
        """获取中枢价格区间"""
        return self.zd, self.zg
    
    def get_extreme_range(self) -> Tuple[float, float]:
        """获取中枢极值区间"""
        return self.dd, self.gg
    
    def is_expanding(self, other: 'CentralPivot') -> bool:
        """判断是否相对于另一个中枢扩张"""
        return self.gg > other.gg and self.dd < other.dd
    
    def is_contracting(self, other: 'CentralPivot') -> bool:
        """判断是否相对于另一个中枢收缩"""
        return self.gg < other.gg and self.dd > other.dd


class CentralPivotSeries:
    """中枢序列"""
    
    def __init__(self, pivots: List[CentralPivot]):
        self.pivots = pivots
    
    def __len__(self) -> int:
        return len(self.pivots)
    
    def __getitem__(self, index: int) -> CentralPivot:
        return self.pivots[index]
    
    def get_pivot_by_price(self, price: float) -> List[CentralPivot]:
        """根据价格查找相关中枢"""
        return [pivot for pivot in self.pivots if pivot.is_price_in_pivot(price)]
    
    def get_pivots_above_price(self, price: float) -> List[CentralPivot]:
        """获取价格上方的中枢"""
        return [pivot for pivot in self.pivots if pivot.zd > price]
    
    def get_pivots_below_price(self, price: float) -> List[CentralPivot]:
        """获取价格下方的中枢"""
        return [pivot for pivot in self.pivots if pivot.zg < price]
    
    def get_latest_pivot(self) -> CentralPivot:
        """获取最新的中枢"""
        if not self.pivots:
            raise ValueError("中枢序列为空")
        return self.pivots[-1]
    
    def find_overlapping_pivots(self) -> List[Tuple[CentralPivot, CentralPivot]]:
        """查找重叠的中枢"""
        overlapping = []
        n = len(self.pivots)
        
        for i in range(n):
            for j in range(i + 1, n):
                pivot1 = self.pivots[i]
                pivot2 = self.pivots[j]
                
                # 检查中枢是否重叠
                if (pivot1.zd <= pivot2.zg and pivot1.zg >= pivot2.zd) or \
                   (pivot2.zd <= pivot1.zg and pivot2.zg >= pivot1.zd):
                    overlapping.append((pivot1, pivot2))
        
        return overlapping