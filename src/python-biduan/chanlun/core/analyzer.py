"""
缠论分析器 - 核心算法实现
"""

from typing import List, Tuple, Dict, Any
import numpy as np
from datetime import datetime
from .kline import KLine, KLineSeries
from .pen import Pen, PenSeries
from .segment import Segment, SegmentSeries
from .central_pivot import CentralPivot, CentralPivotSeries


class ChanLunAnalyzer:
    """缠论分析器"""
    
    def __init__(self, min_pen_kline: int = 5, min_segment_pen: int = 3):
        self.min_pen_kline = min_pen_kline  # 笔的最小K线数量
        self.min_segment_pen = min_segment_pen  # 线段的最小笔数量
    
    def analyze(self, klines: List[KLine]) -> Dict[str, Any]:
        """
        完整的缠论分析流程
        
        Args:
            klines: K线数据列表
            
        Returns:
            包含所有分析结果的字典
        """
        kline_series = KLineSeries(klines)
        
        processed_klines, inclusion_info, inclusion_mapping, kline_states, merged_kline_states = self._process_kline_inclusion(kline_series)
        
        processed_kline_series = KLineSeries(processed_klines)
        fractals = self._find_fractals(kline_series, processed_klines, inclusion_mapping, merged_kline_states)
        
        # 3. 划分笔
        pens, top_bottom_markers, valid_top_fractals, valid_bottom_fractals = self._identify_pens(kline_series, fractals)
        pen_series = PenSeries(pens)
        
        # 4. 划分线段
        segments = self._identify_segments(pen_series)
        segment_series = SegmentSeries(segments)
        
        # 5. 识别中枢
        pivots = self._identify_central_pivots(segment_series)
        pivot_series = CentralPivotSeries(pivots)
        
        # 6. 识别一级笔中枢
        zg_dict, zd_dict, zg_time_dict, zd_time_dict = self._identify_pen_pivots(kline_series, top_bottom_markers)
        
        # 7. 计算前顶底日期
        prev_top_bottom_dates = {}
        sorted_top_bottom_indices = sorted([idx for idx, marker in top_bottom_markers.items() if marker in ["上顶", "下底"]])
        for i, idx in enumerate(sorted_top_bottom_indices):
            if i > 0:  # 从第二个顶底标记开始
                prev_idx = sorted_top_bottom_indices[i-1]
                prev_kline = kline_series._sorted_klines[prev_idx]
                # 判断是否包含时间信息
                if prev_kline.timestamp.hour == 0 and prev_kline.timestamp.minute == 0 and prev_kline.timestamp.second == 0:
                    prev_date = prev_kline.timestamp.strftime('%Y-%m-%d')
                else:
                    prev_date = prev_kline.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                prev_top_bottom_dates[idx] = prev_date
        
        return {
            'kline_series': kline_series,
            'processed_kline_series': processed_kline_series,
            'fractals': fractals,
            'pen_series': pen_series,
            'segment_series': segment_series,
            'pivot_series': pivot_series,
            'inclusion_info': inclusion_info,
            'inclusion_mapping': inclusion_mapping,
            'kline_states': kline_states,
            'top_bottom_markers': top_bottom_markers,
            'valid_top_fractals': valid_top_fractals,
            'valid_bottom_fractals': valid_bottom_fractals,
            'prev_top_bottom_dates': prev_top_bottom_dates,
            'zg_dict': zg_dict,
            'zd_dict': zd_dict,
            'zg_time_dict': zg_time_dict,
            'zd_time_dict': zd_time_dict
        }
    
    def _process_kline_inclusion(self, kline_series: KLineSeries) -> tuple[List[KLine], List[tuple[int, str]], dict, List[str]]:
        """
        处理K线包含关系并标记K线状态
        
        Args:
            kline_series: K线序列
            
        Returns:
            (处理包含关系后的K线列表, 包含关系信息列表[(索引, 类型)], 映射字典{处理后索引: [原始索引列表]}, 原始K线状态列表)
        """
        if len(kline_series) <= 1:
            mapping = {i: [i] for i in range(len(kline_series._sorted_klines))}
            kline_states = ["下降"] if len(kline_series) == 1 else []
            return kline_series._sorted_klines.copy(), [], mapping, kline_states
        
        # 获取原始K线列表
        original_klines = kline_series._sorted_klines
        n = len(original_klines)
        
        # 初始化原始K线状态列表
        kline_states = ["下降"] * n  # 第一根K线初始化为下降
        
        # 初始化合并K线状态列表，记录处理后K线的状态
        merged_kline_states = ["下降"]  # 第一根处理后K线的状态初始化为下降
        
        # 记录包含关系信息
        inclusion_info = []
        
        # 创建处理后的K线列表，初始时包含第一根原始K线（创建新对象）
        first_kline = original_klines[0]
        processed_klines = [KLine(
            timestamp=first_kline.timestamp,
            open=first_kline.open,
            high=first_kline.high,
            low=first_kline.low,
            close=first_kline.close,
            volume=first_kline.volume
        )]
        
        # 初始化映射关系，记录处理后K线对应哪些原始K线
        mapping = {0: [0]}
        
        # 处理从第二根K线开始的所有K线
        for i in range(1, n):
            current_kline = original_klines[i]
            last_processed_kline = processed_klines[-1]
            
            # 获取前一根合并K线的状态（根据4.2.2最新定义）
            prev_merged_state = merged_kline_states[-1]
            
            # 检查是否存在包含关系
            is_inclusion = False
            inclusion_type = ""
            merged_kline = None
            
            # 情况1：前日K线被今日K线包含（当日高点>=前日高点且当日低点<=前日低点）
            if (current_kline.high >= last_processed_kline.high and current_kline.low <= last_processed_kline.low):
                is_inclusion = True
                # 根据前日合并K线状态判断包含类型（根据4.2.2最新定义）
                if prev_merged_state == "上升":
                    inclusion_type = "上升包含"
                elif prev_merged_state == "下降":
                    inclusion_type = "下降包含"
                
                # 获取所有参与合并的原始K线
                original_indices = mapping[len(processed_klines)-1] + [i]
                original_klines_in_merge = [original_klines[idx] for idx in original_indices]
                
                # 根据包含类型计算合并后的高点和低点（根据4.2.2最新定义）
                if inclusion_type == "上升包含":
                    # 上升包含的合并K线高点=所有K线的最高点，低点=所有K线的最低点中的最高点
                    merged_high = max(k.high for k in original_klines_in_merge)
                    merged_low = max(k.low for k in original_klines_in_merge)
                else:  # 下降包含
                    # 下降包含的合并K线高点=所有K线的最高点的最低点，低点=所有K线的最低点
                    merged_high = min(k.high for k in original_klines_in_merge)
                    merged_low = min(k.low for k in original_klines_in_merge)
                
                # 创建合并K线
                merged_kline = KLine(
                    timestamp=current_kline.timestamp,
                    open=last_processed_kline.open,
                    high=merged_high,
                    low=merged_low,
                    close=current_kline.close,
                    volume=sum(k.volume for k in original_klines_in_merge)
                )
            
            # 情况2：今日K线被前日K线包含（当日高点<=前日高点且当日低点>=前日低点）
            elif (current_kline.high <= last_processed_kline.high and current_kline.low >= last_processed_kline.low):
                is_inclusion = True
                # 根据前日合并K线状态判断包含类型（根据4.2.2最新定义）
                if prev_merged_state == "上升":
                    inclusion_type = "上升包含"
                elif prev_merged_state == "下降":
                    inclusion_type = "下降包含"
                
                # 获取所有参与合并的原始K线
                original_indices = mapping[len(processed_klines)-1] + [i]
                original_klines_in_merge = [original_klines[idx] for idx in original_indices]
                
                # 根据包含类型计算合并后的高点和低点（根据4.2.2最新定义）
                if inclusion_type == "上升包含":
                    # 上升包含的合并K线高点=所有K线的最高点，低点=所有K线的最低点中的最高点
                    merged_high = max(k.high for k in original_klines_in_merge)
                    merged_low = max(k.low for k in original_klines_in_merge)
                else:  # 下降包含
                    # 下降包含的合并K线高点=所有K线的最高点的最低点，低点=所有K线的最低点
                    merged_high = min(k.high for k in original_klines_in_merge)
                    merged_low = min(k.low for k in original_klines_in_merge)
                
                # 创建合并K线
                merged_kline = KLine(
                    timestamp=current_kline.timestamp,
                    open=last_processed_kline.open,
                    high=merged_high,
                    low=merged_low,
                    close=current_kline.close,
                    volume=sum(k.volume for k in original_klines_in_merge)
                )
            
            # 处理包含关系
            if is_inclusion and inclusion_type:
                # 更新处理后的K线列表
                processed_klines[-1] = merged_kline
                
                # 更新映射关系，将当前原始K线的索引添加到最后一个处理后K线的映射中
                mapping[len(processed_klines)-1].append(i)
                
                # 标记当前原始K线为对应包含类型
                kline_states[i] = inclusion_type
                inclusion_info.append((i, inclusion_type))
                
            else:
                # 非包含关系，确定当前K线方向
                if current_kline.high > last_processed_kline.high and current_kline.low > last_processed_kline.low:
                    # 上升：当前K线的高点高于前一根处理后K线的高点，低点也高于前一根处理后K线的低点
                    kline_states[i] = "上升"
                    # 更新合并K线状态
                    merged_kline_states.append("上升")
                elif current_kline.high < last_processed_kline.high and current_kline.low < last_processed_kline.low:
                    # 下降：当前K线的高点低于前一根处理后K线的高点，低点也低于前一根处理后K线的低点
                    kline_states[i] = "下降"
                    # 更新合并K线状态
                    merged_kline_states.append("下降")
                else:
                    # 如果不是明确的上下关系，则继承前一根合并K线的方向（根据4.2.2最新定义）
                    kline_states[i] = prev_merged_state
                    # 更新合并K线状态
                    merged_kline_states.append(prev_merged_state)
                
                # 将当前原始K线添加到处理后的K线列表中（创建新对象）
                processed_klines.append(KLine(
                    timestamp=current_kline.timestamp,
                    open=current_kline.open,
                    high=current_kline.high,
                    low=current_kline.low,
                    close=current_kline.close,
                    volume=current_kline.volume
                ))
                
                # 更新映射关系
                mapping[len(processed_klines)-1] = [i]
        
        return processed_klines, inclusion_info, mapping, kline_states, merged_kline_states
    
    def _find_fractals(self, kline_series: KLineSeries, processed_klines: List[KLine] = None, inclusion_mapping: dict = None, merged_kline_states: List[str] = None) -> Dict[str, List[int]]:
        """
        识别顶分型和底分型
        
        Args:
            kline_series: K线序列
            processed_klines: 处理包含关系后的K线列表（可选）
            inclusion_mapping: 处理后K线到原始K线的映射字典（可选）
            merged_kline_states: 合并K线状态列表（可选）
            
        Returns:
            包含顶分型和底分型索引的字典
        """
        if processed_klines is None or inclusion_mapping is None or merged_kline_states is None:
            processed_klines, _, inclusion_mapping, _, merged_kline_states = self._process_kline_inclusion(kline_series)
        
        n = len(processed_klines)
        
        top_fractals = []
        bottom_fractals = []
        
        for i in range(1, n - 1):
            if (processed_klines[i].high > processed_klines[i-1].high and 
                processed_klines[i].high > processed_klines[i+1].high):
                original_indices = inclusion_mapping.get(i, [i])
                if original_indices:
                    if len(original_indices) == 1:
                        original_idx = original_indices[0]
                    else:
                        max_high = -1
                        original_idx = original_indices[0]
                        for idx in original_indices:
                            if 0 <= idx < len(kline_series._sorted_klines):
                                kline = kline_series._sorted_klines[idx]
                                if kline.high > max_high:
                                    max_high = kline.high
                                    original_idx = idx
                    
                    if 0 <= original_idx < len(kline_series._sorted_klines):
                        top_fractals.append(original_idx)
            
            elif (processed_klines[i].low < processed_klines[i-1].low and 
                  processed_klines[i].low < processed_klines[i+1].low):
                original_indices = inclusion_mapping.get(i, [i])
                if original_indices:
                    if len(original_indices) == 1:
                        original_idx = original_indices[0]
                    else:
                        min_low = float('inf')
                        original_idx = original_indices[0]
                        for idx in original_indices:
                            if 0 <= idx < len(kline_series._sorted_klines):
                                kline = kline_series._sorted_klines[idx]
                                if kline.low < min_low:
                                    min_low = kline.low
                                    original_idx = idx
                    
                    if 0 <= original_idx < len(kline_series._sorted_klines):
                        bottom_fractals.append(original_idx)
        
        last_merged_state = merged_kline_states[-1] if merged_kline_states else "下降"
        last_original_indices = inclusion_mapping.get(n - 1, [n - 1])
        
        if last_merged_state == "下降":
            if len(last_original_indices) == 1:
                original_idx = last_original_indices[0]
            else:
                min_low = float('inf')
                original_idx = last_original_indices[0]
                for idx in last_original_indices:
                    if 0 <= idx < len(kline_series._sorted_klines):
                        kline = kline_series._sorted_klines[idx]
                        if kline.low < min_low:
                            min_low = kline.low
                            original_idx = idx
            if 0 <= original_idx < len(kline_series._sorted_klines):
                bottom_fractals.append(original_idx)
        elif last_merged_state == "上升":
            if len(last_original_indices) == 1:
                original_idx = last_original_indices[0]
            else:
                max_high = -1
                original_idx = last_original_indices[0]
                for idx in last_original_indices:
                    if 0 <= idx < len(kline_series._sorted_klines):
                        kline = kline_series._sorted_klines[idx]
                        if kline.high > max_high:
                            max_high = kline.high
                            original_idx = idx
            if 0 <= original_idx < len(kline_series._sorted_klines):
                top_fractals.append(original_idx)
        
        all_fractals = []
        for idx in top_fractals:
            all_fractals.append((idx, 'top'))
        for idx in bottom_fractals:
            all_fractals.append((idx, 'bottom'))
        
        all_fractals.sort(key=lambda x: x[0])
        
        filtered_top_fractals = []
        filtered_bottom_fractals = []
        
        for i, (idx, fractal_type) in enumerate(all_fractals):
            if i == 0:
                if fractal_type == 'top':
                    filtered_top_fractals.append(idx)
                else:
                    filtered_bottom_fractals.append(idx)
            else:
                prev_fractal_type = all_fractals[i-1][1]
                
                if fractal_type != prev_fractal_type:
                    if fractal_type == 'top':
                        filtered_top_fractals.append(idx)
                    else:
                        filtered_bottom_fractals.append(idx)
                else:
                    if fractal_type == 'top':
                        prev_idx = all_fractals[i-1][0]
                        if 0 <= idx < len(kline_series._sorted_klines) and 0 <= prev_idx < len(kline_series._sorted_klines):
                            if kline_series._sorted_klines[idx].high > kline_series._sorted_klines[prev_idx].high:
                                if prev_idx in filtered_top_fractals:
                                    filtered_top_fractals.remove(prev_idx)
                                filtered_top_fractals.append(idx)
                    else:
                        prev_idx = all_fractals[i-1][0]
                        if 0 <= idx < len(kline_series._sorted_klines) and 0 <= prev_idx < len(kline_series._sorted_klines):
                            if kline_series._sorted_klines[idx].low < kline_series._sorted_klines[prev_idx].low:
                                if prev_idx in filtered_bottom_fractals:
                                    filtered_bottom_fractals.remove(prev_idx)
                                filtered_bottom_fractals.append(idx)
        
        return {
            'top': filtered_top_fractals,
            'bottom': filtered_bottom_fractals
        }
    
    def _identify_pens(self, kline_series: KLineSeries, fractals: Dict[str, List[int]]) -> tuple[List[Pen], Dict[int, str], set, set]:
        """
        根据上顶和下底识别笔
        
        Args:
            kline_series: K线序列
            fractals: 分型字典
            
        Returns:
            (笔对象列表, 组合调整后的顶底标记字典, 有效顶分型集合, 有效底分型集合)
        """
        pens = []
        top_fractals = fractals['top']
        bottom_fractals = fractals['bottom']
        
        # 识别有效分型：顶顶分型和底底分型
        sorted_top_fractals = sorted(list(top_fractals))
        sorted_bottom_fractals = sorted(list(bottom_fractals))
        
        valid_top_fractals = set()  # 顶顶分型
        valid_bottom_fractals = set()  # 底底分型
        
        # 识别顶顶分型：当前顶分型的最高值>=前顶分型的最高值 且 当前顶分型的最高值>后一个顶分型的最高值
        for i, idx in enumerate(sorted_top_fractals):
            if 0 <= idx < len(kline_series._sorted_klines):
                current_high = kline_series._sorted_klines[idx].high
                
                # 检查前一个和后一个顶分型
                prev_high = None
                next_high = None
                
                # 获取前一个顶分型的高点
                if i > 0:
                    prev_idx = sorted_top_fractals[i-1]
                    if 0 <= prev_idx < len(kline_series._sorted_klines):
                        prev_high = kline_series._sorted_klines[prev_idx].high
                
                # 获取后一个顶分型的高点
                if i < len(sorted_top_fractals) - 1:
                    next_idx = sorted_top_fractals[i+1]
                    if 0 <= next_idx < len(kline_series._sorted_klines):
                        next_high = kline_series._sorted_klines[next_idx].high
                
                # 判断是否为顶顶分型
                is_valid_top = True
                if prev_high is not None and current_high < prev_high:
                    is_valid_top = False
                if next_high is not None and current_high <= next_high:
                    is_valid_top = False
                
                if is_valid_top:
                    valid_top_fractals.add(idx)
        
        # 识别底底分型：当前底分型的最低值<=前底分型的最低值 且 当前底分型的最低值<后一个底分型的最低值
        for i, idx in enumerate(sorted_bottom_fractals):
            if 0 <= idx < len(kline_series._sorted_klines):
                current_low = kline_series._sorted_klines[idx].low
                
                # 检查前一个和后一个底分型
                prev_low = None
                next_low = None
                
                # 获取前一个底分型的低点
                if i > 0:
                    prev_idx = sorted_bottom_fractals[i-1]
                    if 0 <= prev_idx < len(kline_series._sorted_klines):
                        prev_low = kline_series._sorted_klines[prev_idx].low
                
                # 获取后一个底分型的低点
                if i < len(sorted_bottom_fractals) - 1:
                    next_idx = sorted_bottom_fractals[i+1]
                    if 0 <= next_idx < len(kline_series._sorted_klines):
                        next_low = kline_series._sorted_klines[next_idx].low
                
                # 判断是否为底底分型
                is_valid_bottom = True
                if prev_low is not None and current_low > prev_low:
                    is_valid_bottom = False
                if next_low is not None and current_low >= next_low:
                    is_valid_bottom = False
                
                if is_valid_bottom:
                    valid_bottom_fractals.add(idx)
        
        # 识别有效分型组合
        # 创建所有有效分型的有序列表，按索引排序
        all_valid_fractals = sorted(list(valid_top_fractals | valid_bottom_fractals))
        
        # 初始化顶底标记
        top_bottom_markers = {}
        
        # 1. 所有有效分型是顶顶分型，则顶底标注为上顶（强制规则，不受间隔限制）
        # 2. 所有有效分型是底底分型，则顶底标注为下底（强制规则，不受间隔限制）
        for idx in valid_top_fractals:
            top_bottom_markers[idx] = "上顶"
        
        for idx in valid_bottom_fractals:
            top_bottom_markers[idx] = "下底"
        
        # 3. 遍历有效分型组合，执行组合调整（仅在有中间分型需要处理时才执行）
        for i, idx in enumerate(all_valid_fractals):
            if i > 0:  # 从第二个有效分型开始
                prev_idx = all_valid_fractals[i-1]  # 前一个有效分型的索引
                
                # 获取前一个和当前有效分型的类型
                prev_type = "顶顶分型" if prev_idx in valid_top_fractals else "底底分型"
                curr_type = "顶顶分型" if idx in valid_top_fractals else "底底分型"
                
                # 根据组合类型执行相应的组合调整
                # 注意：基础的顶顶分型和底底分型已经按照强制规则被标记为"上顶"和"下底"
                # 以下逻辑仅处理需要插入中间分型的情况
                if prev_type == "顶顶分型" and curr_type == "顶顶分型":  # 有效顶顶组合
                    # 在两个顶顶分型中寻找一个底分型
                    # 寻找范围是从前一个顶顶分型到当前顶顶分型之间
                    start_idx = prev_idx + 1
                    end_idx = idx - 1
                    
                    # 寻找符合条件的底分型（距离前后顶顶分型都至少间隔3个K线），需要最低，如果不是最低则次低以此类推
                    candidate_bottom_fractals = []
                    for j in range(start_idx, end_idx + 1):
                        if j in bottom_fractals:  # 是底分型
                            # 检查间隔条件：距离前一个顶顶分型和当前顶顶分型都至少3个K线
                            if abs(j - prev_idx) >= 4 and abs(j - idx) >= 4:  # 至少间隔3个K线，即4个位置差
                                candidate_bottom_fractals.append((j, kline_series._sorted_klines[j].low))
                    
                    # 按照低点从低到高排序，寻找最低的底分型，如果不是最低则次低以此类推
                    candidate_bottom_fractals.sort(key=lambda x: x[1])  # 按照低点价格升序排列
                    
                    found_bottom_fractal = None
                    for j, low_price in candidate_bottom_fractals:
                        found_bottom_fractal = j
                        break  # 取最低的那个
                    
                    # 如果找到符合条件的底分型，则标记
                    if found_bottom_fractal is not None:
                        # 原有的顶顶分型仍保持"上顶"（这是强制规则）
                        # 找到的底分型标记为"下底"
                        if found_bottom_fractal not in top_bottom_markers:  # 确保中间的底分型也被标记
                            top_bottom_markers[found_bottom_fractal] = "下底"
                    else:
                        # 如果无满足的，删除上顶低的那个的上顶标记
                        # 比较两个顶顶分型的高度，删除低的那个
                        prev_high = kline_series._sorted_klines[prev_idx].high
                        curr_high = kline_series._sorted_klines[idx].high
                        if prev_high < curr_high:
                            # 删除前一个顶顶分型的标记
                            if prev_idx in top_bottom_markers:
                                del top_bottom_markers[prev_idx]
                        else:
                            # 删除当前顶顶分型的标记
                            if idx in top_bottom_markers:
                                del top_bottom_markers[idx]
                
                elif prev_type == "底底分型" and curr_type == "底底分型":  # 有效底底组合
                    # 在两个底底分型中寻找一个顶分型
                    # 寻找范围是从前一个底底分型到当前底底分型之间
                    start_idx = prev_idx + 1
                    end_idx = idx - 1
                    
                    # 寻找符合条件的顶分型（距离前后底底分型都至少间隔3个K线），需要最高，如果不是最高则次高以此类推
                    candidate_top_fractals = []
                    for j in range(start_idx, end_idx + 1):
                        if j in top_fractals:  # 是顶分型
                            # 检查间隔条件：距离前一个底底分型和当前底底分型都至少3个K线
                            if abs(j - prev_idx) >= 4 and abs(j - idx) >= 4:  # 至少间隔3个K线，即4个位置差
                                candidate_top_fractals.append((j, kline_series._sorted_klines[j].high))
                    
                    # 按照高点从高到低排序，寻找最高的顶分型，如果不是最高则次高以此类推
                    candidate_top_fractals.sort(key=lambda x: x[1], reverse=True)  # 按照高点价格降序排列
                    
                    found_top_fractal = None
                    for j, high_price in candidate_top_fractals:
                        found_top_fractal = j
                        break  # 取最高的那个
                    
                    # 如果找到符合条件的顶分型，则标记
                    if found_top_fractal is not None:
                        # 原有的底底分型仍保持"下底"（这是强制规则）
                        # 找到的顶分型标记为"上顶"
                        if found_top_fractal not in top_bottom_markers:  # 确保中间的顶分型也被标记
                            top_bottom_markers[found_top_fractal] = "上顶"
                    else:
                        # 如果无满足的，删除下底高的那个的下底标记
                        # 比较两个底底分型的高度，删除高的那个
                        prev_low = kline_series._sorted_klines[prev_idx].low
                        curr_low = kline_series._sorted_klines[idx].low
                        if prev_low > curr_low:
                            # 删除前一个底底分型的标记
                            if prev_idx in top_bottom_markers:
                                del top_bottom_markers[prev_idx]
                        else:
                            # 删除当前底底分型的标记
                            if idx in top_bottom_markers:
                                del top_bottom_markers[idx]
                
                elif prev_type == "顶顶分型" and curr_type == "底底分型":  # 有效顶底组合
                    # 处理规则：只标记第一对满足条件的顶分型和底分型
                    # 寻找顺序：先找底分型，再在底分型之后找顶分型
                    start_idx = prev_idx + 1
                    end_idx = idx - 1
                    
                    found_top_fractal = None
                    found_bottom_fractal = None
                    
                    # 1. 先从前一个上顶开始，寻找一个间隔大于3个K线的底分型
                    for j in range(start_idx, end_idx + 1):
                        if j in bottom_fractals:  # 是底分型
                            # 检查底分型距离前顶顶分型至少3个K线
                            if abs(j - prev_idx) >= 4:  # 至少间隔3个K线，即4个位置差
                                # 2. 在找到的底分型之后，寻找一个间隔大于3个K线的顶分型
                                for k in range(j + 1, end_idx + 1):  # 在底分型之后寻找顶分型
                                    if k in top_fractals:  # 是顶分型
                                        # 3. 找到的这个顶分型距离有效底底组合间隔大于3个K线
                                        if abs(k - idx) >= 4 and abs(k - j) >= 4:  # 顶分型距离底底分型和底分型都至少3个K线
                                            # 检查顶的最高点是否高于底的最低点
                                            top_high = kline_series._sorted_klines[k].high
                                            bottom_low = kline_series._sorted_klines[j].low
                                            if top_high > bottom_low:  # 顶的最高点高于底的最低点
                                                found_top_fractal = k
                                                found_bottom_fractal = j
                                                break  # 找到第一对就退出
                                if found_top_fractal is not None and found_bottom_fractal is not None:
                                    break  # 找到第一对就退出
                    
                    # 如果找到符合条件的顶分型和底分型，则标记
                    if found_top_fractal is not None and found_bottom_fractal is not None:
                        # 原有的顶顶分型和底底分型保持原有标记（这是强制规则）
                        # 找到的中间顶分型和底分型也需要标记
                        if found_top_fractal not in top_bottom_markers:
                            top_bottom_markers[found_top_fractal] = "上顶"
                        if found_bottom_fractal not in top_bottom_markers:
                            top_bottom_markers[found_bottom_fractal] = "下底"
                
                elif prev_type == "底底分型" and curr_type == "顶顶分型":  # 有效底顶组合
                    # 处理规则：只标记第一对满足条件的顶分型和底分型
                    # 寻找顺序：先找顶分型，再在顶分型之后找底分型
                    start_idx = prev_idx + 1
                    end_idx = idx - 1
                    
                    found_top_fractal = None
                    found_bottom_fractal = None
                    
                    # 1. 先从前一个下底开始，寻找一个间隔大于3个K线的顶分型
                    for j in range(start_idx, end_idx + 1):
                        if j in top_fractals:  # 是顶分型
                            # 检查顶分型距离前底底分型至少3个K线
                            if abs(j - prev_idx) >= 4:  # 至少间隔3个K线，即4个位置差
                                # 2. 在找到的顶分型之后，寻找一个间隔大于3个K线的底分型
                                for k in range(j + 1, end_idx + 1):  # 在顶分型之后寻找底分型
                                    if k in bottom_fractals:  # 是底分型
                                        # 3. 找到的这个底分型距离有效顶顶组合间隔大于3个K线
                                        if abs(k - idx) >= 4 and abs(k - j) >= 4:  # 底分型距离顶顶分型和顶分型都至少3个K线
                                            # 检查顶的最高点是否高于底的最低点
                                            top_high = kline_series._sorted_klines[j].high
                                            bottom_low = kline_series._sorted_klines[k].low
                                            if top_high > bottom_low:  # 顶的最高点高于底的最低点
                                                found_top_fractal = j
                                                found_bottom_fractal = k
                                                break  # 找到第一对就退出
                                if found_top_fractal is not None and found_bottom_fractal is not None:
                                    break  # 找到第一对就退出
                    
                    # 如果找到符合条件的顶分型和底分型，则标记
                    if found_top_fractal is not None and found_bottom_fractal is not None:
                        # 原有的底底分型和顶顶分型保持原有标记（这是强制规则）
                        # 找到的中间顶分型和底分型也需要标记
                        if found_top_fractal not in top_bottom_markers:
                            top_bottom_markers[found_top_fractal] = "上顶"
                        if found_bottom_fractal not in top_bottom_markers:
                            top_bottom_markers[found_bottom_fractal] = "下底"
        
        # 4. 确保上顶和下底交替出现，且间隔的K线最小是3个
        # 但是，强制规则（所有有效顶顶分型为上顶，所有有效底底分型为下底）应优先保留
        # 按照索引排序所有顶底标记
        sorted_markers = sorted([(idx, marker) for idx, marker in top_bottom_markers.items()], key=lambda x: x[0])
        
        # 识别哪些是原始的有效分型（强制规则标记的）
        original_valid_top_markers = {idx for idx in valid_top_fractals if idx in top_bottom_markers}
        original_valid_bottom_markers = {idx for idx in valid_bottom_fractals if idx in top_bottom_markers}
        
        # 检查并修正顶底标记，确保交替出现且间隔至少3个K线
        if len(sorted_markers) >= 2:
            # 从第二个标记开始检查
            i = 1
            while i < len(sorted_markers):
                prev_idx, prev_marker = sorted_markers[i-1]
                curr_idx, curr_marker = sorted_markers[i]
                
                # 检查是否交替出现
                if prev_marker == curr_marker:
                    # 如果标记相同，需要决定保留哪一个
                    # 对于顶顶分型，保留较高的；对于底底分型，保留较低的
                    # 注意：根据强制规则，原始有效分型不应被删除
                    should_remove_prev = False
                    should_remove_curr = False
                    
                    # 检查是否都是原始有效分型
                    both_original_valid = False
                    if curr_marker == "上顶":
                        both_original_valid = prev_idx in original_valid_top_markers and curr_idx in original_valid_top_markers
                    else:  # "下底"
                        both_original_valid = prev_idx in original_valid_bottom_markers and curr_idx in original_valid_bottom_markers
                    
                    # 如果都是原始有效分型，根据强制规则，两者都应保留
                    # 这里我们特殊处理，暂时不删除任何一个，后续笔的识别会处理这种情况
                    if both_original_valid:
                        # 如果都是原始有效分型，跳过这个检查，继续下一个循环
                        i += 1
                        continue
                    
                    if curr_marker == "上顶":
                        # 比较两个顶分型的高度
                        prev_high = kline_series._sorted_klines[prev_idx].high
                        curr_high = kline_series._sorted_klines[curr_idx].high
                        if curr_high > prev_high:
                            # 保留当前标记，移除前一个标记（但如果前一个是原始有效分型，优先保留）
                            if prev_idx in original_valid_top_markers:
                                should_remove_curr = True
                            else:
                                should_remove_prev = True
                        else:
                            # 保留前一个标记，移除当前标记（但如果当前是原始有效分型，优先保留）
                            if curr_idx in original_valid_top_markers:
                                should_remove_prev = True
                            else:
                                should_remove_curr = True
                    else:  # "下底"
                        # 比较两个底分型的高度
                        prev_low = kline_series._sorted_klines[prev_idx].low
                        curr_low = kline_series._sorted_klines[curr_idx].low
                        if curr_low < prev_low:
                            # 保留当前标记，移除前一个标记（但如果前一个是原始有效分型，优先保留）
                            if prev_idx in original_valid_bottom_markers:
                                should_remove_curr = True
                            else:
                                should_remove_prev = True
                        else:
                            # 保留前一个标记，移除当前标记（但如果当前是原始有效分型，优先保留）
                            if curr_idx in original_valid_bottom_markers:
                                should_remove_prev = True
                            else:
                                should_remove_curr = True
                    
                    # 执行删除操作
                    if should_remove_prev:
                        if prev_idx in top_bottom_markers:
                            del top_bottom_markers[prev_idx]
                    elif should_remove_curr:
                        if curr_idx in top_bottom_markers:
                            del top_bottom_markers[curr_idx]
                    
                    # 重新获取排序后的标记列表
                    sorted_markers = sorted([(idx, marker) for idx, marker in top_bottom_markers.items()], key=lambda x: x[0])
                    # 重新开始循环，因为删除元素后索引可能发生变化
                    i = 1
                    continue
                
                # 检查间隔是否至少3个K线
                if curr_idx - prev_idx < 4:  # 间隔不足3个K线
                    # 根据强制规则，原始有效分型不应被删除，即使间隔不足
                    # 检查是否有原始有效分型
                    has_original_valid = prev_idx in (original_valid_top_markers | original_valid_bottom_markers) or curr_idx in (original_valid_top_markers | original_valid_bottom_markers)
                    
                    # 如果有原始有效分型，根据强制规则，两者都应保留
                    # 这里我们特殊处理，暂时不删除任何一个，后续笔的识别会处理这种情况
                    if has_original_valid:
                        # 如果有原始有效分型，跳过这个检查，继续下一个循环
                        i += 1
                        continue
                    
                    # 如果没有原始有效分型，根据类型决定保留哪一个
                    should_remove_prev = False
                    should_remove_curr = False
                    
                    if curr_marker == "上顶":
                        # 比较两个顶分型的高度
                        prev_high = kline_series._sorted_klines[prev_idx].high
                        curr_high = kline_series._sorted_klines[curr_idx].high
                        if curr_high > prev_high:
                            should_remove_prev = True
                        else:
                            should_remove_curr = True
                    else:  # "下底"
                        # 比较两个底分型的高度
                        prev_low = kline_series._sorted_klines[prev_idx].low
                        curr_low = kline_series._sorted_klines[curr_idx].low
                        if curr_low < prev_low:
                            should_remove_prev = True
                        else:
                            should_remove_curr = True
                    
                    # 执行删除操作
                    if should_remove_prev:
                        if prev_idx in top_bottom_markers:
                            del top_bottom_markers[prev_idx]
                    elif should_remove_curr:
                        if curr_idx in top_bottom_markers:
                            del top_bottom_markers[curr_idx]
                    
                    # 重新获取排序后的标记列表
                    sorted_markers = sorted([(idx, marker) for idx, marker in top_bottom_markers.items()], key=lambda x: x[0])
                    # 重新开始循环，因为删除元素后索引可能发生变化
                    i = 1
                    continue
                
                i += 1
        
        # 3.5.3 顶底二次调整
        # 再次遍历所有顶底标记对，进行二次调整
        top_bottom_pairs = sorted([(idx, marker) for idx, marker in top_bottom_markers.items() if marker in ["上顶", "下底"]], key=lambda x: x[0])
        
        # 再次遍历，进行二次调整
        for i, idx in enumerate(top_bottom_pairs):
            if i > 0:  # 从第二个顶底标记开始
                prev_idx, prev_marker = top_bottom_pairs[i-1]
                curr_idx, curr_marker = idx
                
                # 检查是否是需要二次调整的组合
                # 当前上顶，前一个是下底
                if prev_marker == "下底" and curr_marker == "上顶":
                    # 有效底顶组合的二次调整
                    # 在两个有效分型之间寻找一个顶分型和一个底分型
                    start_idx = prev_idx + 1
                    end_idx = curr_idx - 1
                    
                    found_top_fractal = None
                    found_bottom_fractal = None
                    
                    # 1. 先从前一个下底开始，寻找一个间隔大于3个K线的顶分型
                    for j in range(start_idx, end_idx + 1):
                        if j in top_fractals:  # 是顶分型
                            # 检查顶分型距离前底底分型至少3个K线
                            if abs(j - prev_idx) >= 4:  # 至少间隔3个K线，即4个位置差
                                # 2. 在找到的顶分型之后，寻找一个间隔大于3个K线的底分型
                                for k in range(j + 1, end_idx + 1):  # 在顶分型之后寻找底分型
                                    if k in bottom_fractals:  # 是底分型
                                        # 3. 找到的这个底分型距离有效顶顶组合间隔大于3个K线
                                        if abs(k - curr_idx) >= 4 and abs(k - j) >= 4:  # 底分型距离顶顶分型和顶分型都至少3个K线
                                            # 检查顶的最高点是否高于底的最低点
                                            top_high = kline_series._sorted_klines[j].high
                                            bottom_low = kline_series._sorted_klines[k].low
                                            if top_high > bottom_low:  # 顶的最高点高于底的最低点
                                                found_top_fractal = j
                                                found_bottom_fractal = k
                                                break  # 找到第一对就退出
                                if found_top_fractal is not None and found_bottom_fractal is not None:
                                    break  # 找到第一对就退出
                    
                    # 如果找到符合条件的顶分型和底分型，则标记
                    if found_top_fractal is not None and found_bottom_fractal is not None:
                        # 找到的中间顶分型和底分型也需要标记
                        if found_top_fractal not in top_bottom_markers:
                            top_bottom_markers[found_top_fractal] = "上顶"
                        if found_bottom_fractal not in top_bottom_markers:
                            top_bottom_markers[found_bottom_fractal] = "下底"
                
                # 当前下底，前一个是上顶
                elif prev_marker == "上顶" and curr_marker == "下底":
                    # 有效顶底组合的二次调整
                    # 在两个有效分型之间寻找一个顶分型和一个底分型
                    start_idx = prev_idx + 1
                    end_idx = curr_idx - 1
                    
                    found_top_fractal = None
                    found_bottom_fractal = None
                    
                    # 1. 先从前一个上顶开始，寻找一个间隔大于3个K线的底分型
                    for j in range(start_idx, end_idx + 1):
                        if j in bottom_fractals:  # 是底分型
                            # 检查底分型距离前顶顶分型至少3个K线
                            if abs(j - prev_idx) >= 4:  # 至少间隔3个K线，即4个位置差
                                # 2. 在找到的底分型之后，寻找一个间隔大于3个K线的顶分型
                                for k in range(j + 1, end_idx + 1):  # 在底分型之后寻找顶分型
                                    if k in top_fractals:  # 是顶分型
                                        # 3. 找到的这个顶分型距离有效底底组合间隔大于3个K线
                                        if abs(k - curr_idx) >= 4 and abs(k - j) >= 4:  # 顶分型距离底底分型和底分型都至少3个K线
                                            # 检查顶的最高点是否高于底的最低点
                                            top_high = kline_series._sorted_klines[k].high
                                            bottom_low = kline_series._sorted_klines[j].low
                                            if top_high > bottom_low:  # 顶的最高点高于底的最低点
                                                found_top_fractal = k
                                                found_bottom_fractal = j
                                                break  # 找到第一对就退出
                                if found_top_fractal is not None and found_bottom_fractal is not None:
                                    break  # 找到第一对就退出
                    
                    # 如果找到符合条件的顶分型和底分型，则标记
                    if found_top_fractal is not None and found_bottom_fractal is not None:
                        # 找到的中间顶分型和底分型也需要标记
                        if found_top_fractal not in top_bottom_markers:
                            top_bottom_markers[found_top_fractal] = "上顶"
                        if found_bottom_fractal not in top_bottom_markers:
                            top_bottom_markers[found_bottom_fractal] = "下底"
        
        # 按索引排序所有顶底标记
        top_bottom_pairs = sorted([(idx, marker) for idx, marker in top_bottom_markers.items() if marker in ["上顶", "下底"]], key=lambda x: x[0])
        
        # 识别笔
        # 根据3.6.3：第一个顶底是一笔，但它没有笔开始的记录（只有结束）
        # 但应该把第一个不完整的笔也返回，这样就不会错位了
        if len(top_bottom_pairs) >= 1:
            # 第一个顶底：创建一个不完整的笔（只有结束，没有开始）
            first_idx, first_marker = top_bottom_pairs[0]
            first_pen = Pen(
                start_kline=kline_series[first_idx],  # 虽然是不完整的，但用同一个K线作为开始和结束
                end_kline=kline_series[first_idx],
                direction='up' if first_marker == "上顶" else 'down',
                klines=[kline_series[first_idx]]
            )
            pens.append(first_pen)
        
        # 后续的顶底：创建完整的笔
        for i in range(len(top_bottom_pairs) - 1):
            current_idx, current_marker = top_bottom_pairs[i]
            next_idx, next_marker = top_bottom_pairs[i + 1]
            
            # 确保顶底标记交替出现
            if current_marker != next_marker:
                # 创建笔对象
                start_kline = kline_series[current_idx]
                end_kline = kline_series[next_idx]
                direction = 'up' if current_marker == "下底" else 'down'
                
                # 获取笔包含的所有K线
                pen_klines = [kline_series[j] for j in range(current_idx, next_idx + 1)]
                
                pen = Pen(
                    start_kline=start_kline,
                    end_kline=end_kline,
                    direction=direction,
                    klines=pen_klines
                )
                
                if pen.is_valid():
                    pens.append(pen)
        
        return pens, top_bottom_markers, valid_top_fractals, valid_bottom_fractals
    
    def _identify_segments(self, pen_series: PenSeries) -> List[Segment]:
        """
        根据笔识别线段
        
        Args:
            pen_series: 笔序列
            
        Returns:
            线段对象列表
        """
        segments = []
        pens = pen_series.pens
        
        if len(pens) < self.min_segment_pen:
            return segments
        
        i = 0
        while i < len(pens) - 2:
            # 尝试构建线段
            segment_pens = [pens[i]]
            
            j = i + 1
            while j < len(pens):
                # 检查笔的方向是否交替
                if pens[j].direction != segment_pens[-1].direction:
                    segment_pens.append(pens[j])
                    
                    # 如果满足线段条件
                    if len(segment_pens) >= self.min_segment_pen:
                        # 创建线段对象
                        start_pen = segment_pens[0]
                        end_pen = segment_pens[-1]
                        direction = 'up' if start_pen.direction == 'up' else 'down'
                        
                        segment = Segment(
                            start_pen=start_pen,
                            end_pen=end_pen,
                            direction=direction,
                            pens=segment_pens.copy()
                        )
                        
                        if segment.is_valid():
                            segments.append(segment)
                            i = j  # 移动到当前线段结束位置
                            break
                
                j += 1
            
            i += 1
        
        return segments
    
    def _identify_central_pivots(self, segment_series: SegmentSeries) -> List[CentralPivot]:
        """
        根据线段识别中枢
        
        Args:
            segment_series: 线段序列
            
        Returns:
            中枢对象列表
        """
        pivots = []
        segments = segment_series.segments
        
        if len(segments) < 3:
            return pivots
        
        for i in range(len(segments) - 2):
            # 检查三个连续线段是否构成中枢
            seg1 = segments[i]
            seg2 = segments[i + 1]
            seg3 = segments[i + 2]
            
            # 确保线段方向交替
            if (seg1.direction != seg2.direction and 
                seg2.direction != seg3.direction):
                
                # 计算中枢参数
                if seg1.direction == 'up':
                    zg = min(seg1.end_price, seg3.end_price)  # 中枢高点
                    zd = max(seg1.start_price, seg3.start_price)  # 中枢低点
                    gg = max(seg1.end_price, seg3.end_price)  # 中枢最高点
                    dd = min(seg1.start_price, seg3.start_price)  # 中枢最低点
                else:
                    zg = min(seg1.start_price, seg3.start_price)
                    zd = max(seg1.end_price, seg3.end_price)
                    gg = max(seg1.start_price, seg3.start_price)
                    dd = min(seg1.end_price, seg3.end_price)
                
                # 确保中枢有效
                if zg > zd:
                    pivot = CentralPivot(
                        zg=zg,
                        zd=zd,
                        gg=gg,
                        dd=dd,
                        segments=[seg1, seg2, seg3]
                    )
                    pivots.append(pivot)
        
        return pivots
    
    def get_trend_strength(self, analysis_result: Dict[str, Any]) -> Dict[str, float]:
        """
        分析趋势强度
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            趋势强度指标
        """
        pen_series = analysis_result['pen_series']
        segment_series = analysis_result['segment_series']
        
        if len(pen_series) == 0 or len(segment_series) == 0:
            return {'up_trend': 0.0, 'down_trend': 0.0, 'consolidation': 1.0}
        
        # 计算笔的趋势强度
        up_pens = pen_series.get_high_pens()
        down_pens = pen_series.get_low_pens()
        
        up_trend_strength = sum(pen.length for pen in up_pens) / len(pen_series)
        down_trend_strength = sum(pen.length for pen in down_pens) / len(pen_series)
        
        # 计算线段的趋势强度
        up_segments = segment_series.get_up_segments()
        down_segments = segment_series.get_down_segments()
        
        if up_segments:
            up_trend_strength += sum(seg.length for seg in up_segments) / len(segment_series)
        if down_segments:
            down_trend_strength += sum(seg.length for seg in down_segments) / len(segment_series)
        
        total_strength = up_trend_strength + down_trend_strength
        
        if total_strength > 0:
            up_ratio = up_trend_strength / total_strength
            down_ratio = down_trend_strength / total_strength
            consolidation_ratio = 1.0 - (up_ratio + down_ratio)
        else:
            up_ratio = down_ratio = 0.0
            consolidation_ratio = 1.0
        
        return {
            'up_trend': up_ratio,
            'down_trend': down_ratio,
            'consolidation': consolidation_ratio
        }
    
    def _identify_pen_pivots(self, kline_series: KLineSeries, top_bottom_markers: Dict[int, str]) -> Tuple[Dict[int, float], Dict[int, float], Dict[int, datetime], Dict[int, datetime]]:
        """
        识别一级笔中枢（基于3.7.4的实现）
        
        Args:
            kline_series: K线序列
            top_bottom_markers: 顶底标记字典
            
        Returns:
            (zg_dict, zd_dict, zg_time_dict, zd_time_dict)
        """
        zg_dict = {}  # 中枢顶价格，key为K线索引
        zd_dict = {}  # 中枢底价格，key为K线索引
        zg_time_dict = {}  # 中枢顶时间，key为K线索引
        zd_time_dict = {}  # 中枢底时间，key为K线索引
        
        # 按索引排序所有顶底标记
        sorted_top_bottom = sorted([(idx, marker) for idx, marker in top_bottom_markers.items() if marker in ["上顶", "下底"]], key=lambda x: x[0])
        
        if len(sorted_top_bottom) < 1:
            return zg_dict, zd_dict, zg_time_dict, zd_time_dict
        
        # 为每个顶底计算ZG和ZD
        top_bottom_zg = {}
        top_bottom_zd = {}
        top_bottom_zg_time = {}
        top_bottom_zd_time = {}
        
        # 3.7.4.2 初始化第一个中枢
        first_idx, first_marker = sorted_top_bottom[0]
        first_kline = kline_series._sorted_klines[first_idx]
        
        prev_zg = None
        prev_zd = None
        prev_zg_time = None
        prev_zd_time = None
        
        if first_marker == "上顶":
            prev_zg = first_kline.high
            prev_zg_time = first_kline.timestamp
        else:  # 下底
            prev_zd = first_kline.low
            prev_zd_time = first_kline.timestamp
        
        # 记录第一个顶底的ZG和ZD
        top_bottom_zg[first_idx] = prev_zg
        top_bottom_zd[first_idx] = prev_zd
        top_bottom_zg_time[first_idx] = prev_zg_time
        top_bottom_zd_time[first_idx] = prev_zd_time
        
        # 3.7.4.3 第二个顶底开始
        if len(sorted_top_bottom) >= 2:
            second_idx, second_marker = sorted_top_bottom[1]
            second_kline = kline_series._sorted_klines[second_idx]
            
            if second_marker == "上顶":
                # 当前顶底是上顶
                prev_zg = second_kline.high
                prev_zg_time = second_kline.timestamp
                prev_zd = first_kline.low
                prev_zd_time = first_kline.timestamp
            else:  # 下底
                # 当前顶底是下底
                prev_zg = first_kline.high
                prev_zg_time = first_kline.timestamp
                prev_zd = second_kline.low
                prev_zd_time = second_kline.timestamp
            
            # 记录第二个顶底的ZG和ZD
            top_bottom_zg[second_idx] = prev_zg
            top_bottom_zd[second_idx] = prev_zd
            top_bottom_zg_time[second_idx] = prev_zg_time
            top_bottom_zd_time[second_idx] = prev_zd_time
        
        # 3.7.4.4 正常情况顶底判断（第三个及以后的顶底）
        for i in range(2, len(sorted_top_bottom)):
            curr_idx, curr_marker = sorted_top_bottom[i]
            curr_kline = kline_series._sorted_klines[curr_idx]
            
            if curr_marker == "下底":
                # 当下K线是下底
                curr_low = curr_kline.low
                
                if prev_zd is not None and prev_zg is not None:
                    if curr_low >= prev_zd and curr_low <= prev_zg:
                        # 在前一个K线中枢内
                        new_zg = prev_zg
                        new_zd = curr_low
                        new_zg_time = prev_zg_time
                        new_zd_time = curr_kline.timestamp
                    elif curr_low < prev_zd:
                        # 在前一个K线中枢下
                        new_zg = prev_zg
                        new_zd = prev_zd
                        new_zg_time = prev_zg_time
                        new_zd_time = prev_zd_time
                    else:  # curr_low > prev_zg
                        # 在前一个K线中枢上
                        # 找到前一个上顶
                        prev_top_idx = None
                        prev_top_high = None
                        for j in range(i-1, -1, -1):
                            check_idx, check_marker = sorted_top_bottom[j]
                            if check_marker == "上顶":
                                prev_top_idx = check_idx
                                prev_top_high = kline_series._sorted_klines[prev_top_idx].high
                                break
                        
                        if prev_top_high is not None:
                            new_zg = prev_top_high
                            new_zd = curr_low
                            new_zg_time = kline_series._sorted_klines[prev_top_idx].timestamp
                            new_zd_time = curr_kline.timestamp
                        else:
                            new_zg = prev_zg
                            new_zd = curr_low
                            new_zg_time = prev_zg_time
                            new_zd_time = curr_kline.timestamp
                else:
                    new_zg = prev_zg
                    new_zd = curr_low
                    new_zg_time = prev_zg_time
                    new_zd_time = curr_kline.timestamp
                
                prev_zg = new_zg
                prev_zd = new_zd
                prev_zg_time = new_zg_time
                prev_zd_time = new_zd_time
            
            else:  # 上顶
                # 当下K线是上顶
                curr_high = curr_kline.high
                
                if prev_zd is not None and prev_zg is not None:
                    if curr_high >= prev_zd and curr_high <= prev_zg:
                        # 在前一个K线中枢内
                        new_zg = curr_high
                        new_zd = prev_zd
                        new_zg_time = curr_kline.timestamp
                        new_zd_time = prev_zd_time
                    elif curr_high > prev_zg:
                        # 在前一个K线中枢上
                        new_zg = prev_zg
                        new_zd = prev_zd
                        new_zg_time = prev_zg_time
                        new_zd_time = prev_zd_time
                    else:  # curr_high < prev_zd
                        # 在前一个K线中枢下
                        # 找到前一个下底
                        prev_bottom_idx = None
                        prev_bottom_low = None
                        for j in range(i-1, -1, -1):
                            check_idx, check_marker = sorted_top_bottom[j]
                            if check_marker == "下底":
                                prev_bottom_idx = check_idx
                                prev_bottom_low = kline_series._sorted_klines[prev_bottom_idx].low
                                break
                        
                        if prev_bottom_low is not None:
                            new_zg = curr_high
                            new_zd = prev_bottom_low
                            new_zg_time = curr_kline.timestamp
                            new_zd_time = kline_series._sorted_klines[prev_bottom_idx].timestamp
                        else:
                            new_zg = curr_high
                            new_zd = prev_zd
                            new_zg_time = curr_kline.timestamp
                            new_zd_time = prev_zd_time
                else:
                    new_zg = curr_high
                    new_zd = prev_zd
                    new_zg_time = curr_kline.timestamp
                    new_zd_time = prev_zd_time
                
                prev_zg = new_zg
                prev_zd = new_zd
                prev_zg_time = new_zg_time
                prev_zd_time = new_zd_time
            
            # 记录当前顶底的ZG和ZD
            top_bottom_zg[curr_idx] = prev_zg
            top_bottom_zd[curr_idx] = prev_zd
            top_bottom_zg_time[curr_idx] = prev_zg_time
            top_bottom_zd_time[curr_idx] = prev_zd_time
        
        # 3.7.4.5 非顶底K线的数据沿用规则
        # 为每个K线设置ZG和ZD
        last_zg = None
        last_zd = None
        last_zg_time = None
        last_zd_time = None
        
        # 从前向后遍历，确保每个K线都有ZG和ZD
        for i in range(len(kline_series._sorted_klines)):
            # 检查这个K线是否是顶底标记
            is_top_bottom = i in top_bottom_zg
            
            if is_top_bottom:
                # 如果是顶底标记，使用之前计算的ZG和ZD
                last_zg = top_bottom_zg[i]
                last_zd = top_bottom_zd[i]
                last_zg_time = top_bottom_zg_time[i]
                last_zd_time = top_bottom_zd_time[i]
            
            # 为当前K线设置ZG和ZD（顶底K线和非顶底K线都使用最近的）
            zg_dict[i] = last_zg
            zd_dict[i] = last_zd
            zg_time_dict[i] = last_zg_time
            zd_time_dict[i] = last_zd_time
        
        return zg_dict, zd_dict, zg_time_dict, zd_time_dict
