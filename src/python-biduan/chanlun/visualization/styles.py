"""
缠论图表样式配置
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class ChartStyles:
    """缠论图表样式配置类"""
    
    # K线样式
    kline_up_color: str = "red"
    kline_down_color: str = "green"
    kline_linewidth: float = 1.0
    kline_alpha: float = 0.8
    
    # 笔样式
    pen_up_color: str = "blue"
    pen_down_color: str = "orange"
    pen_linewidth: float = 2.0
    pen_linestyle: str = "-"
    pen_alpha: float = 0.9
    
    # 线段样式
    segment_up_color: str = "purple"
    segment_down_color: str = "brown"
    segment_linewidth: float = 3.0
    segment_linestyle: str = "--"
    segment_alpha: float = 0.8
    
    # 中枢样式
    pivot_fill_color: str = "lightgray"
    pivot_edge_color: str = "black"
    pivot_linewidth: float = 1.5
    pivot_alpha: float = 0.3
    
    # 分型标记样式
    top_fractal_color: str = "red"
    bottom_fractal_color: str = "green"
    fractal_marker: str = "o"
    fractal_size: int = 50
    
    # 图表基础样式
    background_color: str = "white"
    grid_color: str = "lightgray"
    grid_alpha: float = 0.3
    title_fontsize: int = 14
    label_fontsize: int = 10
    
    @classmethod
    def get_dark_theme(cls) -> 'ChartStyles':
        """获取暗色主题配置"""
        return cls(
            kline_up_color="#00ff00",
            kline_down_color="#ff0000",
            pen_up_color="#4da6ff",
            pen_down_color="#ffa64d",
            segment_up_color="#cc66ff",
            segment_down_color="#ff9966",
            pivot_fill_color="#333333",
            pivot_edge_color="#666666",
            background_color="#1e1e1e",
            grid_color="#444444"
        )
    
    @classmethod
    def get_light_theme(cls) -> 'ChartStyles':
        """获取亮色主题配置"""
        return cls()
    
    def get_pen_style(self, direction: str) -> Tuple[str, float, str, float]:
        """获取笔的样式"""
        if direction == 'up':
            return (self.pen_up_color, self.pen_linewidth, 
                    self.pen_linestyle, self.pen_alpha)
        else:
            return (self.pen_down_color, self.pen_linewidth,
                    self.pen_linestyle, self.pen_alpha)
    
    def get_segment_style(self, direction: str) -> Tuple[str, float, str, float]:
        """获取线段样式"""
        if direction == 'up':
            return (self.segment_up_color, self.segment_linewidth,
                    self.segment_linestyle, self.segment_alpha)
        else:
            return (self.segment_down_color, self.segment_linewidth,
                    self.segment_linestyle, self.segment_alpha)
    
    def get_fractal_style(self, fractal_type: str) -> Tuple[str, str, int]:
        """获取分型标记样式"""
        if fractal_type == 'top':
            return (self.top_fractal_color, self.fractal_marker, self.fractal_size)
        else:
            return (self.bottom_fractal_color, self.fractal_marker, self.fractal_size)