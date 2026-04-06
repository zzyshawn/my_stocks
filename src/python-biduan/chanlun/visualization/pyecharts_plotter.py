"""
使用pyecharts绘制缠论分析图
"""

import os
from typing import Dict, Any, List
from datetime import datetime
from pyecharts.charts import Line, Kline
from pyecharts.globals import ThemeType
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode

from ..core.kline import KLine, KLineSeries
from ..core.pen import Pen, PenSeries
from ..core.segment import Segment, SegmentSeries
from ..core.central_pivot import CentralPivot, CentralPivotSeries
from .styles import ChartStyles


class PyechartsPlotter:
    """使用pyecharts绘制缠论分析图"""
    
    def __init__(self, styles: ChartStyles = None):
        self.styles = styles or ChartStyles()
    
    def plot_analysis_chart(self, analysis_result: Dict[str, Any], output_file: str = "analysis_chart.html") -> str:
        """
        绘制缠论分析图表
        
        Args:
            analysis_result: 分析结果字典
            output_file: 输出文件名
            
        Returns:
            输出文件路径
        """
        kline_series = analysis_result['kline_series']
        processed_kline_series = analysis_result.get('processed_kline_series', kline_series)
        fractals = analysis_result['fractals']
        pen_series = analysis_result['pen_series']
        segment_series = analysis_result['segment_series']
        pivot_series = analysis_result['pivot_series']
        inclusion_info = analysis_result.get('inclusion_info', [])
        inclusion_mapping = analysis_result.get('inclusion_mapping', {})
        
        # 准备数据 - 使用全部K线数据用于显示
        sorted_klines = kline_series._sorted_klines
        dates = []
        for kline in sorted_klines:
            # 判断是否包含时间信息
            if kline.timestamp.hour == 0 and kline.timestamp.minute == 0 and kline.timestamp.second == 0:
                # 日线数据，只显示日期
                dates.append(kline.timestamp.strftime('%Y-%m-%d'))
            else:
                # 分钟数据，显示日期和时间
                dates.append(kline.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        kline_data = []
        for kline in sorted_klines:
            kline_data.append([kline.open, kline.close, kline.low, kline.high])
        
        # 计算y轴范围，上下留5%的空白
        all_lows = [kline.low for kline in sorted_klines]
        all_highs = [kline.high for kline in sorted_klines]
        data_min = min(all_lows)
        data_max = max(all_highs)
        data_range = data_max - data_min
        y_min = data_min - data_range * 0.05  # 下留5%空白
        y_max = data_max + data_range * 0.05  # 上留5%空白
        
        # 创建K线图（使用适中的配置，添加颜色但保持简单）
        kline = Kline(
            init_opts=opts.InitOpts(
                width="1400px",  # 按照需求4.4.2的尺寸
                height="900px",  # 按照需求4.4.2的尺寸
                page_title=f"{analysis_result.get('stock_code', '未知')} {analysis_result.get('stock_name', '股票')} 缠论分析图"
            )
        )
        kline.add_xaxis(xaxis_data=dates)
        kline.add_yaxis(
            series_name="K线",
            y_axis=kline_data,
            itemstyle_opts=opts.ItemStyleOpts(
                color="#ef232a",  # 阳线颜色，符合需求4.4.3
                color0="#14b143",  # 阴线颜色，符合需求4.4.3
                border_color="#ef232a",  # 阳线边框颜色
                border_color0="#14b143",  # 阴线边框颜色
            ),
        )
        
        # 设置全局配置（添加基本交互功能）
        kline.set_global_opts(
            title_opts=opts.TitleOpts(title=f"{analysis_result.get('stock_code', '未知')} {analysis_result.get('stock_name', '股票')} 缠论分析图"),  # 需求4.4.2
            xaxis_opts=opts.AxisOpts(
                type_="category",
                boundary_gap=False,
            ),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                min_=y_min,  # y轴最小值，下留5%空白
                max_=y_max,  # y轴最大值，上留5%空白
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),  # 需求4.4.2
            datazoom_opts=[
                opts.DataZoomOpts(range_start=0, range_end=100, filter_mode="filter"),  # 整体缩放，需求4.4.2，过滤模式使y轴自动调整
                opts.DataZoomOpts(type_="inside", filter_mode="filter"),  # 内部鼠标滚轮缩放，需求4.4.2，过滤模式使y轴自动调整
            ],
            toolbox_opts=opts.ToolboxOpts(  # 需求4.4.2
                feature={
                    "saveAsImage": {"show": True, "title": "保存为图片"},
                    "restore": {"show": True, "title": "还原"},
                    "dataZoom": {"show": True, "title": {"zoom": "区域缩放", "back": "缩放还原"}},
                }
            ),
        )
        
        # 使用全部数据，不需要过滤
        filtered_inclusion_info = inclusion_info
        filtered_inclusion_mapping = inclusion_mapping
        filtered_fractals = fractals
        
        # 创建一个临时的分析结果对象，使用过滤后的数据
        filtered_analysis_result = analysis_result.copy()
        filtered_analysis_result['fractals'] = filtered_fractals
        
        # 添加包含关系标记
        self._plot_inclusion_marks(kline, dates, kline_series, filtered_inclusion_info, filtered_inclusion_mapping)
        
        # 添加分型标记（映射到原始K线位置）
        self._plot_fractals_on_kline(kline, dates, kline_series, filtered_fractals, processed_kline_series, filtered_inclusion_mapping)
        
        # 添加连接上顶和下底的线段（按 4.2.10 需求绘制笔）
        # 启用笔连线功能
        self._plot_top_bottom_lines(kline, dates, kline_series, filtered_analysis_result)
        
        # 添加中枢矩形区域（按 4.3.6 和 5.2.1 需求）
        # 1.3.3 强制要求：使用核心代码计算的数据
        # 绘制一级笔中枢（3.7.6）
        self._plot_pen_pivots(kline, dates, kline_series, analysis_result)
        
        # 保存图表
        kline.render(output_file)
        return output_file
    
    def _plot_inclusion_marks(self, chart: Kline, dates: List[str], kline_series: KLineSeries, inclusion_info: List[tuple[int, str]], inclusion_mapping: dict = None) -> None:
        """在K线图上绘制包含关系背景颜色"""
        # 如果没有包含关系映射信息，仅使用inclusion_info进行标记
        if not inclusion_mapping:
            # 提取包含关系的索引
            up_inclusion_indices = []
            down_inclusion_indices = []
            
            for idx, inc_type in inclusion_info:
                if 0 <= idx < len(dates):
                    if inc_type == "上升包含":
                        up_inclusion_indices.append(idx)
                    elif inc_type == "下降包含":
                        down_inclusion_indices.append(idx)
            
            # 使用markArea来创建背景区域
            mark_areas = []
            
            # 添加上升包含的背景区域（黄色）
            for idx in up_inclusion_indices:
                if 0 <= idx < len(dates):
                    # 获取该K线的最高价和最低价作为区域边界
                    high_price = kline_series[idx].high
                    low_price = kline_series[idx].low
                    mark_areas.append(
                        opts.MarkAreaItem(
                            x=(idx, idx + 1),  # 在x轴上的范围
                            y=(low_price, high_price),  # 在y轴上的范围（从最低价到最高价）
                            itemstyle_opts=opts.ItemStyleOpts(
                                color="#FFFF99",  # 浅黄色
                                opacity=0.4
                            )
                        )
                    )
            
            # 添加下降包含的背景区域（绿色）
            for idx in down_inclusion_indices:
                if 0 <= idx < len(dates):
                    # 获取该K线的最高价和最低价作为区域边界
                    high_price = kline_series[idx].high
                    low_price = kline_series[idx].low
                    mark_areas.append(
                        opts.MarkAreaItem(
                            x=(idx, idx + 1),  # 在x轴上的范围
                            y=(low_price, high_price),  # 在y轴上的范围（从最低价到最高价）
                            itemstyle_opts=opts.ItemStyleOpts(
                                color="#99FF99",  # 浅绿色
                                opacity=0.4
                            )
                        )
                    )
        else:
            # 使用包含关系映射来正确标记合并K线的范围
            mark_areas = []
            processed_indices = set()  # 用于跟踪已处理的映射组，避免重复标记
            
            # 遍历映射关系，找出包含关系涉及的K线范围
            for processed_idx, original_indices in inclusion_mapping.items():
                if len(original_indices) > 1 and processed_idx not in processed_indices:  # 说明有K线合并且未处理过
                    # 标记为已处理
                    processed_indices.add(processed_idx)
                    
                    # 检查这个合并区间内是否有包含关系
                    has_inclusion = False
                    for idx in original_indices:
                        for inc_idx, inc_type in inclusion_info:
                            if inc_idx == idx:
                                # 确定颜色
                                color = "#FFFF99" if inc_type == "上升包含" else "#99FF99"
                                
                                # 找到这个合并区间的最高价和最低价
                                min_low = float('inf')
                                max_high = float('-inf')
                                for orig_idx in original_indices:
                                    if 0 <= orig_idx < len(kline_series):
                                        kline = kline_series[orig_idx]
                                        min_low = min(min_low, kline.low)
                                        max_high = max(max_high, kline.high)
                                
                                # 添加背景区域，覆盖合并的K线范围
                                # 使用原始索引作为x轴坐标，因为它们与kline_series索引一致
                                x_start = min(original_indices)
                                x_end = max(original_indices) + 1
                                if x_start < len(dates) and x_end <= len(dates):
                                    mark_areas.append(
                                        opts.MarkAreaItem(
                                            x=(x_start, x_end),  # 在x轴上的范围
                                            y=(min_low, max_high),  # 在y轴上的范围（从合并区间的最低价到最高价）
                                            itemstyle_opts=opts.ItemStyleOpts(
                                                color=color,
                                                opacity=0.4
                                            )
                                        )
                                    )
                                has_inclusion = True
                                break  # 找到匹配的包含关系后跳出内层循环
                        if has_inclusion:
                            break  # 找到匹配的包含关系后跳出外层循环
        
        # 添加markArea到图表
        if mark_areas:
            chart.set_series_opts(
                markarea_opts=opts.MarkAreaOpts(
                    data=mark_areas
                )
            )
    
    def _plot_fractals_on_kline(self, chart: Kline, dates: List[str], kline_series: KLineSeries, fractals: Dict[str, List[int]], processed_kline_series: KLineSeries = None, inclusion_mapping: dict = None) -> None:
        """在K线图上绘制分型"""
        # 使用markpoint来绘制分型标记
        markpoints = []
        
        # 使用全部数据，无需限制数量
        top_fractals = set(fractals['top'])
        bottom_fractals = set(fractals['bottom'])
        
        # 创建顶分型和底分型的有序列表，按索引排序
        sorted_top_fractals = sorted(list(top_fractals))
        sorted_bottom_fractals = sorted(list(bottom_fractals))
        
        # 使用全部数据
        all_klines = kline_series._sorted_klines
        
        # 识别有效分型：顶顶分型和低低分型
        valid_top_fractals = set()  # 顶顶分型
        valid_bottom_fractals = set()  # 低低分型
        
        # 识别顶顶分型：当前顶分型的最高值>=前顶分型的最高值 且 当前顶分型的最高值>后一个顶分型的最高值
        for i, idx in enumerate(sorted_top_fractals):
            if 0 <= idx < len(all_klines):
                current_high = all_klines[idx].high
                
                # 检查前一个和后一个顶分型
                prev_high = None
                next_high = None
                
                # 获取前一个顶分型的高点
                if i > 0:
                    prev_idx = sorted_top_fractals[i-1]
                    if 0 <= prev_idx < len(all_klines):
                        prev_high = all_klines[prev_idx].high
                
                # 获取后一个顶分型的高点
                if i < len(sorted_top_fractals) - 1:
                    next_idx = sorted_top_fractals[i+1]
                    if 0 <= next_idx < len(all_klines):
                        next_high = all_klines[next_idx].high
                
                # 判断是否为顶顶分型
                is_valid_top = True
                if prev_high is not None and current_high < prev_high:
                    is_valid_top = False
                if next_high is not None and current_high <= next_high:
                    is_valid_top = False
                
                if is_valid_top:
                    valid_top_fractals.add(idx)
        
        # 识别低低分型：当前底分型的最低值<=前底分型的最低值 且 当前底分型的最低值<后一个底分型的最低值
        for i, idx in enumerate(sorted_bottom_fractals):
            if 0 <= idx < len(all_klines):
                current_low = all_klines[idx].low
                
                # 检查前一个和后一个底分型
                prev_low = None
                next_low = None
                
                # 获取前一个底分型的低点
                if i > 0:
                    prev_idx = sorted_bottom_fractals[i-1]
                    if 0 <= prev_idx < len(all_klines):
                        prev_low = all_klines[prev_idx].low
                
                # 获取后一个底分型的低点
                if i < len(sorted_bottom_fractals) - 1:
                    next_idx = sorted_bottom_fractals[i+1]
                    if 0 <= next_idx < len(all_klines):
                        next_low = all_klines[next_idx].low
                
                # 判断是否为低低分型
                is_valid_bottom = True
                if prev_low is not None and current_low > prev_low:
                    is_valid_bottom = False
                if next_low is not None and current_low >= next_low:
                    is_valid_bottom = False
                
                if is_valid_bottom:
                    valid_bottom_fractals.add(idx)
        
        # 添加顶顶分型标记（使用特殊符号）
        for idx in valid_top_fractals:
            if 0 <= idx < len(dates):
                # 顶顶分型位置为当前最高值再高一点
                adjusted_high = all_klines[idx].high * 1.005  # 高出0.5%
                markpoints.append(
                    opts.MarkPointItem(
                        coord=[dates[idx], adjusted_high],
                        symbol="triangle",  # 三角形符号表示顶顶分型
                        symbol_size=15,  # 修改为15像素大小
                        symbol_rotate=180,  # 旋转180度，使三角形朝下
                        itemstyle_opts=opts.ItemStyleOpts(color="#FFA500")  # 橙色
                    )
                )
        
        # 添加低低分型标记（使用特殊符号）
        for idx in valid_bottom_fractals:
            if 0 <= idx < len(dates):
                # 低低分型位置为当前最低值再低一点
                adjusted_low = all_klines[idx].low * 0.995  # 低于0.5%
                markpoints.append(
                    opts.MarkPointItem(
                        coord=[dates[idx], adjusted_low],
                        symbol="triangle",  # 三角形符号表示低低分型
                        symbol_size=15,  # 修改为15像素大小
                        itemstyle_opts=opts.ItemStyleOpts(color="#32CD32")  # 绿色
                    )
                )
        
        # 添加普通顶分型标记
        for idx in top_fractals:
            if 0 <= idx < len(dates) and idx not in valid_top_fractals:  # 排除顶顶分型
                # 顶分型位置为当前最高值再高一点
                adjusted_high = all_klines[idx].high * 1.005  # 高出0.5%
                markpoints.append(
                    opts.MarkPointItem(
                        coord=[dates[idx], adjusted_high],
                        symbol="triangle",  # 三角形符号，向上
                        symbol_size=10,  # 修改为10像素大小
                        symbol_rotate=180,  # 旋转180度，使三角形朝下
                        itemstyle_opts=opts.ItemStyleOpts(color="#FF0000")  # 红色
                    )
                )
        
        # 添加普通底分型标记
        for idx in bottom_fractals:
            if 0 <= idx < len(dates) and idx not in valid_bottom_fractals:  # 排除低低分型
                # 底分型位置为当前最低值再低一点
                adjusted_low = all_klines[idx].low * 0.995  # 低于0.5%
                markpoints.append(
                    opts.MarkPointItem(
                        coord=[dates[idx], adjusted_low],
                        symbol="triangle",  # 三角形符号，但向下
                        symbol_size=10,  # 修改为10像素大小
                        itemstyle_opts=opts.ItemStyleOpts(color="#0000FF")  # 蓝色
                    )
                )
        
        # 添加markpoint到图表
        if markpoints:
            chart.set_series_opts(
                markpoint_opts=opts.MarkPointOpts(
                    data=markpoints
                )
            )
    
    def _plot_top_bottom_lines(self, chart: Kline, dates: List[str], kline_series: KLineSeries, analysis_result: Dict[str, Any]) -> None:
        """在K线图上绘制连接上顶和下底的线段"""
        # 直接从分析结果中获取组合调整后的顶底标记
        top_bottom_markers = analysis_result.get('top_bottom_markers', {})
        
        # 使用全部数据（从kline_series获取，与dates对应）
        all_klines = kline_series._sorted_klines
        
        # 按索引排序所有顶底标记
        top_bottom_pairs = sorted([(idx, marker) for idx, marker in top_bottom_markers.items() if marker in ["上顶", "下底"]], key=lambda x: x[0])
        
        # 绘制连接上顶和下底的线段
        # 创建线条数据
        for i in range(len(top_bottom_pairs) - 1):
            current_idx, current_marker = top_bottom_pairs[i]
            next_idx, next_marker = top_bottom_pairs[i + 1]
            
            # 确保索引在范围内
            if current_idx < len(dates) and next_idx < len(dates) and 0 <= current_idx < len(all_klines) and 0 <= next_idx < len(all_klines):
                # 获取当前和下一个标记的坐标
                current_price = all_klines[current_idx].high if current_marker == "上顶" else all_klines[current_idx].low
                next_price = all_klines[next_idx].high if next_marker == "上顶" else all_klines[next_idx].low
                
                # 确定线条颜色和样式
                if current_marker == "下底" and next_marker == "上顶":  # 上行笔
                    color = "#FF0000"  # 红色
                    line_style = "dashed"  # 虚线
                elif current_marker == "上顶" and next_marker == "下底":  # 下行笔
                    color = "#008000"  # 绿色
                    line_style = "dashed"  # 虚线
                else:
                    # 如果是相同类型的标记（理论上不应该发生，但为了安全起见）
                    color = "#808080"  # 灰色
                    line_style = "dotted"  # 点线
                
                # 创建线条
                line = Line()
                line.add_xaxis(xaxis_data=[dates[current_idx], dates[next_idx]])
                line.add_yaxis(
                    series_name=f"笔连线_{i+1}",
                    y_axis=[current_price, next_price],
                    symbol="none",  # 不显示任何符号
                    symbol_size=0,  # 确保符号大小为0
                    linestyle_opts=opts.LineStyleOpts(
                        color=color,
                        type_=line_style,
                        width=2
                    ),
                    is_smooth=False,
                    label_opts=opts.LabelOpts(is_show=False)  # 不显示标签
                )
                
                # 将线条叠加到K线图上
                chart.overlap(line)
    
    def _plot_pen_pivots(self, chart: Kline, dates: List[str], kline_series: KLineSeries, analysis_result: Dict[str, Any]) -> None:
        """
        在K线图上绘制一级笔中枢（3.7.6）
        
        Args:
            chart: K线图表对象
            dates: 日期列表
            kline_series: K线序列
            analysis_result: 分析结果
        """
        # 1.3.3强制要求：直接使用核心代码返回的笔中枢数据
        zg_dict = analysis_result.get('zg_dict', {})
        zd_dict = analysis_result.get('zd_dict', {})
        
        if not zg_dict or not zd_dict:
            return
        
        # 3.7.6绘制规则：当当前K线的ZG != 前一个K线的ZG 或 当前K线的ZD != 前一个K线的ZD时，开始绘制前一个中枢
        
        # 找出所有有有效ZG和ZD的K线索引
        valid_indices = []
        for i in range(len(dates)):
            zg = zg_dict.get(i)
            zd = zd_dict.get(i)
            if zg is not None and zd is not None:
                valid_indices.append(i)
        
        if len(valid_indices) < 2:
            return
        
        # 创建中枢区间
        pivot_regions = []
        
        # 遍历有效索引，检测中枢变化
        start_idx = valid_indices[0]
        prev_zg = zg_dict.get(start_idx)
        prev_zd = zd_dict.get(start_idx)
        
        for i in range(1, len(valid_indices)):
            curr_idx = valid_indices[i]
            curr_zg = zg_dict.get(curr_idx)
            curr_zd = zd_dict.get(curr_idx)
            
            # 检查中枢是否变化
            if abs(curr_zg - prev_zg) > 0.001 or abs(curr_zd - prev_zd) > 0.001:
                # 绘制前一个中枢
                end_idx = valid_indices[i-1]
                if end_idx > start_idx:
                    # 确保日期在范围内
                    if start_idx < len(dates) and end_idx < len(dates):
                        pivot_regions.append({
                            'start_idx': start_idx,
                            'end_idx': end_idx,
                            'zg': prev_zg,
                            'zd': prev_zd
                        })
                
                # 更新为新中枢
                start_idx = curr_idx
                prev_zg = curr_zg
                prev_zd = curr_zd
        
        # 添加最后一个中枢
        if start_idx < valid_indices[-1]:
            end_idx = valid_indices[-1]
            if start_idx < len(dates) and end_idx < len(dates):
                pivot_regions.append({
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                    'zg': prev_zg,
                    'zd': prev_zd
                })
        
        # 绘制中枢矩形区域
        mark_areas = []
        for region in pivot_regions:
            start_idx = region['start_idx']
            end_idx = region['end_idx']
            zg = region['zg']
            zd = region['zd']
            
            # 确保ZG和ZD的顺序正确
            high = max(zg, zd)
            low = min(zg, zd)
            
            mark_areas.append(
                opts.MarkAreaItem(
                    x=(dates[start_idx], dates[end_idx]),
                    y=(low, high),
                    itemstyle_opts=opts.ItemStyleOpts(
                        color="#FFD700",  # 金色
                        opacity=0.2
                    )
                )
            )
        
        # 添加markArea到图表
        if mark_areas:
            chart.set_series_opts(
                markarea_opts=opts.MarkAreaOpts(
                    data=mark_areas
                )
            )
    
