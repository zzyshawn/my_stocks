"""
缠论线段数据结构
"""

from dataclasses import dataclass
from typing import List, Optional
from .pen import Pen


@dataclass
class Segment:
    """缠论线段对象"""
    
    start_pen: Pen      # 线段的起始笔
    end_pen: Pen        # 线段的结束笔
    direction: str      # 方向: 'up' 或 'down'
    pens: List[Pen]     # 包含的所有笔
    
    def __post_init__(self):
        if self.direction not in ['up', 'down']:
            raise ValueError("方向必须是 'up' 或 'down'")
    
    @property
    def start_price(self) -> float:
        """线段的起始价格"""
        return self.start_pen.start_price if self.direction == 'up' else self.start_pen.start_price
    
    @property
    def end_price(self) -> float:
        """线段的结束价格"""
        return self.end_pen.end_price if self.direction == 'up' else self.end_pen.end_price
    
    @property
    def length(self) -> float:
        """线段的长度（价格差）"""
        return abs(self.end_price - self.start_price)
    
    @property
    def duration(self) -> int:
        """线段的持续时间（笔的数量）"""
        return len(self.pens)
    
    def is_valid(self) -> bool:
        """验证线段的有效性"""
        if len(self.pens) < 3:
            return False
        
        # 检查方向一致性
        for i in range(len(self.pens) - 1):
            if self.pens[i].direction == self.pens[i + 1].direction:
                return False
        
        if self.direction == 'up':
            return self.end_price > self.start_price
        else:
            return self.end_price < self.start_price
    
    def contains_pen(self, pen: Pen) -> bool:
        """判断是否包含指定笔"""
        return pen in self.pens
    
    def get_extreme_price(self) -> float:
        """获取极值价格"""
        if self.direction == 'up':
            return max(pen.end_price for pen in self.pens if pen.direction == 'up')
        else:
            return min(pen.end_price for pen in self.pens if pen.direction == 'down')
    
    def get_pivot_range(self) -> tuple[float, float]:
        """获取线段的价格区间"""
        if self.direction == 'up':
            return self.start_price, self.end_price
        else:
            return self.end_price, self.start_price


class SegmentSeries:
    """线段序列"""
    
    def __init__(self, segments: List[Segment]):
        self.segments = segments
    
    def __len__(self) -> int:
        return len(self.segments)
    
    def __getitem__(self, index: int) -> Segment:
        return self.segments[index]
    
    def get_up_segments(self) -> List[Segment]:
        """获取所有向上线段"""
        return [seg for seg in self.segments if seg.direction == 'up']
    
    def get_down_segments(self) -> List[Segment]:
        """获取所有向下线段"""
        return [seg for seg in self.segments if seg.direction == 'down']
    
    def find_segment_by_pen(self, pen: Pen) -> Optional[Segment]:
        """根据笔查找所属的线段"""
        for seg in self.segments:
            if seg.contains_pen(pen):
                return seg
        return None
    
    def get_segment_boundaries(self) -> List[float]:
        """获取所有线段的边界价格"""
        boundaries = []
        for seg in self.segments:
            boundaries.append(seg.start_price)
            boundaries.append(seg.end_price)
        return boundaries