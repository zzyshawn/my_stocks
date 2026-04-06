"""
技术指标计算工具
"""

import numpy as np
from typing import List, Optional
from ..core.kline import KLine, KLineSeries


class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_ma(klines: List[KLine], period: int) -> List[Optional[float]]:
        """
        计算移动平均线
        
        Args:
            klines: K线数据列表
            period: 周期
            
        Returns:
            移动平均值列表
        """
        if len(klines) < period:
            return [None] * len(klines)
        
        closes = [k.close for k in klines]
        ma_values = []
        
        for i in range(len(closes)):
            if i < period - 1:
                ma_values.append(None)
            else:
                ma = sum(closes[i-period+1:i+1]) / period
                ma_values.append(ma)
        
        return ma_values
    
    @staticmethod
    def calculate_ema(klines: List[KLine], period: int) -> List[Optional[float]]:
        """
        计算指数移动平均线
        
        Args:
            klines: K线数据列表
            period: 周期
            
        Returns:
            EMA值列表
        """
        if len(klines) < period:
            return [None] * len(klines)
        
        closes = [k.close for k in klines]
        ema_values = []
        
        # 计算平滑因子
        alpha = 2.0 / (period + 1)
        
        # 第一个EMA使用简单移动平均
        first_ema = sum(closes[:period]) / period
        ema_values.extend([None] * (period - 1))
        ema_values.append(first_ema)
        
        # 计算后续EMA
        for i in range(period, len(closes)):
            ema = alpha * closes[i] + (1 - alpha) * ema_values[i-1]
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def calculate_macd(klines: List[KLine], 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> dict:
        """
        计算MACD指标
        
        Args:
            klines: K线数据列表
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
            
        Returns:
            MACD指标字典
        """
        closes = [k.close for k in klines]
        
        # 计算EMA
        ema_fast = TechnicalIndicators._calculate_ema_array(closes, fast_period)
        ema_slow = TechnicalIndicators._calculate_ema_array(closes, slow_period)
        
        # 计算DIF
        dif = []
        for i in range(len(closes)):
            if ema_fast[i] is None or ema_slow[i] is None:
                dif.append(None)
            else:
                dif.append(ema_fast[i] - ema_slow[i])
        
        # 计算DEA
        dea = TechnicalIndicators._calculate_ema_array(dif, signal_period)
        
        # 计算MACD柱
        macd_hist = []
        for i in range(len(closes)):
            if dif[i] is None or dea[i] is None:
                macd_hist.append(None)
            else:
                macd_hist.append((dif[i] - dea[i]) * 2)
        
        return {
            'dif': dif,
            'dea': dea,
            'macd': macd_hist
        }
    
    @staticmethod
    def calculate_rsi(klines: List[KLine], period: int = 14) -> List[Optional[float]]:
        """
        计算RSI指标
        
        Args:
            klines: K线数据列表
            period: 周期
            
        Returns:
            RSI值列表
        """
        if len(klines) < period + 1:
            return [None] * len(klines)
        
        closes = [k.close for k in klines]
        rsi_values = []
        
        # 计算价格变化
        price_changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        for i in range(len(closes)):
            if i < period:
                rsi_values.append(None)
            else:
                # 计算上涨和下跌幅度
                gains = [max(0, change) for change in price_changes[i-period:i]]
                losses = [max(0, -change) for change in price_changes[i-period:i]]
                
                avg_gain = sum(gains) / period
                avg_loss = sum(losses) / period
                
                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                
                rsi_values.append(rsi)
        
        return rsi_values
    
    @staticmethod
    def calculate_bollinger_bands(klines: List[KLine], 
                                 period: int = 20, 
                                 std_dev: float = 2.0) -> dict:
        """
        计算布林带
        
        Args:
            klines: K线数据列表
            period: 周期
            std_dev: 标准差倍数
            
        Returns:
            布林带指标字典
        """
        if len(klines) < period:
            empty = [None] * len(klines)
            return {'upper': empty, 'middle': empty, 'lower': empty}
        
        closes = [k.close for k in klines]
        upper_band = []
        middle_band = []
        lower_band = []
        
        for i in range(len(closes)):
            if i < period - 1:
                upper_band.append(None)
                middle_band.append(None)
                lower_band.append(None)
            else:
                # 计算中轨（移动平均）
                ma = sum(closes[i-period+1:i+1]) / period
                middle_band.append(ma)
                
                # 计算标准差
                std = np.std(closes[i-period+1:i+1])
                
                # 计算上下轨
                upper_band.append(ma + std_dev * std)
                lower_band.append(ma - std_dev * std)
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }
    
    @staticmethod
    def _calculate_ema_array(values: List[Optional[float]], period: int) -> List[Optional[float]]:
        """计算EMA数组（内部方法）"""
        if len(values) < period:
            return [None] * len(values)
        
        ema_values = []
        alpha = 2.0 / (period + 1)
        
        # 找到第一个有效窗口
        start_idx = 0
        while start_idx < len(values) - period + 1:
            window = values[start_idx:start_idx + period]
            if all(v is not None for v in window):
                break
            start_idx += 1
        
        if start_idx >= len(values) - period + 1:
            return [None] * len(values)
        
        # 第一个EMA使用简单移动平均
        first_ema = sum(values[start_idx:start_idx + period]) / period
        ema_values.extend([None] * start_idx)
        ema_values.extend([None] * (period - 1))
        ema_values.append(first_ema)
        
        # 计算后续EMA
        for i in range(start_idx + period, len(values)):
            if values[i] is None or ema_values[i-1] is None:
                ema_values.append(None)
            else:
                ema = alpha * values[i] + (1 - alpha) * ema_values[i-1]
                ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def calculate_volume_profile(klines: List[KLine], 
                                price_bins: int = 20) -> dict:
        """
        计算成交量分布
        
        Args:
            klines: K线数据列表
            price_bins: 价格区间数量
            
        Returns:
            成交量分布字典
        """
        if not klines:
            return {'prices': [], 'volumes': []}
        
        # 获取价格范围
        prices = [k.close for k in klines]
        min_price = min(prices)
        max_price = max(prices)
        
        # 创建价格区间
        price_range = max_price - min_price
        bin_size = price_range / price_bins
        
        # 初始化成交量数组
        volumes = [0] * price_bins
        
        # 分配成交量到各个价格区间
        for kline in klines:
            if kline.volume is not None:
                # 计算价格所属的区间
                bin_index = int((kline.close - min_price) / bin_size)
                bin_index = min(bin_index, price_bins - 1)  # 防止越界
                volumes[bin_index] += kline.volume
        
        # 生成价格标签
        price_labels = [min_price + i * bin_size + bin_size/2 for i in range(price_bins)]
        
        return {
            'prices': price_labels,
            'volumes': volumes
        }
    
    @staticmethod
    def calculate_rsi_h(klines: List[KLine], period: int = 6) -> List[Optional[float]]:
        """
        计算 RSI_H（基于最高价）
        
        Args:
            klines: K线数据列表
            period: 周期，默认6
            
        Returns:
            RSI_H 值列表
        """
        if len(klines) < period + 1:
            return [None] * len(klines)
        
        highs = [k.high for k in klines]
        return TechnicalIndicators._calculate_rsi_by_series(highs, period)
    
    @staticmethod
    def calculate_rsi_l(klines: List[KLine], period: int = 6) -> List[Optional[float]]:
        """
        计算 RSI_L（基于最低价）
        
        Args:
            klines: K线数据列表
            period: 周期，默认6
            
        Returns:
            RSI_L 值列表
        """
        if len(klines) < period + 1:
            return [None] * len(klines)
        
        lows = [k.low for k in klines]
        return TechnicalIndicators._calculate_rsi_by_series(lows, period)
    
    @staticmethod
    def _calculate_rsi_by_series(values: List[float], period: int) -> List[Optional[float]]:
        """
        RSI 核心计算逻辑（通用）
        
        Args:
            values: 价格序列
            period: 周期
            
        Returns:
            RSI 值列表
        """
        rsi_values = []
        
        # 计算价格变化
        price_changes = [values[i] - values[i-1] for i in range(1, len(values))]
        
        for i in range(len(values)):
            if i < period:
                rsi_values.append(None)
            else:
                # 计算上涨和下跌幅度
                gains = [max(0, change) for change in price_changes[i-period:i]]
                losses = [max(0, -change) for change in price_changes[i-period:i]]
                
                avg_gain = sum(gains) / period
                avg_loss = sum(losses) / period
                
                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                
                rsi_values.append(rsi)
        
        return rsi_values
    
    @staticmethod
    def calculate_volume_ma(klines: List[KLine], period: int = 10) -> List[Optional[float]]:
        """
        计算成交量均线
        
        Args:
            klines: K线数据列表
            period: 周期，默认10
            
        Returns:
            成交量均线值列表
        """
        if len(klines) < period:
            return [None] * len(klines)
        
        volumes = [k.volume for k in klines]
        ma_values = []
        
        for i in range(len(volumes)):
            if i < period - 1:
                ma_values.append(None)
            else:
                ma = sum(volumes[i-period+1:i+1]) / period
                ma_values.append(ma)
        
        return ma_values
    
    @staticmethod
    def calculate_chip_distribution(
        klines_5min: List[KLine],
        target_timestamp,
        lookback: int = 1,
        price_bins: int = 50
    ) -> dict:
        """
        计算筹码分布
        
        Args:
            klines_5min: 5分钟K线数据列表
            target_timestamp: 目标时间点
            lookback: 回看周期数（1-100）
            price_bins: 价格区间数量
            
        Returns:
            筹码分布字典
        """
        from datetime import datetime
        
        if not klines_5min:
            return {
                'prices': [],
                'volumes': [],
                'profit_ratio': 0,
                'avg_cost': 0,
                'concentration': 0,
                'current_price': 0
            }
        
        # 筛选目标时间点之前的5分钟K线
        # 计算回看的时间范围（每个周期 = 1天 = 48根5分钟K线）
        klines_per_day = 48
        klines_to_use = lookback * klines_per_day
        
        # 找到目标时间点的索引
        target_idx = None
        for i, kline in enumerate(klines_5min):
            if kline.timestamp <= target_timestamp:
                target_idx = i
        
        if target_idx is None:
            target_idx = len(klines_5min) - 1
        
        # 获取回看范围内的K线
        start_idx = max(0, target_idx - klines_to_use + 1)
        selected_klines = klines_5min[start_idx:target_idx + 1]
        
        if not selected_klines:
            return {
                'prices': [],
                'volumes': [],
                'profit_ratio': 0,
                'avg_cost': 0,
                'concentration': 0,
                'current_price': 0
            }
        
        # 获取价格范围
        all_prices = []
        for k in selected_klines:
            all_prices.extend([k.high, k.low])
        
        min_price = min(all_prices)
        max_price = max(all_prices)
        
        # 创建价格区间
        price_range = max_price - min_price
        if price_range == 0:
            price_range = 0.01
        
        bin_size = price_range / price_bins
        
        # 初始化筹码分布数组
        chips = [0.0] * price_bins
        
        # 将每根K线的成交量按价格区间分配
        for kline in selected_klines:
            if kline.volume is None or kline.volume == 0:
                continue
            
            # 计算这根K线的价格区间
            kline_min_idx = int((kline.low - min_price) / bin_size)
            kline_max_idx = int((kline.high - min_price) / bin_size)
            
            kline_min_idx = max(0, min(kline_min_idx, price_bins - 1))
            kline_max_idx = max(0, min(kline_max_idx, price_bins - 1))
            
            if kline_min_idx == kline_max_idx:
                # 价格区间在同一格
                chips[kline_min_idx] += kline.volume
            else:
                # 价格区间跨多个格，按比例分配
                price_range_in_kline = kline.high - kline.low
                if price_range_in_kline > 0:
                    for idx in range(kline_min_idx, kline_max_idx + 1):
                        bin_low = min_price + idx * bin_size
                        bin_high = min_price + (idx + 1) * bin_size
                        
                        # 计算该格与K线重叠的区间
                        overlap_low = max(bin_low, kline.low)
                        overlap_high = min(bin_high, kline.high)
                        overlap_range = max(0, overlap_high - overlap_low)
                        
                        # 按重叠比例分配成交量
                        ratio = overlap_range / price_range_in_kline
                        chips[idx] += kline.volume * ratio
        
        # 生成价格标签
        price_labels = [min_price + i * bin_size + bin_size / 2 for i in range(price_bins)]
        
        # 当前价格（最后一个K线的收盘价）
        current_price = selected_klines[-1].close
        
        # 计算平均成本
        total_volume = sum(chips)
        if total_volume > 0:
            avg_cost = sum(p * v for p, v in zip(price_labels, chips)) / total_volume
        else:
            avg_cost = current_price
        
        # 计算获利比例
        if total_volume > 0:
            profit_volume = sum(v for p, v in zip(price_labels, chips) if p < current_price)
            profit_ratio = profit_volume / total_volume
        else:
            profit_ratio = 0
        
        # 计算90%筹码区间
        sorted_chips = sorted(zip(price_labels, chips), key=lambda x: x[1], reverse=True)
        cumulative = 0
        chip_90_prices = []
        chip_70_prices = []
        
        for price, volume in sorted_chips:
            cumulative += volume
            ratio = cumulative / total_volume if total_volume > 0 else 0
            
            if ratio <= 0.90:
                chip_90_prices.append(price)
            if ratio <= 0.70:
                chip_70_prices.append(price)
        
        # 计算集中度
        if chip_90_prices:
            concentration = 1 - (max(chip_90_prices) - min(chip_90_prices)) / current_price
        else:
            concentration = 0
        
        return {
            'prices': price_labels,
            'volumes': chips,
            'profit_ratio': profit_ratio,
            'avg_cost': avg_cost,
            'concentration': concentration,
            'current_price': current_price,
            'chip_90_range': (min(chip_90_prices), max(chip_90_prices)) if chip_90_prices else (current_price, current_price),
            'chip_70_range': (min(chip_70_prices), max(chip_70_prices)) if chip_70_prices else (current_price, current_price)
        }