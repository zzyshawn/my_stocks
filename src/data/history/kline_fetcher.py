"""
K线数据获取模块

支持从 baostock 获取日线和分钟线数据。
支持增量更新，自动合并历史数据。
"""

import os
import sys

# 设置环境变量解决 Windows 控制台中文乱码
os.environ['PYTHONIOENCODING'] = 'utf-8'


def _fix_windows_encoding():
    """修复 Windows 控制台编码问题"""
    if sys.platform != 'win32':
        return
    import io
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

import time
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

# 支持直接运行和作为模块导入
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from src.data.history.baostock_client import bs_login, get_bao_data
    from src.data.history_tdx.tdx_client import tdx_login, get_tdx_data
else:
    from .baostock_client import bs_login, get_bao_data
    from ..history_tdx.tdx_client import tdx_login, get_tdx_data


class KLineFetcher:
    """K线数据获取器"""

    def __init__(self, data_dir: str, end_date: str = "2026-12-31", source: str = "tdx"):
        """
        初始化K线获取器

        Args:
            data_dir: 股票数据根目录
            end_date: 数据获取结束日期
            source: 数据源 ('tdx' 或 'baostock')
        """
        self.data_dir = data_dir
        self.end_date = end_date
        self.end_date_dash = end_date
        self.source = source
        self._cache: Dict[str, pd.DataFrame] = {}

    def _get_stock_dir(self, symbol: str) -> str:
        """获取股票数据目录"""
        return os.path.join(self.data_dir, symbol)

    def _ensure_dir(self, path: str) -> None:
        """确保目录存在"""
        os.makedirs(path, exist_ok=True)

    def _normalize_data(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        标准化K线数据格式

        Args:
            df: 原始数据
            period: 周期 ('d', '30', '5')

        Returns:
            标准化后的数据
        """
        if df.empty:
            return df

        # 列名映射
        column_mapping = {
            'date': '日期',
            'time': '日期',
            'code': '股票代码',
            'open': '开盘',
            'close': '收盘',
            'high': '最高',
            'low': '最低',
            'volume': '成交量',
            'amount': '成交额',
            'turn': '换手率',
        }
        df = df.rename(columns=column_mapping)

        # 处理日期格式
        if period == 'd':
            df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
            columns = ['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '换手率']
        else:
            df['日期'] = pd.to_datetime(df['日期'].str[:14]).dt.strftime('%Y-%m-%d %H:%M:%S')
            columns = ['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', '成交额']

        # 数值转换
        for col in ['开盘', '收盘', '最高', '最低', '成交量', '成交额']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').round(2)

        # 处理股票代码
        if '股票代码' in df.columns and len(df) > 0:
            code = df['股票代码'].iloc[-1]
            if isinstance(code, str) and len(code) > 6:
                code = code[3:9]
            df['股票代码'] = str(code).zfill(6)

        # 返回指定列
        existing_cols = [c for c in columns if c in df.columns]
        return df[existing_cols]

    def fetch_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取日线数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            K线数据
        """
        try:
            if self.source == 'tdx':
                df = get_tdx_data(symbol, 'd', start_date, end_date)
            else:
                df = get_bao_data(symbol, 'd', start_date, end_date)
            return self._normalize_data(df, 'd')
        except Exception as e:
            print(f"{self.source} 获取日线失败 {symbol}: {e}")
            return pd.DataFrame()

    def fetch_minute(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "30"
    ) -> pd.DataFrame:
        """
        获取分钟数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            period: 周期 ('30' 或 '5')

        Returns:
            K线数据
        """
        try:
            if self.source == 'tdx':
                df = get_tdx_data(symbol, period, start_date, end_date)
            else:
                df = get_bao_data(symbol, period, start_date, end_date)
            return self._normalize_data(df, period)
        except Exception as e:
            print(f"{self.source} 获取分钟线失败 {symbol}: {e}")
            return pd.DataFrame()

    def update_daily(self, symbol: str, today: str) -> pd.DataFrame:
        """
        更新日线数据

        Args:
            symbol: 股票代码
            today: 今日日期 (YYYY-MM-DD)

        Returns:
            更新后的数据
        """
        stock_dir = self._get_stock_dir(symbol)
        file_path = os.path.join(stock_dir, f"{symbol}_d.xlsx")
        bi_dir = os.path.join(stock_dir, "biduan")
        bi_path = os.path.join(bi_dir, f"{symbol}_d.csv")

        self._ensure_dir(stock_dir)
        self._ensure_dir(bi_dir)

        # 检查现有文件
        if os.path.exists(file_path):
            old_df = pd.read_excel(file_path, dtype={'股票代码': str})
            old_df['股票代码'] = old_df['股票代码'].str.zfill(6)

            # 获取最后日期
            last_date = pd.to_datetime(old_df.iloc[-1, 0], errors='coerce').strftime('%Y-%m-%d')

            if len(old_df) < 60:
                last_date = '2024-01-01'

            if today == last_date:
                print(f"日线数据已是最新: {symbol}")
                return old_df

            # 增量获取
            print(f"更新日线: {symbol} (从 {last_date})")
            new_df = self.fetch_daily(symbol, last_date, self.end_date_dash)
            if new_df.empty:
                return old_df

            result_df = pd.concat([old_df, new_df], ignore_index=True)
            result_df = result_df.drop_duplicates(subset='日期')
        else:
            # 全量获取
            print(f"新建日线: {symbol}")
            result_df = self.fetch_daily(symbol, '2024-01-01', self.end_date_dash)

        # 保存
        if not result_df.empty:
            result_df.to_excel(file_path, index=False)

            # 保存CSV (缠论使用)
            csv_cols = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '换手率']
            csv_cols = [c for c in csv_cols if c in result_df.columns]
            result_df[csv_cols].to_csv(bi_path, index=False, encoding='gbk')

        return result_df

    def update_minute(
        self,
        symbol: str,
        today: str,
        period: str = "30"
    ) -> pd.DataFrame:
        """
        更新分钟线数据（使用 baostock）

        Args:
            symbol: 股票代码
            today: 今日日期 (YYYY-MM-DD)
            period: 周期 ('30' 或 '5')

        Returns:
            更新后的数据
        """
        stock_dir = self._get_stock_dir(symbol)
        file_path = os.path.join(stock_dir, f"{symbol}_{period}.xlsx")

        self._ensure_dir(stock_dir)

        # 检查现有文件
        if os.path.exists(file_path):
            old_df = pd.read_excel(file_path, dtype={'股票代码': str})
            old_df['股票代码'] = old_df['股票代码'].str.zfill(6)

            # 获取最后日期时间
            last_datetime = pd.to_datetime(old_df.iloc[-1, 0], errors='coerce')
            last_date = last_datetime.strftime('%Y-%m-%d')

            if len(old_df) < 60:
                last_date = '2024-01-01'

            # 检查是否已是最新（同一天的数据）
            if today == last_date:
                print(f"分钟{period}线数据已是最新: {symbol}")
                return old_df

            # 增量获取
            print(f"更新分钟{period}线: {symbol} (从 {last_date})")
            new_df = self.fetch_minute(symbol, last_date, self.end_date_dash, period)
            if new_df.empty:
                return old_df

            result_df = pd.concat([old_df, new_df], ignore_index=True)
            result_df = result_df.drop_duplicates(subset='日期')
        else:
            # 全量获取
            print(f"新建分钟{period}线: {symbol}")
            result_df = self.fetch_minute(symbol, '2024-01-01', self.end_date_dash, period)

        # 保存
        if not result_df.empty:
            result_df.to_excel(file_path, index=False)
            time.sleep(0.1)

        return result_df

    def update_all_periods(self, symbol: str, today: str) -> Dict[str, pd.DataFrame]:
        """
        更新所有周期数据

        Args:
            symbol: 股票代码
            today: 今日日期 (YYYY-MM-DD)

        Returns:
            各周期数据字典
        """
        results = {}

        # 日线
        results['d'] = self.update_daily(symbol, today)

        # 30分钟线
        results['30'] = self.update_minute(symbol, today, "30")
        

        # 5分钟线
        results['5'] = self.update_minute(symbol, today, "5")

        return results


# ============================================================
# 便捷函数
# ============================================================

def update_kline(symbol: str, today: str, data_dir: str, period: str = "d") -> pd.DataFrame:
    """更新K线数据（便捷函数）"""
    fetcher = KLineFetcher(data_dir)
    if period == "d":
        return fetcher.update_daily(symbol, today)
    else:
        return fetcher.update_minute(symbol, today, period)


# ============================================================
# 模块测试
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("K线获取模块测试")
    print("=" * 50)

    try:
        # 从配置获取路径
        from src.utils.config import get_config
        config = get_config()
        DATA_DIR = config.get("data.base_dir")
        if not DATA_DIR:
            raise ValueError("配置缺失: data.base_dir")
        print(f"数据目录: {DATA_DIR}")

        fetcher = KLineFetcher(DATA_DIR)

        # 测试获取日线
        print("\n测试: 更新日线数据")
        df = fetcher.update_daily("000001", "2026-03-17")
        if not df.empty:
            print(f"  数据行数: {len(df)}")
            print(f"  最新日期: {df['日期'].iloc[-1]}")
        else:
            print("  日线数据为空")

        print("\n" + "=" * 50)
        print("测试完成")
        print("=" * 50)

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()