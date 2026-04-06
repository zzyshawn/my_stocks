"""
缠论图表绘制器
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.dates import DateFormatter
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..core.kline import KLine, KLineSeries
from ..core.pen import Pen, PenSeries
from ..core.segment import Segment, SegmentSeries
from ..core.central_pivot import CentralPivot, CentralPivotSeries
from ..core.analyzer import ChanLunAnalyzer
from .styles import ChartStyles


class ChanLunPlotter:
    """缠论图表绘制器"""
    
    def __init__(self, styles: Optional[ChartStyles] = None):
        self.styles = styles or ChartStyles()
        self.fig = None
        self.ax = None
    
    def plot_kline_with_chanlun(self, analysis_result: Dict[str, Any], 
                               title: str = "缠论分析图", 
                               figsize: tuple = (15, 10)) -> None:
        """
        绘制K线图并叠加缠论分析结果
        
        Args:
            analysis_result: 缠论分析结果
            title: 图表标题
            figsize: 图表尺寸
        """
        self.fig, self.ax = plt.subplots(figsize=figsize)
        
        # 获取分析结果
        kline_series = analysis_result['kline_series']
        fractals = analysis_result['fractals']
        pen_series = analysis_result['pen_series']
        segment_series = analysis_result['segment_series']
        pivot_series = analysis_result['pivot_series']
        
        # 绘制K线
        self._plot_klines(kline_series)
        
        # 绘制分型
        self._plot_fractals(kline_series, fractals)
        
        # 绘制笔
        self._plot_pens(pen_series)
        
        # 绘制线段
        self._plot_segments(segment_series)
        
        # 绘制中枢
        self._plot_pivots(pivot_series)
        
        # 设置图表样式
        self._setup_chart(title)
        
        plt.tight_layout()
        plt.show()
    
    def _plot_klines(self, kline_series: KLineSeries) -> None:
        """绘制K线图"""
        timestamps = kline_series.get_timestamps()
        
        for i, kline in enumerate(kline_series._sorted_klines):
            color = self.styles.kline_up_color if kline.is_positive() else self.styles.kline_down_color
            
            # 绘制实体
            body_start = min(kline.open, kline.close)
            body_end = max(kline.open, kline.close)
            body_height = body_end - body_start
            
            if body_height > 0:
                # 计算K线宽度（使用时间增量）
                if i < len(timestamps) - 1:
                    # 使用相邻K线的时间差作为宽度的参考
                    time_diff = timestamps[i+1] - timestamps[i]
                    width = time_diff * 0.8  # 使用80%的时间间隔作为宽度
                else:
                    # 最后一根K线，使用默认值
                    from datetime import timedelta
                    width = timedelta(days=0.1)  # 假设是日线数据
                
                rect = patches.Rectangle(
                    (timestamps[i], body_start), 
                    width=width,
                    height=body_height,
                    facecolor=color,
                    alpha=self.styles.kline_alpha,
                    edgecolor=color
                )
                self.ax.add_patch(rect)
            
            # 绘制影线
            self.ax.plot([timestamps[i], timestamps[i]], 
                        [kline.low, kline.high], 
                        color=color, 
                        linewidth=self.styles.kline_linewidth)
    
    def _plot_fractals(self, kline_series: KLineSeries, fractals: Dict[str, List[int]]) -> None:
        """绘制分型标记"""
        timestamps = kline_series.get_timestamps()
        
        # 绘制顶分型
        for idx in fractals['top']:
            color, marker, size = self.styles.get_fractal_style('top')
            kline = kline_series[idx]
            self.ax.scatter(timestamps[idx], kline.high, 
                           color=color, marker=marker, s=size, zorder=5)
        
        # 绘制底分型
        for idx in fractals['bottom']:
            color, marker, size = self.styles.get_fractal_style('bottom')
            kline = kline_series[idx]
            self.ax.scatter(timestamps[idx], kline.low, 
                           color=color, marker=marker, s=size, zorder=5)
    
    def _plot_pens(self, pen_series: PenSeries) -> None:
        """绘制笔"""
        for pen in pen_series.pens:
            color, linewidth, linestyle, alpha = self.styles.get_pen_style(pen.direction)
            
            # 绘制笔的连线
            start_time = pen.start_kline.timestamp
            end_time = pen.end_kline.timestamp
            
            self.ax.plot([start_time, end_time], 
                        [pen.start_price, pen.end_price],
                        color=color, 
                        linewidth=linewidth,
                        linestyle=linestyle,
                        alpha=alpha,
                        zorder=3)
    
    def _plot_segments(self, segment_series: SegmentSeries) -> None:
        """绘制线段"""
        for segment in segment_series.segments:
            color, linewidth, linestyle, alpha = self.styles.get_segment_style(segment.direction)
            
            # 绘制线段的连线
            start_time = segment.start_pen.start_kline.timestamp
            end_time = segment.end_pen.end_kline.timestamp
            
            self.ax.plot([start_time, end_time], 
                        [segment.start_price, segment.end_price],
                        color=color, 
                        linewidth=linewidth,
                        linestyle=linestyle,
                        alpha=alpha,
                        zorder=4)
    
    def _plot_pivots(self, pivot_series: CentralPivotSeries) -> None:
        """绘制中枢"""
        for pivot in pivot_series.pivots:
            # 获取中枢的时间范围
            start_time = pivot.segments[0].start_pen.start_kline.timestamp
            end_time = pivot.segments[-1].end_pen.end_kline.timestamp
            
            # 创建中枢矩形
            width = (end_time - start_time).total_seconds() / (24 * 3600)  # 转换为天数
            height = pivot.zg - pivot.zd
            
            rect = patches.Rectangle(
                (start_time, pivot.zd),
                width=width,
                height=height,
                facecolor=self.styles.pivot_fill_color,
                edgecolor=self.styles.pivot_edge_color,
                linewidth=self.styles.pivot_linewidth,
                alpha=self.styles.pivot_alpha,
                zorder=2
            )
            self.ax.add_patch(rect)
            
            # 绘制中枢边界线
            self.ax.axhline(y=pivot.zg, color=self.styles.pivot_edge_color, 
                           linestyle=':', alpha=0.5, zorder=2)
            self.ax.axhline(y=pivot.zd, color=self.styles.pivot_edge_color, 
                           linestyle=':', alpha=0.5, zorder=2)
    
    def _setup_chart(self, title: str) -> None:
        """设置图表样式"""
        self.ax.set_title(title, fontsize=self.styles.title_fontsize)
        self.ax.set_xlabel("时间", fontsize=self.styles.label_fontsize)
        self.ax.set_ylabel("价格", fontsize=self.styles.label_fontsize)
        
        # 设置背景色
        self.ax.set_facecolor(self.styles.background_color)
        self.fig.patch.set_facecolor(self.styles.background_color)
        
        # 设置网格
        self.ax.grid(True, color=self.styles.grid_color, alpha=self.styles.grid_alpha)
        
        # 设置日期格式
        date_format = DateFormatter("%m-%d %H:%M")
        self.ax.xaxis.set_major_formatter(date_format)
        plt.xticks(rotation=45)
    
    def save_plot(self, filename: str, dpi: int = 300) -> None:
        """保存图表"""
        if self.fig is not None:
            self.fig.savefig(filename, dpi=dpi, bbox_inches='tight')
    
    def plot_interactive(self, analysis_result: Dict[str, Any], 
                        title: str = "缠论分析图") -> None:
        """
        绘制交互式图表（使用plotly）
        
        Args:
            analysis_result: 缠论分析结果
            title: 图表标题
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            print("请安装plotly库: pip install plotly")
            return
        
        kline_series = analysis_result['kline_series']
        pen_series = analysis_result['pen_series']
        segment_series = analysis_result['segment_series']
        pivot_series = analysis_result['pivot_series']
        
        fig = make_subplots(rows=1, cols=1, subplot_titles=[title])
        
        # 绘制K线
        timestamps = kline_series.get_timestamps()
        highs = kline_series.get_highs()
        lows = kline_series.get_lows()
        opens = [k.open for k in kline_series._sorted_klines]
        closes = [k.close for k in kline_series._sorted_klines]
        
        # 添加K线图
        fig.add_trace(go.Candlestick(
            x=timestamps,
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            name="K线"
        ), row=1, col=1)
        
        # 绘制笔
        for pen in pen_series.pens:
            color = 'blue' if pen.direction == 'up' else 'orange'
            fig.add_trace(go.Scatter(
                x=[pen.start_kline.timestamp, pen.end_kline.timestamp],
                y=[pen.start_price, pen.end_price],
                mode='lines',
                line=dict(color=color, width=2),
                name=f"笔({pen.direction})",
                showlegend=False
            ), row=1, col=1)
        
        # 绘制线段
        for segment in segment_series.segments:
            color = 'purple' if segment.direction == 'up' else 'brown'
            fig.add_trace(go.Scatter(
                x=[segment.start_pen.start_kline.timestamp, 
                   segment.end_pen.end_kline.timestamp],
                y=[segment.start_price, segment.end_price],
                mode='lines',
                line=dict(color=color, width=3, dash='dash'),
                name=f"线段({segment.direction})",
                showlegend=False
            ), row=1, col=1)
        
        # 绘制中枢
        for pivot in pivot_series.pivots:
            start_time = pivot.segments[0].start_pen.start_kline.timestamp
            end_time = pivot.segments[-1].end_pen.end_kline.timestamp
            
            fig.add_trace(go.Scatter(
                x=[start_time, end_time, end_time, start_time, start_time],
                y=[pivot.zd, pivot.zd, pivot.zg, pivot.zg, pivot.zd],
                fill='toself',
                fillcolor='rgba(128,128,128,0.2)',
                line=dict(color='black', width=1),
                name="中枢",
                showlegend=False
            ), row=1, col=1)
        
        fig.update_layout(
            title=title,
            xaxis_title="时间",
            yaxis_title="价格",
            template="plotly_white"
        )
        
        fig.show()