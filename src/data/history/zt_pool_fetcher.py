"""
涨停池获取模块

从 akshare 获取涨停股票池数据，支持增量更新。
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

# 支持直接运行时添加项目根目录到 sys.path
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from datetime import datetime
from typing import List, Optional, Tuple

import akshare as ak
import pandas as pd


class ZtPoolFetcher:
    """涨停池数据获取器"""

    def __init__(self, data_dir: str, concept_file: Optional[str] = None):
        """
        初始化涨停池获取器

        Args:
            data_dir: 数据存储目录
            concept_file: 概念成分清单文件路径
        """
        self.data_dir = data_dir
        self.zt_dir = os.path.join(data_dir, "涨停数据")
        self.concept_file = concept_file
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """确保目录存在"""
        os.makedirs(self.zt_dir, exist_ok=True)

    def get_trading_date(self, days: int = 10) -> Tuple[str, List[str]]:
        """
        获取最近N个交易日

        Args:
            days: 获取天数

        Returns:
            (最近交易日, 交易日列表)
            - 最近交易日: 格式 'YYYYMMDD'
            - 交易日列表: ['YYYYMMDD', ...]
        """
        # 获取沪指数据
        stock_data = ak.stock_zh_index_daily(symbol="sh000001")

        # 获取最后一个交易日
        last_trading_day = stock_data['date'].iloc[-1]
        last_trading_day_str = pd.to_datetime(last_trading_day).strftime('%Y%m%d')

        # 获取最后N个交易日
        last_days = stock_data.tail(days)['date']
        last_days_str = [pd.to_datetime(day).strftime('%Y%m%d') for day in last_days]

        return last_trading_day_str, last_days_str

    def get_zt_pool(self, date: str, with_concept: bool = True) -> pd.DataFrame:
        """
        获取指定日期涨停股票池

        Args:
            date: 日期，格式 'YYYYMMDD'
            with_concept: 是否合并概念数据

        Returns:
            涨停股票DataFrame，包含代码、名称、概念等字段
        """
        output_file = os.path.join(self.zt_dir, f"hy{date}.xlsx")

        # 检查是否已存在
        if os.path.exists(output_file):
            print(f"{date} 涨停数据已存在，直接读取")
            return pd.read_excel(output_file, dtype={'代码': str})

        # 获取涨停池数据
        try:
            zt_df = ak.stock_zt_pool_em(date=date)
            zt_df.rename(columns={"序号": "日期"}, inplace=True)
            zt_df['日期'] = date
        except Exception as e:
            print(f"获取涨停池数据失败: {e}")
            return pd.DataFrame()

        # 合并概念数据
        if with_concept and self.concept_file and os.path.exists(self.concept_file):
            concept_df = pd.read_excel(self.concept_file, dtype={'代码': str})
            zt_df = pd.merge(
                left=zt_df,
                right=concept_df[['代码', '概念']],
                on='代码',
                how='left'
            )

        # 保存到文件
        zt_df.to_excel(output_file, index=False)
        print(f"涨停数据已保存: {output_file}")

        return zt_df

    def get_zt_codes(self, date: str) -> List[str]:
        """
        获取指定日期涨停股票代码列表

        Args:
            date: 日期，格式 'YYYYMMDD'

        Returns:
            股票代码列表
        """
        zt_df = self.get_zt_pool(date, with_concept=False)
        if zt_df.empty:
            return []
        return zt_df['代码'].tolist()

    def update_watchlist(
        self,
        date: str,
        watchlist_path: str,
        columns: List[str] = None
    ) -> pd.DataFrame:
        """
        更新监控清单，添加当日涨停股票

        Args:
            date: 日期
            watchlist_path: 监控清单文件路径
            columns: 保留的列

        Returns:
            更新后的监控清单
        """
        if columns is None:
            columns = ["日期", "代码", "名称"]

        # 获取涨停数据
        zt_df = self.get_zt_pool(date, with_concept=False)
        df_filtered = zt_df[columns] if all(c in zt_df.columns for c in columns) else zt_df

        # 读取或创建监控清单
        if os.path.exists(watchlist_path):
            print("监控清单已存在，追加数据")
            existing_df = pd.read_excel(watchlist_path, dtype={'代码': str})
            combined_df = pd.concat([existing_df, df_filtered], ignore_index=True)
            result_df = combined_df.drop_duplicates(subset='代码')
        else:
            result_df = df_filtered

        # 保存
        os.makedirs(os.path.dirname(watchlist_path), exist_ok=True)
        result_df.to_excel(watchlist_path, index=False)
        print(f"监控清单已更新: {watchlist_path}")

        return result_df


# ============================================================
# 便捷函数
# ============================================================

def get_trading_date(days: int = 10) -> Tuple[str, List[str]]:
    """获取最近N个交易日（便捷函数）"""
    fetcher = ZtPoolFetcher(data_dir=".")
    return fetcher.get_trading_date(days)


def get_zt_pool(date: str, data_dir: str = ".", concept_file: str = None) -> pd.DataFrame:
    """获取涨停池数据（便捷函数）"""
    fetcher = ZtPoolFetcher(data_dir, concept_file)
    return fetcher.get_zt_pool(date)


# ============================================================
# 模块测试
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("涨停池获取模块测试")
    print("=" * 50)

    try:
        # 从配置获取路径
        from src.utils.config import get_config
        config = get_config()
        base_dir = config.get("data.base_dir")
        if not base_dir:
            raise ValueError("配置缺失: data.base_dir")

        # 去掉末尾的 "股票数据" 以获取 daban 目录
        DATA_DIR = base_dir
        for suffix in ["/股票数据", "\\股票数据", "/股票数据/", "\\股票数据\\"]:
            if DATA_DIR.endswith(suffix):
                DATA_DIR = DATA_DIR[:-len(suffix)]
                break

        CONCEPT_FILE = config.get("data.concept_file")
        if not CONCEPT_FILE:
            CONCEPT_FILE = os.path.join(DATA_DIR, "概念成分清单_合并.xlsx")

        print(f"数据目录: {DATA_DIR}")
        print(f"概念文件: {CONCEPT_FILE}")

        fetcher = ZtPoolFetcher(DATA_DIR, CONCEPT_FILE)

        # 测试获取交易日
        print("\n测试: 获取交易日")
        today, dates = fetcher.get_trading_date(10)
        print(f"  最近交易日: {today}")
        print(f"  交易日列表: {dates[:3]}...")

        # 测试获取涨停池
        print("\n测试: 获取涨停池")
        zt_df = fetcher.get_zt_pool(today, with_concept=False)
        if not zt_df.empty:
            print(f"  涨停股票数量: {len(zt_df)}")
            print(f"  数据列: {list(zt_df.columns)[:5]}...")
        else:
            print("  涨停池数据为空")

        print("\n" + "=" * 50)
        print("测试完成")
        print("=" * 50)

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()