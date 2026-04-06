"""
数据准备模块 - 缠论实时交易模拟系统

功能：
1. 按日期循环处理每个交易日
2. 逐根处理48根5分钟数据（09:30-11:30, 13:00-15:00）
3. 累积生成多时间框架数据（5分钟/30分钟/日线）
4. 计算并保存技术指标

输出目录结构：
{base_dir}/{code}/backtest/{date}/
├── {code}_rt_5_0.xlsx ~ {code}_rt_5_47.xlsx      (48个5分钟)
├── {code}_rt_30_0.xlsx ~ {code}_rt_30_7.xlsx     (8个30分钟，累积更新)
├── {code}_rt_d_0.xlsx                            (1个日线，累积更新)
├── {code}_ind_5_0.xlsx ~ {code}_ind_5_47.xlsx    (48个5分钟指标)
├── {code}_ind_30_0.xlsx ~ {code}_ind_30_7.xlsx   (8个30分钟指标)
└── {code}_ind_d_0.xlsx                           (1个日线指标)
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger

from src.utils.config import get_config, ConfigManager
from src.analysis.indicators import ma, ema, macd, kdj, rsi, bollinger


# 交易时间列表（48根5分钟K线）
TRADING_TIME_LIST = [
    # 上午 09:30-11:30 (24根)
    "09:30", "09:35", "09:40", "09:45", "09:50", "09:55",
    "10:00", "10:05", "10:10", "10:15", "10:20", "10:25", "10:30",
    "10:35", "10:40", "10:45", "10:50", "10:55", "11:00",
    "11:05", "11:10", "11:15", "11:20", "11:25", "11:30",
    # 下午 13:00-15:00 (24根)
    "13:00", "13:05", "13:10", "13:15", "13:20", "13:25", "13:30",
    "13:35", "13:40", "13:45", "13:50", "13:55", "14:00",
    "14:05", "14:10", "14:15", "14:20", "14:25", "14:30",
    "14:35", "14:40", "14:45", "14:50", "14:55", "15:00"
]


class DataPreparation:
    """数据准备类 - 实时模拟数据生成"""

    def __init__(self, config: Optional[ConfigManager] = None):
        """
        初始化数据准备模块

        Args:
            config: 配置管理器实例，默认使用全局配置
        """
        self.config = config or get_config()
        self.base_dir = Path(self.config.get("data.base_dir"))

        # 回测时间配置
        self.train_end = self.config.get("backtest.train_end")  # "2024-06-30"
        self.test_start = self.config.get("backtest.start_time")  # "2024-09-01"
        self.test_end = self.config.get("backtest.end_time")  # "2024-12-31"

        # 指标配置
        self.ma_periods = self.config.get("analysis.ma_periods", {})
        self.macd_config = self.config.get("analysis.macd", {})
        self.kdj_config = self.config.get("analysis.kdj", {})
        self.rsi_periods = self.config.get("analysis.rsi_periods", [6, 12, 24])
        self.bollinger_config = self.config.get("analysis.bollinger", {})

        logger.info(f"数据准备模块初始化完成")
        logger.info(f"数据目录: {self.base_dir}")
        logger.info(f"测试区间: {self.test_start} ~ {self.test_end}")

    def load_5min_data(self, stock_code: str) -> pd.DataFrame:
        """
        加载5分钟K线数据

        Args:
            stock_code: 股票代码，如 "000001"

        Returns:
            5分钟K线数据DataFrame
        """
        file_path = self.config.get_kline_file_path(stock_code, "5")

        if not file_path.exists():
            raise FileNotFoundError(f"5分钟K线数据文件不存在: {file_path}")

        df = pd.read_excel(file_path)

        # 确保日期列是datetime类型
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'])

        # 过滤出交易时间内的数据
        df['时间'] = df['日期'].dt.strftime('%H:%M')
        df = df[df['时间'].isin(TRADING_TIME_LIST)]

        logger.info(f"加载 {stock_code} 5分钟数据: {len(df)} 条记录")
        return df

    def get_trading_dates(self, df: pd.DataFrame) -> List[datetime]:
        """
        从5分钟数据中提取交易日期列表

        Args:
            df: 5分钟K线数据

        Returns:
            交易日期列表（去重且排序）
        """
        dates = df['日期'].dt.date.unique()
        return sorted([datetime.combine(d, datetime.min.time()) for d in dates])

    def filter_test_dates(self, dates: List[datetime]) -> List[datetime]:
        """
        过滤出测试区间内的交易日

        Args:
            dates: 所有交易日列表

        Returns:
            测试区间内的交易日列表
        """
        test_start = pd.to_datetime(self.test_start)
        test_end = pd.to_datetime(self.test_end)

        filtered = [d for d in dates if test_start <= d <= test_end]
        logger.info(f"测试区间交易日数量: {len(filtered)}")
        return filtered

    def get_day_5min_bars(self, df: pd.DataFrame, date: datetime) -> pd.DataFrame:
        """
        获取指定日期的48根5分钟数据

        Args:
            df: 5分钟K线数据
            date: 指定日期

        Returns:
            当日48根5分钟数据
        """
        date_str = date.strftime('%Y-%m-%d')
        day_data = df[df['日期'].dt.date == pd.to_datetime(date_str).date()].copy()

        # 按时间排序
        day_data = day_data.sort_values('日期').reset_index(drop=True)

        return day_data

    def merge_to_30min(self, bars_5min: pd.DataFrame, position: int) -> Dict:
        """
        将5分钟数据累积合并为30分钟线

        关键：累积更新，不是满6根才生成
        位置0-5：都更新rt_30_0（累积中）
        位置6-11：都更新rt_30_1（累积中）

        Args:
            bars_5min: 当日所有5分钟数据
            position: 当前处理的位置(0-47)

        Returns:
            30分钟K线数据字典
        """
        # 当前30分钟区间的起始位置（0, 6, 12, 18, 24, 30, 36, 42）
        start_idx = (position // 6) * 6
        bars_in_30min = bars_5min.iloc[start_idx:position+1]

        if len(bars_in_30min) == 0:
            return None

        bar_30min = {
            '日期': bars_in_30min.iloc[0]['日期'],
            '开盘': bars_in_30min.iloc[0]['开盘'],
            '最高': bars_in_30min['最高'].max(),
            '最低': bars_in_30min['最低'].min(),
            '收盘': bars_in_30min.iloc[-1]['收盘'],
            '成交量': bars_in_30min['成交量'].sum()
        }

        return bar_30min

    def merge_to_daily(self, bars_5min: pd.DataFrame, position: int) -> Dict:
        """
        将5分钟数据累积合并为日线

        关键：持续累积更新

        Args:
            bars_5min: 当日所有5分钟数据
            position: 当前处理的位置(0-47)

        Returns:
            日线数据字典
        """
        bars_daily = bars_5min.iloc[:position+1]

        if len(bars_daily) == 0:
            return None

        bar_daily = {
            '日期': pd.to_datetime(bars_daily.iloc[0]['日期'].date()),
            '开盘': bars_daily.iloc[0]['开盘'],
            '最高': bars_daily['最高'].max(),
            '最低': bars_daily['最低'].min(),
            '收盘': bars_daily.iloc[-1]['收盘'],
            '成交量': bars_daily['成交量'].sum()
        }

        return bar_daily

    def calculate_indicators(self, bars: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标

        Args:
            bars: K线数据DataFrame

        Returns:
            包含指标值的DataFrame（仅最后一行）
        """
        if len(bars) == 0:
            return pd.DataFrame()

        close = bars['收盘']
        high = bars['最高']
        low = bars['最低']
        volume = bars['成交量']

        result = {}

        # MA均线
        all_ma_periods = []
        for group in ['short', 'medium', 'long']:
            all_ma_periods.extend(self.ma_periods.get(group, []))

        for period in all_ma_periods:
            result[f'MA{period}'] = ma(close, period).iloc[-1]

        # MACD
        fast = self.macd_config.get('fast_period', 12)
        slow = self.macd_config.get('slow_period', 26)
        signal = self.macd_config.get('signal_period', 9)
        dif, dea, macd_bar = macd(close, fast, slow, signal)
        result['DIF'] = dif.iloc[-1]
        result['DEA'] = dea.iloc[-1]
        result['MACD_BAR'] = macd_bar.iloc[-1]

        # RSI
        for period in self.rsi_periods:
            result[f'RSI{period}'] = rsi(close, period).iloc[-1]

        # KDJ
        n = self.kdj_config.get('n', 9)
        m1 = self.kdj_config.get('m1', 3)
        m2 = self.kdj_config.get('m2', 3)
        k, d, j = kdj(high, low, close, n, m1, m2)
        result['K'] = k.iloc[-1]
        result['D'] = d.iloc[-1]
        result['J'] = j.iloc[-1]

        # 布林带
        bb_period = self.bollinger_config.get('period', 20)
        bb_std = self.bollinger_config.get('std_dev', 2.0)
        upper, middle, lower = bollinger(close, bb_period, bb_std)
        result['BOLL_UPPER'] = upper.iloc[-1]
        result['BOLL_MIDDLE'] = middle.iloc[-1]
        result['BOLL_LOWER'] = lower.iloc[-1]

        # 成交量指标
        result['VMA5'] = ma(volume, 5).iloc[-1]
        result['VMA10'] = ma(volume, 10).iloc[-1]
        result['VMA20'] = ma(volume, 20).iloc[-1]

        # 成交量变异率
        if len(volume) > 1:
            result['VOL_CHANGE'] = (volume.iloc[-1] - volume.iloc[-2]) / volume.iloc[-2] * 100 if volume.iloc[-2] != 0 else 0
        else:
            result['VOL_CHANGE'] = 0

        return pd.DataFrame([result])

    def save_bar_to_excel(self, bar: Dict, file_path: Path):
        """
        保存单根K线到Excel

        Args:
            bar: K线数据字典
            file_path: 保存路径
        """
        df = pd.DataFrame([bar])
        df.to_excel(file_path, index=False)

    def save_indicators_to_excel(self, indicators_df: pd.DataFrame, file_path: Path):
        """
        保存指标数据到Excel

        Args:
            indicators_df: 指标DataFrame
            file_path: 保存路径
        """
        indicators_df.to_excel(file_path, index=False)

    def process_single_day(self, stock_code: str, date: datetime,
                          day_5min_bars: pd.DataFrame) -> Dict:
        """
        处理单个交易日的数据

        Args:
            stock_code: 股票代码
            date: 交易日期
            day_5min_bars: 当日48根5分钟数据

        Returns:
            处理结果字典
        """
        date_str = date.strftime('%Y-%m-%d')
        backtest_dir = self.base_dir / stock_code / "backtest" / date_str
        backtest_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"处理 {stock_code} {date_str}，共 {len(day_5min_bars)} 根5分钟数据")

        result = {
            'date': date_str,
            'bars_5min_count': 0,
            'bars_30min_count': 0,
            'indicators_count': 0
        }

        # 逐根处理48根5分钟数据
        for i in range(len(day_5min_bars)):
            # 1. 保存5分钟线
            bar_5min = day_5min_bars.iloc[i].to_dict()
            file_5min = backtest_dir / f"{stock_code}_rt_5_{i}.xlsx"
            self.save_bar_to_excel(bar_5min, file_5min)
            result['bars_5min_count'] += 1

            # 2. 累积生成30分钟线
            bar_30min = self.merge_to_30min(day_5min_bars, i)
            if bar_30min:
                position_30min = i // 6
                file_30min = backtest_dir / f"{stock_code}_rt_30_{position_30min}.xlsx"
                self.save_bar_to_excel(bar_30min, file_30min)
                result['bars_30min_count'] = position_30min + 1

            # 3. 累积生成日线
            bar_daily = self.merge_to_daily(day_5min_bars, i)
            if bar_daily:
                file_daily = backtest_dir / f"{stock_code}_rt_d_0.xlsx"
                self.save_bar_to_excel(bar_daily, file_daily)

            # 4. 计算并保存5分钟指标
            bars_5min_so_far = day_5min_bars.iloc[:i+1]
            indicators_df = self.calculate_indicators(bars_5min_so_far)
            if not indicators_df.empty:
                file_ind_5 = backtest_dir / f"{stock_code}_ind_5_{i}.xlsx"
                self.save_indicators_to_excel(indicators_df, file_ind_5)
                result['indicators_count'] += 1

        # 5. 计算并保存30分钟指标（每满6根计算一次）
        for j in range(8):  # 8根30分钟线
            end_pos = (j + 1) * 6
            bars_for_30min = day_5min_bars.iloc[:end_pos]
            if len(bars_for_30min) > 0:
                # 构建30分钟线DataFrame用于计算指标
                bars_30min_list = []
                for pos in range(j + 1):
                    bar_30 = self.merge_to_30min(day_5min_bars, min(pos * 6 + 5, len(day_5min_bars) - 1))
                    if bar_30:
                        bars_30min_list.append(bar_30)

                if bars_30min_list:
                    df_30min = pd.DataFrame(bars_30min_list)
                    indicators_30min = self.calculate_indicators(df_30min)
                    if not indicators_30min.empty:
                        file_ind_30 = backtest_dir / f"{stock_code}_ind_30_{j}.xlsx"
                        self.save_indicators_to_excel(indicators_30min, file_ind_30)

        # 6. 计算并保存日线指标
        if len(day_5min_bars) > 0:
            bars_daily_list = []
            for pos in range(len(day_5min_bars)):
                bar_d = self.merge_to_daily(day_5min_bars, pos)
                if bar_d:
                    bars_daily_list.append(bar_d)

            if bars_daily_list:
                df_daily = pd.DataFrame(bars_daily_list)
                indicators_daily = self.calculate_indicators(df_daily)
                if not indicators_daily.empty:
                    file_ind_d = backtest_dir / f"{stock_code}_ind_d_0.xlsx"
                    self.save_indicators_to_excel(indicators_daily, file_ind_d)

        logger.info(f"完成 {stock_code} {date_str}: "
                   f"5分钟={result['bars_5min_count']}, "
                   f"30分钟={result['bars_30min_count']}, "
                   f"指标={result['indicators_count']}")

        return result

    def process_stock(self, stock_code: str) -> Dict:
        """
        处理单个股票的实时模拟数据生成

        Args:
            stock_code: 股票代码

        Returns:
            处理结果字典
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"开始处理股票: {stock_code}")
        logger.info(f"{'='*60}")

        result = {
            'stock_code': stock_code,
            'status': 'success',
            'dates_processed': [],
            'errors': []
        }

        try:
            # 1. 加载5分钟数据
            df_5min = self.load_5min_data(stock_code)

            if len(df_5min) == 0:
                logger.warning(f"{stock_code} 5分钟数据为空，跳过")
                result['status'] = 'skipped'
                return result

            # 2. 获取测试区间内的交易日
            all_dates = self.get_trading_dates(df_5min)
            test_dates = self.filter_test_dates(all_dates)

            if len(test_dates) == 0:
                logger.warning(f"{stock_code} 在测试区间内无数据")
                result['status'] = 'no_data'
                return result

            # 3. 逐个日期处理
            for date in test_dates:
                try:
                    # 获取当日48根5分钟数据
                    day_bars = self.get_day_5min_bars(df_5min, date)

                    if len(day_bars) == 0:
                        logger.warning(f"{stock_code} {date.strftime('%Y-%m-%d')} 无数据，跳过")
                        continue

                    # 处理单日数据
                    day_result = self.process_single_day(stock_code, date, day_bars)
                    result['dates_processed'].append(day_result)

                except Exception as e:
                    error_msg = f"处理 {date.strftime('%Y-%m-%d')} 失败: {e}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)

        except FileNotFoundError as e:
            error_msg = f"文件不存在: {e}"
            logger.error(error_msg)
            result['status'] = 'error'
            result['errors'].append(error_msg)
        except Exception as e:
            error_msg = f"处理 {stock_code} 失败: {e}"
            logger.error(error_msg)
            result['status'] = 'error'
            result['errors'].append(error_msg)

        logger.info(f"\n股票 {stock_code} 处理完成: {len(result['dates_processed'])} 个交易日")
        return result

    def process_stocks(self, stock_codes: List[str]) -> List[Dict]:
        """
        批量处理多个股票

        Args:
            stock_codes: 股票代码列表

        Returns:
            处理结果列表
        """
        results = []

        for stock_code in stock_codes:
            result = self.process_stock(stock_code)
            results.append(result)

        return results


def prepare_single_stock(stock_code: str, config_path: str = None) -> Dict:
    """
    便捷函数：准备单个股票的实时模拟数据

    Args:
        stock_code: 股票代码
        config_path: 配置文件路径，默认使用全局配置

    Returns:
        处理结果字典
    """
    config = get_config(config_path) if config_path else get_config()
    prep = DataPreparation(config)
    return prep.process_stock(stock_code)


def prepare_from_watchlist(config_path: str = None) -> List[Dict]:
    """
    从监控清单批量准备数据

    Args:
        config_path: 配置文件路径

    Returns:
        处理结果列表
    """
    config = get_config(config_path) if config_path else get_config()

    # 读取监控清单
    watchlist_path = config.get_watchlist_path()

    if not watchlist_path.exists():
        raise FileNotFoundError(f"监控清单不存在: {watchlist_path}")

    df = pd.read_excel(watchlist_path)
    code_column = config.get("data_source.watchlist.code_column", "代码")

    if code_column not in df.columns:
        raise ValueError(f"监控清单缺少列: {code_column}")

    # 提取股票代码
    stock_codes = df[code_column].astype(str).str.zfill(6).tolist()

    logger.info(f"从监控清单读取到 {len(stock_codes)} 只股票")

    # 批量处理
    prep = DataPreparation(config)
    return prep.process_stocks(stock_codes)


if __name__ == "__main__":
    # 测试代码
    import sys

    # 配置日志
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")
    logger.add("logs/data_preparation.log", rotation="10 MB", level="INFO")

    # 测试单只股票
    test_code = "603906"  # 测试用股票
    if len(sys.argv) > 1:
        test_code = sys.argv[1]

    logger.info(f"开始测试数据准备模块，股票代码: {test_code}")

    try:
        result = prepare_single_stock(test_code)
        logger.info(f"处理结果:\n{result}")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise
