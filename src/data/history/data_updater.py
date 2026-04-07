"""
数据更新模块 - 主入口

用于每日更新股票K线数据，集成涨停池获取、K线下载和通知功能。

使用:
    python src/data/data_updater.py
"""

import os
import sys

# 设置环境变量解决 Windows 控制台中文乱码
os.environ['PYTHONIOENCODING'] = 'utf-8'

TDX2DB_PATH = r"D:\code\tdx-data\tdx2db"
if TDX2DB_PATH not in sys.path:
    sys.path.insert(0, TDX2DB_PATH)


def _fix_windows_encoding():
    """修复 Windows 控制台编码问题"""
    if sys.platform != 'win32':
        return
    import io
    # 只在主模块中修复一次
    if not hasattr(sys, '_encoding_fixed'):
        if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer:
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            except (ValueError, AttributeError):
                pass
        if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer:
            try:
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            except (ValueError, AttributeError):
                pass
        sys._encoding_fixed = True


_fix_windows_encoding()

import concurrent.futures
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

import my_tdx_data

logger = logging.getLogger("history_updater")
logger.setLevel(logging.DEBUG)

# 文件处理器 - 记录失败信息
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history_update.log")
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 支持直接运行和作为模块导入
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from src.data.history.globals import set_jin_ri, set_zt_list, get_zt_list
    from src.data.history.zt_pool_fetcher import ZtPoolFetcher
else:
    from .globals import set_jin_ri, set_zt_list, get_zt_list
    from .zt_pool_fetcher import ZtPoolFetcher


class DataUpdater:
    """数据更新器"""

    def __init__(
        self,
        data_dir: str,
        concept_file: str,
        watchlist_dir: str,
        watchlist_file: str = "check_list.xlsx",
        end_date: str = "2026-12-31",
    ):
        """
        初始化数据更新器

        Args:
            data_dir: 数据根目录 (H:/股票信息/股票数据库/daban)
            concept_file: 概念成分清单文件路径
            watchlist_dir: 监控清单目录
            watchlist_file: 监控清单文件名
            end_date: 数据获取结束日期
        """
        self.data_dir = data_dir
        self.stock_data_dir = os.path.join(data_dir, "股票数据")
        self.concept_file = concept_file
        self.watchlist_path = os.path.join(watchlist_dir, watchlist_file)
        self.end_date = end_date

        self.zt_fetcher = ZtPoolFetcher(data_dir, concept_file)

        self.today: str = ""
        self.trading_dates: List[str] = []
        self.stats: Dict = {}

        self._load_file_naming_config()

    def _load_file_naming_config(self):
        """从配置文件加载文件命名规则"""
        try:
            if __name__ == "__main__" and __package__ is None:
                from src.utils.config import get_config
            else:
                from ..utils.config import get_config

            config = get_config()
            kline_config = config.get("naming.files.kline", {})

            self.file_pattern = kline_config.get("pattern", "{symbol}_{period}")
            self.file_extension = kline_config.get("extension", ".xlsx")
            self.period_map = kline_config.get("period_map", {
                "daily": "d",
                "min30": "30",
                "min5": "5"
            })
        except Exception:
            self.file_pattern = "{symbol}_{period}"
            self.file_extension = ".xlsx"
            self.period_map = {"daily": "d", "min30": "30", "min5": "5"}

    def _get_kline_filename(self, symbol: str, period_key: str) -> str:
        """根据配置生成K线数据文件名"""
        period_id = self.period_map.get(period_key, period_key)
        filename = self.file_pattern.format(symbol=symbol, period=period_id)
        return f"{filename}{self.file_extension}"

    def get_trading_date(self, days: int = 10) -> Tuple[str, List[str]]:
        """
        获取最近交易日

        Args:
            days: 获取天数

        Returns:
            (最近交易日, 交易日列表)
        """
        self.today, self.trading_dates = self.zt_fetcher.get_trading_date(days)

        # 设置全局变量
        set_jin_ri(self.today)
        set_zt_list(self.trading_dates)

        return self.today, self.trading_dates

    def get_zt_pool(self) -> pd.DataFrame:
        """
        获取涨停股票池

        Returns:
            涨停股票DataFrame
        """
        if not self.today:
            self.get_trading_date()

        return self.zt_fetcher.get_zt_pool(self.today, with_concept=True)

    def update_watchlist(self) -> pd.DataFrame:
        """
        更新监控清单

        Returns:
            更新后的监控清单
        """
        if not self.today:
            self.get_trading_date()

        return self.zt_fetcher.update_watchlist(self.today, self.watchlist_path)

    def delete_single_stock(self, symbol: str, del_date: str) -> Dict:
        """
        删除单只股票指定日期及以后的历史数据

        Args:
            symbol: 股票代码
            del_date: 删除起始日期(YYYY-MM-DD)，删除该日期及以后的数据

        Returns:
            删除结果
        """
        try:
            stock_dir = os.path.join(self.stock_data_dir, symbol)
            if not os.path.exists(stock_dir):
                return {"symbol": symbol, "success": True, "message": "目录不存在，无需清理"}

            periods = ['daily', 'min30', 'min5']
            cleaned_periods = []

            for period_key in periods:
                file_name = self._get_kline_filename(symbol, period_key)
                file_path = os.path.join(stock_dir, file_name)

                if not os.path.exists(file_path):
                    continue

                try:
                    df_existing = pd.read_excel(file_path)
                    if df_existing.empty:
                        continue

                    date_col = df_existing.columns[0]
                    if date_col not in df_existing.columns:
                        continue

                    df_existing[date_col] = pd.to_datetime(df_existing[date_col])
                    mask = df_existing[date_col] >= pd.to_datetime(del_date)

                    if not mask.any():
                        continue

                    df_filtered = df_existing[~mask]
                    original_count = len(df_existing)
                    deleted_count = mask.sum()

                    if df_filtered.empty:
                        os.remove(file_path)
                        logger.info(f"已删除 {symbol} {period_key}: {file_name}")
                    else:
                        df_filtered.to_excel(file_path, index=False)
                        logger.info(f"已清理 {symbol} {period_key}: 删除{deleted_count}条，保留{len(df_filtered)}条")

                    cleaned_periods.append(period_key)
                except Exception as e:
                    logger.warning(f"清理失败 {symbol} {period_key}: {e}")

            return {
                "symbol": symbol,
                "success": True,
                "periods": cleaned_periods
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "success": False,
                "error": str(e)
            }

    def delete_batch(
        self,
        symbols: List[str],
        del_date: str,
        max_workers: int = 10,
        progress_callback=None
    ) -> Dict:
        """
        批量删除历史数据

        Args:
            symbols: 股票代码列表
            del_date: 删除起始日期(YYYY-MM-DD)
            max_workers: 并发数，默认10
            progress_callback: 进度回调函数

        Returns:
            删除统计
        """
        start_time = datetime.now()
        results = []
        success_count = 0
        fail_count = 0
        future_start_times = {}

        print(f"\n开始批量清理历史数据 (日期 >= {del_date})...")
        print(f"股票数量: {len(symbols)} (并发数: {max_workers})")
        print("=" * 50)

        try:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix='tdx_deleter'
            ) as executor:
                futures = {}
                for symbol in symbols:
                    future = executor.submit(self.delete_single_stock, symbol, del_date)
                    futures[future] = symbol
                    future_start_times[future] = datetime.now()

                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    symbol = futures[future]
                    task_time = datetime.now() - future_start_times.get(future, start_time)
                    try:
                        result = future.result()
                    except Exception as e:
                        result = {
                            "symbol": symbol,
                            "success": False,
                            "error": str(e)
                        }
                        logger.error(f"线程异常: {symbol} - {e}")

                    result["time"] = str(task_time).split('.')[0]
                    results.append(result)

                    if result["success"]:
                        success_count += 1
                    else:
                        fail_count += 1
                        error_msg = result.get('error', 'Unknown')
                        print(f"\n  失败: {result['symbol']} - {error_msg}")

                    progress = f"[{i}/{len(symbols)}]"
                    status = "✓" if result["success"] else "✗"
                    print(f"\r  {progress} {status} {result['symbol']} [{task_time.seconds}.{task_time.microseconds//10000}s]", end="", flush=True)

                    if progress_callback:
                        progress_callback(i, len(symbols), result)

        except Exception as e:
            logger.error(f"批量清理异常: {e}")
            raise

        use_time = datetime.now() - start_time
        self.stats = {
            "total": len(symbols),
            "success": success_count,
            "fail": fail_count,
            "time_seconds": int(use_time.total_seconds()),
            "results": results
        }

        print(f"\n\n批量清理完成:")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        print(f"  耗时: {use_time}")

        return self.stats

    def _get_last_date_from_file(self, file_path: str) -> Optional[str]:
        """
        从Excel文件获取最后一行日期

        Args:
            file_path: Excel文件路径

        Returns:
            最后日期字符串 (YYYY-MM-DD)，如果文件不存在或为空返回None
        """
        try:
            if not os.path.exists(file_path):
                return None

            df = pd.read_excel(file_path, usecols=[0])
            if df.empty:
                return None

            last_date = df.iloc[-1, 0]

            if isinstance(last_date, str):
                return last_date[:10]
            elif hasattr(last_date, 'strftime'):
                return last_date.strftime('%Y-%m-%d')
            else:
                return str(last_date)[:10]
        except Exception:
            return None

    def _is_data_up_to_date(self, last_date_str: str, today_str: str) -> bool:
        """
        检查数据是否已是最新（按日期判断）

        Args:
            last_date_str: 文件最后日期 (YYYY-MM-DD)
            today_str: 今日日期 (YYYYMMDD)

        Returns:
            True表示数据已是最新，无需更新
        """
        try:
            if not last_date_str or not today_str:
                return False

            last_date = pd.to_datetime(last_date_str).date()
            today_date = pd.to_datetime(today_str).date()
            return last_date >= today_date
        except Exception:
            return False

    def _check_columns_valid(self, df: pd.DataFrame) -> bool:
        """
        检查列名是否标准
        
        标准列: 日期, 股票代码, 开盘, 最高, 最低, 收盘, 成交量, 成交额, 换手率
        核心列: 日期, 开盘, 最高, 最低, 收盘, 成交量 (必须存在)
        """
        if df.empty:
            return False
        
        actual_cols = list(df.columns)
        standard_cols = ['日期', '股票代码', '开盘', '最高', '最低', '收盘', '成交量', '成交额', '换手率']
        
        if len(actual_cols) > len(standard_cols):
            return False
        
        core_cols = ['日期', '开盘', '最高', '最低', '收盘', '成交量']
        for col in core_cols:
            if col not in actual_cols:
                return False
        
        return True

    def _rename_columns(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        重命名列，标准化数据格式
        
        my_tdx_data.get_tdx_data 返回格式:
        - 日线: date, code, open, high, low, close, volume, amount, turnover_rate
        - 分钟线: datetime, code, open, high, low, close, volume, amount, turnover_rate
        
        标准列: 日期, 股票代码, 开盘, 最高, 最低, 收盘, 成交量, 成交额, 换手率
        """
        if df.empty:
            return df
        
        if period == 'daily':
            df = df.rename(columns={
                'date': '日期', 'code': '股票代码',
                'open': '开盘', 'high': '最高', 'low': '最低', 'close': '收盘',
                'volume': '成交量', 'amount': '成交额', 'turnover_rate': '换手率'
            })
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
        else:
            df = df.rename(columns={
                'datetime': '日期', 'code': '股票代码',
                'open': '开盘', 'high': '最高', 'low': '最低', 'close': '收盘',
                'volume': '成交量', 'amount': '成交额', 'turnover_rate': '换手率'
            })
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        if '股票代码' in df.columns:
            df['股票代码'] = df['股票代码'].astype(str).str.zfill(6)
        
        return df

    def update_single_stock(self, symbol: str, force_start_date: str = None) -> Dict:
        """
        更新单只股票的所有周期数据（优化版本）
        
        流程:
        1. 文件不存在 -> 全量获取 -> 标准化列名 -> 保存
        2. 文件存在 -> 读取 -> 检查列名
           - 列名不标准 -> 删除 -> 全量获取 -> 标准化列名 -> 保存
           - 列名标准 -> 获取最后日期 -> 检查是否最新
             - 已是最新 -> 跳过
             - 需要更新 -> 增量获取 -> 标准化列名 -> 合并去重 -> 保存

        Args:
            symbol: 股票代码
            force_start_date: 强制起始日期，删除该日期之后的数据重新获取

        Returns:
            更新结果
        """
        from datetime import datetime as dt
        period_times = {}
        
        try:
            stock_dir = os.path.join(self.stock_data_dir, symbol)
            os.makedirs(stock_dir, exist_ok=True)
            
            periods = [
                ('daily', 'daily', 'd'),
                ('min30', '30min', '30'),
                ('min5', '5min', '5'),
            ]
            
            saved_periods = []
            skipped_periods = []
            today_str = pd.to_datetime(self.today).strftime('%Y-%m-%d')
            
            for period_key, period_tdx, suffix in periods:
                t0 = dt.now()
                file_path = os.path.join(stock_dir, f"{symbol}_{suffix}.csv")
                
                if os.path.exists(file_path):
                    try:
                        old_df = pd.read_csv(file_path, encoding='utf-8-sig')
                    except Exception as read_err:
                        if "zip" in str(read_err).lower() or "not a valid" in str(read_err).lower() or "utf" in str(read_err).lower():
                            logger.warning(f"文件损坏，删除后重新获取: {file_path}")
                            os.remove(file_path)
                            new_df = my_tdx_data.get_tdx_data(symbol, period_tdx)
                            if new_df.empty:
                                print(f"获取到空数据: {symbol} {period_key}")
                                period_times[period_key] = (dt.now() - t0).total_seconds()
                                continue
                            result_df = self._rename_columns(new_df, period_tdx)
                            result_df['股票代码'] = symbol
                            result_df['股票代码'] = result_df['股票代码'].astype(str).str.zfill(6)
                            result_df['开盘'] = result_df['开盘'].round(2)
                            result_df['最高'] = result_df['最高'].round(2)
                            result_df['最低'] = result_df['最低'].round(2)
                            result_df['收盘'] = result_df['收盘'].round(2)
                            result_df['成交量'] = result_df['成交量'].astype(int)
                            result_df['成交额'] = result_df['成交额'].astype(int)
                            result_df['换手率'] = result_df['换手率'].round(4)
                            result_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                            saved_periods.append(period_key)
                            period_times[period_key] = (dt.now() - t0).total_seconds()
                            continue
                        else:
                            raise read_err
                    
                    if not self._check_columns_valid(old_df):
                        os.remove(file_path)
                        new_df = my_tdx_data.get_tdx_data(symbol, period_tdx)
                        if new_df.empty:
                            period_times[period_key] = (dt.now() - t0).total_seconds()
                            continue
                        result_df = self._rename_columns(new_df, period_tdx)
                    else:
                        if force_start_date:
                            old_df['日期'] = pd.to_datetime(old_df['日期'], format='mixed')
                            mask = old_df['日期'] >= pd.to_datetime(force_start_date)
                            if mask.any():
                                old_df = old_df[~mask]
                                if old_df.empty:
                                    os.remove(file_path)
                                    new_df = my_tdx_data.get_tdx_data(symbol, period_tdx)
                                    if new_df.empty:
                                        print(f"获取到空数据: {symbol} {period_key}")
                                        period_times[period_key] = (dt.now() - t0).total_seconds()
                                        continue
                                    result_df = self._rename_columns(new_df, period_tdx)
                                    result_df['股票代码'] = symbol
                                    result_df['股票代码'] = result_df['股票代码'].astype(str).str.zfill(6)
                                    result_df['开盘'] = result_df['开盘'].round(2)
                                    result_df['最高'] = result_df['最高'].round(2)
                                    result_df['最低'] = result_df['最低'].round(2)
                                    result_df['收盘'] = result_df['收盘'].round(2)
                                    result_df['成交量'] = result_df['成交量'].astype(int)
                                    result_df['成交额'] = result_df['成交额'].astype(int)
                                    result_df['换手率'] = result_df['换手率'].round(4)
                                    result_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                                    saved_periods.append(period_key)
                                    period_times[period_key] = (dt.now() - t0).total_seconds()
                                    continue
                            if period_key == 'daily':
                                old_df['日期'] = old_df['日期'].dt.strftime('%Y-%m-%d')
                            else:
                                old_df['日期'] = old_df['日期'].dt.strftime('%Y-%m-%d %H:%M:%S')
                        
                        last_date = pd.to_datetime(old_df.iloc[-1, 0]).strftime('%Y-%m-%d')
                        
                        if last_date == today_str:
                            skipped_periods.append(period_key)
                            period_times[period_key] = (dt.now() - t0).total_seconds()
                            continue
                        
                        start_date = (pd.to_datetime(last_date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                        new_df = my_tdx_data.get_tdx_data(symbol, period_tdx, start_date=start_date)
                        
                        if new_df.empty:
                            period_times[period_key] = (dt.now() - t0).total_seconds()
                            continue
                        
                        new_df = self._rename_columns(new_df, period_tdx)
                        result_df = pd.concat([old_df, new_df], ignore_index=True)
                        result_df = result_df.drop_duplicates(subset='日期')
                        if period_key == 'daily':
                            result_df['日期'] = pd.to_datetime(result_df['日期'], format='mixed').dt.strftime('%Y-%m-%d')
                        else:
                            result_df['日期'] = pd.to_datetime(result_df['日期'], format='mixed').dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    new_df = my_tdx_data.get_tdx_data(symbol, period_tdx)
                    if new_df.empty:
                        print(f"获取到空数据: {symbol} {period_key}")
                        period_times[period_key] = (dt.now() - t0).total_seconds()
                        continue
                    result_df = self._rename_columns(new_df, period_tdx)
                
                result_df['股票代码'] = symbol
                result_df['股票代码'] = result_df['股票代码'].astype(str).str.zfill(6)
                result_df['开盘'] = result_df['开盘'].round(2)
                result_df['最高'] = result_df['最高'].round(2)
                result_df['最低'] = result_df['最低'].round(2)
                result_df['收盘'] = result_df['收盘'].round(2)
                result_df['成交量'] = result_df['成交量'].astype(int)
                result_df['成交额'] = result_df['成交额'].astype(int)
                result_df['换手率'] = result_df['换手率'].round(4)
                result_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                saved_periods.append(period_key)
                period_times[period_key] = (dt.now() - t0).total_seconds()
            
            d_time = period_times.get('daily', 0)
            m30_time = period_times.get('min30', 0)
            m5_time = period_times.get('min5', 0)
            print(f"  {symbol}-{d_time:.1f}|{m30_time:.1f}|{m5_time:.1f}")
            
            return {
                "symbol": symbol,
                "success": True,
                "periods": saved_periods,
                "skipped": skipped_periods
            }
        except Exception as e:
            logger.error(f"更新股票数据失败 {symbol}: {e}")
            return {
                "symbol": symbol,
                "success": False,
                "error": str(e)
            }

    def update_batch(
        self,
        symbols: List[str],
        max_workers: int = 10,
        force_start_date: str = None,
        progress_callback=None,
        debug_timing: bool = False
    ) -> Dict:
        """
        批量更新股票数据

        Args:
            symbols: 股票代码列表
            max_workers: 并发数，默认10
            force_start_date: 强制起始日期(YYYY-MM-DD)，先清理再更新
            progress_callback: 进度回调函数
            debug_timing: 是否打印详细计时

        Returns:
            更新统计
        """
        if not self.today:
            self.get_trading_date()

        print("\n预加载 gbbq 缓存...")
        preload_start = datetime.now()
        my_tdx_data.preload_gbbq()
        print(f"  gbbq 预加载耗时: {(datetime.now() - preload_start).total_seconds():.2f}s")

        start_time = datetime.now()
        results = []
        success_count = 0
        fail_count = 0
        future_start_times = {}
        futures = {}

        print(f"\n开始批量更新 {len(symbols)} 只股票 (并发数: {max_workers})...")
        print("=" * 50)

        import warnings
        warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*signal wakeup fd.*')

        try:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix='tdx_updater'
            ) as executor:
                for symbol in symbols:
                    future = executor.submit(self.update_single_stock, symbol, force_start_date)
                    futures[future] = symbol
                    future_start_times[future] = datetime.now()

                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    symbol = futures[future]
                    task_time = datetime.now() - future_start_times.get(future, start_time)
                    try:
                        result = future.result()
                    except Exception as e:
                        result = {
                            "symbol": symbol,
                            "success": False,
                            "error": str(e)
                        }
                        logger.error(f"线程异常: {symbol} - {e}")

                    result["time"] = str(task_time).split('.')[0]
                    results.append(result)

                    if result["success"]:
                        success_count += 1
                    else:
                        fail_count += 1
                        error_msg = result.get('error', 'Unknown')
                        print(f"\n  失败: {result['symbol']} - {error_msg}")
                        logger.error(f"更新失败: {result['symbol']} - {error_msg}")

                    progress = f"[{i}/{len(symbols)}]"
                    status = "✓" if result["success"] else "✗"
                    skipped = result.get('skipped', [])
                    skip_info = f" (跳过:{','.join(skipped)})" if skipped else ""
                    print(f"\r  {progress} {status} {result['symbol']}{skip_info} [{task_time.seconds}.{task_time.microseconds//10000}s]", end="", flush=True)

                    if progress_callback:
                        progress_callback(i, len(symbols), result)

        except Exception as e:
            logger.error(f"批量更新异常: {e}")
            raise
        finally:
            my_tdx_data.clear_gbbq_cache()

        # 统计
        use_time = datetime.now() - start_time
        self.stats = {
            "total": len(symbols),
            "success": success_count,
            "fail": fail_count,
            "time_seconds": int(use_time.total_seconds()),
            "results": results
        }

        print(f"\n\n批量更新完成:")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        print(f"  耗时: {use_time}")

        # 打印失败股票列表
        if fail_count > 0:
            failed_stocks = [r for r in results if not r["success"]]
            print(f"\n失败股票列表:")
            for r in failed_stocks:
                error_msg = r.get('error', 'Unknown')[:50]  # 截取前50字符
                print(f"  {r['symbol']}: {error_msg}")

        return self.stats

    def run(self, days: int = 20, max_workers: int = 10, force_start_date: str = None, debug_limit: int = 0, debug_timing: bool = False) -> Dict:
        """
        执行完整的数据更新流程

        Args:
            days: 获取交易日天数
            max_workers: 并发数，默认10
            force_start_date: 强制起始日期(YYYY-MM-DD)，先清理再更新
            debug_limit: 调试限制股票数量，0表示不限制
            debug_timing: 是否打印详细计时

        Returns:
            更新统计
        """
        run_start = datetime.now()
        print("=" * 50)
        print("数据更新模块")
        print("=" * 50)

        # Step 1: 获取交易日
        step_start = datetime.now()
        print("\n[1/4] 获取交易日...")
        self.get_trading_date(days)
        print(f"  最近交易日: {self.today}")
        print(f"  耗时: {(datetime.now() - step_start).total_seconds():.2f}s")

        # Step 2: 获取涨停池
        step_start = datetime.now()
        print("\n[2/4] 获取涨停池...")
        zt_df = self.get_zt_pool()
        zt_count = len(zt_df) if not zt_df.empty else 0
        print(f"  涨停股票数: {zt_count}")
        print(f"  耗时: {(datetime.now() - step_start).total_seconds():.2f}s")

        # Step 3: 更新监控清单
        step_start = datetime.now()
        print("\n[3/4] 更新监控清单...")
        watchlist_df = self.update_watchlist()
        total_count = len(watchlist_df)
        print(f"  监控清单总数: {total_count}")
        print(f"  耗时: {(datetime.now() - step_start).total_seconds():.2f}s")

        # Step 4: 批量更新K线
        step_start = datetime.now()
        print("\n[4/4] 更新K线数据...")

        if watchlist_df.empty:
            print("  警告: 监控清单为空，跳过K线更新")
            return {"total": 0, "success": 0, "fail": 0, "time_seconds": 0}

        symbols = watchlist_df['代码'].tolist()
        
        if debug_limit > 0:
            symbols = symbols[:debug_limit]
            print(f"  [DEBUG] 限制股票数量: {debug_limit}")

        stats = self.update_batch(symbols, max_workers, force_start_date, debug_timing=debug_timing)
        print(f"  耗时: {(datetime.now() - step_start).total_seconds():.2f}s")

        total_time = (datetime.now() - run_start).total_seconds()
        print("\n" + "=" * 50)
        print(f"数据更新完成，总耗时: {total_time:.2f}s")
        print("=" * 50)

        return stats

    def get_summary_message(self) -> str:
        """
        生成摘要消息（用于通知）

        Returns:
            消息文本
        """
        if not self.stats:
            return "数据更新: 无统计数据"

        current_time = datetime.now().strftime("%H:%M:%S")
        return (
            f"{current_time} 数据更新完成 | "
            f"耗时: {self.stats['time_seconds']}秒 | "
            f"处理: {self.stats['total']}只 | "
            f"成功: {self.stats['success']} | "
            f"失败: {self.stats['fail']}"
        )


def send_notification(message: str, webhook_url: Optional[str] = None) -> bool:
    """
    发送完成通知

    Args:
        message: 消息内容
        webhook_url: 已废弃参数，保留向后兼容

    Returns:
        是否发送成功
    """
    try:
        # 支持直接运行和作为模块导入
        if __name__ == "__main__" and __package__ is None:
            from src.communication.feishu import send_feishu_text
            from src.utils.config import get_config
        else:
            from ..communication.feishu import send_feishu_text
            from ..utils.config import get_config

        config = get_config()

        # 检查飞书是否启用
        if config.get("communication.feishu.enabled", False):
            return send_feishu_text(message)
        else:
            print(f"通知: {message}")
            print("提示: 飞书通知未启用，请在 config.yaml 中配置 communication.feishu.enabled = true")
            return True

    except Exception as e:
        print(f"发送通知失败: {e}")
        return False


# ============================================================
# 从配置创建更新器
# ============================================================

def create_updater_from_config() -> DataUpdater:
    """
    从配置文件创建数据更新器

    Returns:
        DataUpdater 实例

    Raises:
        ValueError: 配置缺失时抛出
    """
    # 支持直接运行和作为模块导入
    if __name__ == "__main__" and __package__ is None:
        from src.utils.config import get_config
    else:
        from ..utils.config import get_config
    config = get_config()

    # 从配置读取路径（不使用硬编码默认值）
    base_dir = config.get("data.base_dir")
    if not base_dir:
        raise ValueError("配置缺失: data.base_dir")

    # 去掉末尾的 "股票数据" 以获取 daban 目录
    data_dir = base_dir
    for suffix in ["/股票数据", "\\股票数据", "/股票数据/", "\\股票数据\\"]:
        if data_dir.endswith(suffix):
            data_dir = data_dir[:-len(suffix)]
            break

    # 概念文件优先从配置读取，否则使用默认位置
    concept_file = config.get("data.concept_file")
    if not concept_file:
        concept_file = os.path.join(data_dir, "概念成分清单_合并.xlsx")

    watchlist_dir = config.get("data_source.watchlist.dir")
    if not watchlist_dir:
        raise ValueError("配置缺失: data_source.watchlist.dir")

    watchlist_file = config.get("data_source.watchlist.file", "check_list.xlsx")

    return DataUpdater(
        data_dir=data_dir,
        concept_file=concept_file,
        watchlist_dir=watchlist_dir,
        watchlist_file=watchlist_file
    )


# ============================================================
# 模块测试
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="历史数据更新")
    parser.add_argument("--debug", action="store_true", help="调试模式：测试各功能，不下载K线")
    parser.add_argument("--full", nargs='?', const=True, metavar="DATE", help="完整模式：执行完整数据更新。可指定日期(YYYY-MM-DD)先清理该日期后数据再更新")
    parser.add_argument("--limit", type=int, default=0, help="限制股票数量（用于调试，0表示不限制）")
    parser.add_argument("--workers", type=int, default=10, help="并发线程数，默认10")
    parser.add_argument("--timing", action="store_true", help="打印详细计时信息")

    args = parser.parse_args()
    DEBUG_LIMIT = args.limit
    DEBUG_WORKERS = args.workers
    DEBUG_TIMING = args.timing

    if args.debug:
        MODE = "debug"
        FORCE_DATE = None
    elif args.full:
        if args.full is True:
            MODE = "full"
            FORCE_DATE = None
        else:
            MODE = "full_force"
            FORCE_DATE = args.full
    else:
        MODE = "full"
        FORCE_DATE = None

    print("=" * 50)
    print(f"数据更新模块 [{MODE.upper()} 模式]")
    if FORCE_DATE:
        print(f"强制日期: >= {FORCE_DATE} (先清理再更新)")
    print("=" * 50)

    # 从配置文件创建更新器（路径从 config.yaml 读取）
    try:
        updater = create_updater_from_config()
        print(f"\n配置加载成功:")
        print(f"  数据目录: {updater.data_dir}")
        print(f"  概念文件: {updater.concept_file}")
        print(f"  监控清单: {updater.watchlist_path}")
    except Exception as e:
        print(f"\n[FAIL] 配置加载失败: {e}")
        exit(1)

    try:
        if MODE == "debug":
            # Debug 模式：测试各功能，不下载K线
            print("\n[DEBUG] 测试获取交易日")
            today, dates = updater.get_trading_date(10)
            print(f"  [OK] 最近交易日: {today}")
            print(f"  [OK] 交易日列表: {dates[:3]}...")

            print("\n[DEBUG] 测试获取涨停池")
            zt_df = updater.get_zt_pool()
            if not zt_df.empty:
                print(f"  [OK] 涨停股票数量: {len(zt_df)}")
            else:
                print("  [WARN] 涨停池数据为空")

            print("\n[DEBUG] 测试更新监控清单")
            watchlist_df = updater.update_watchlist()
            print(f"  [OK] 监控清单总数: {len(watchlist_df)}")

            print("\n" + "=" * 50)
            print("[OK] Debug 模式测试通过")
            print("=" * 50)
            print("\n提示: 使用 --full 参数执行完整更新")
            print("  --full              增量更新（跳过已有最新数据）")
            print("  --full 2026-03-01   强制更新（先清理>=该日期数据，再增量获取）")

        elif MODE in ("full", "full_force"):
            # Full 模式：执行完整更新
            stats = updater.run(days=10, max_workers=DEBUG_WORKERS, force_start_date=FORCE_DATE, debug_limit=DEBUG_LIMIT, debug_timing=DEBUG_TIMING)

            # 发送通知
            message = updater.get_summary_message()
            print(f"\n{message}")
            send_notification(message)

            print("\n" + "=" * 50)
            print("[OK] 完整更新完成")
            print("=" * 50)

    except Exception as e:
        print(f"\n[FAIL] 执行失败: {e}")
        import traceback
        traceback.print_exc()