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

# 配置日志
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
    # 直接运行时，添加项目根目录到路径
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from src.data.history.globals import set_jin_ri, set_zt_list, get_zt_list
    from src.data.history.kline_fetcher import KLineFetcher
    from src.data.history.zt_pool_fetcher import ZtPoolFetcher
    from src.data.history.baostock_client import bs_login
    from src.data.history_tdx.tdx_client import tdx_login
else:
    from .globals import set_jin_ri, set_zt_list, get_zt_list
    from .kline_fetcher import KLineFetcher
    from .zt_pool_fetcher import ZtPoolFetcher
    from .baostock_client import bs_login
    from ..history_tdx.tdx_client import tdx_login


class DataUpdater:
    """数据更新器"""

    def __init__(
        self,
        data_dir: str,
        concept_file: str,
        watchlist_dir: str,
        watchlist_file: str = "check_list.xlsx",
        end_date: str = "2026-12-31",
        source: str = "tdx"
    ):
        """
        初始化数据更新器

        Args:
            data_dir: 数据根目录 (H:/股票信息/股票数据库/daban)
            concept_file: 概念成分清单文件路径
            watchlist_dir: 监控清单目录
            watchlist_file: 监控清单文件名
            end_date: 数据获取结束日期
            source: 数据源 ('tdx' 或 'baostock')
        """
        self.data_dir = data_dir
        self.stock_data_dir = os.path.join(data_dir, "股票数据")
        self.concept_file = concept_file
        self.watchlist_path = os.path.join(watchlist_dir, watchlist_file)
        self.source = source

        # 初始化子模块
        self.zt_fetcher = ZtPoolFetcher(data_dir, concept_file)
        self.kline_fetcher = KLineFetcher(self.stock_data_dir, end_date, source=source)

        # 状态
        self.today: str = ""
        self.trading_dates: List[str] = []
        self.stats: Dict = {}

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

    def update_single_stock(self, symbol: str, today_dash: str) -> Dict:
        """
        更新单只股票的所有周期数据

        Args:
            symbol: 股票代码
            today_dash: 今日日期 (YYYY-MM-DD)

        Returns:
            更新结果
        """
        try:
            results = self.kline_fetcher.update_all_periods(symbol, today_dash)
            return {
                "symbol": symbol,
                "success": True,
                "periods": list(results.keys())
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "success": False,
                "error": str(e)
            }

    def update_batch(
        self,
        symbols: List[str],
        max_workers: int = 1,
        progress_callback=None
    ) -> Dict:
        """
        批量更新股票数据

        Args:
            symbols: 股票代码列表
            max_workers: 并发数
            progress_callback: 进度回调函数

        Returns:
            更新统计
        """
        if not self.today:
            self.get_trading_date()

        # 格式化日期
        date_obj = datetime.strptime(self.today, '%Y%m%d')
        today_dash = date_obj.strftime('%Y-%m-%d')

        # 登录数据源
        if self.source == 'tdx':
            tdx_login(1)
        else:
            bs_login(1)

        start_time = datetime.now()
        results = []
        success_count = 0
        fail_count = 0

        print(f"\n开始批量更新 {len(symbols)} 只股票...")
        print("=" * 50)

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.update_single_stock, symbol, today_dash): symbol
                    for symbol in symbols
                }

                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    symbol = futures[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        result = {
                            "symbol": symbol,
                            "success": False,
                            "error": str(e)
                        }
                        logger.error(f"线程异常: {symbol} - {e}")

                    results.append(result)

                    if result["success"]:
                        success_count += 1
                    else:
                        fail_count += 1
                        error_msg = result.get('error', 'Unknown')
                        print(f"  失败: {result['symbol']} - {error_msg}")
                        logger.error(f"更新失败: {result['symbol']} - {error_msg}")

                    # 进度显示
                    progress = f"[{i}/{len(symbols)}]"
                    status = "✓" if result["success"] else "✗"
                    print(f"\r  {progress} {status} {result['symbol']}", end="", flush=True)

                    if progress_callback:
                        progress_callback(i, len(symbols), result)

        except Exception as e:
            logger.error(f"批量更新异常: {e}")
            raise
        finally:
            # 登出数据源
            if self.source == 'tdx':
                tdx_login(0)
            else:
                bs_login(0)

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

    def run(self, days: int = 20, max_workers: int = 1) -> Dict:
        """
        执行完整的数据更新流程

        Args:
            days: 获取交易日天数
            max_workers: 并发数

        Returns:
            更新统计
        """
        print("=" * 50)
        print("数据更新模块")
        print("=" * 50)

        # Step 1: 获取交易日
        print("\n[1/4] 获取交易日...")
        self.get_trading_date(days)
        print(f"  最近交易日: {self.today}")

        # Step 2: 获取涨停池
        print("\n[2/4] 获取涨停池...")
        zt_df = self.get_zt_pool()
        zt_count = len(zt_df) if not zt_df.empty else 0
        print(f"  涨停股票数: {zt_count}")

        # Step 3: 更新监控清单
        print("\n[3/4] 更新监控清单...")
        watchlist_df = self.update_watchlist()
        print(f"  监控清单总数: {len(watchlist_df)}")

        # Step 4: 批量更新K线
        print("\n[4/4] 更新K线数据...")

        if watchlist_df.empty:
            print("  警告: 监控清单为空，跳过K线更新")
            return {"total": 0, "success": 0, "fail": 0, "time_seconds": 0}

        symbols = watchlist_df['代码'].tolist()
        stats = self.update_batch(symbols, max_workers)

        print("\n" + "=" * 50)
        print("数据更新完成")
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
    parser.add_argument("--full", action="store_true", help="完整模式：执行完整数据更新（包括K线下载）")

    args = parser.parse_args()

    # 根据参数设置模式
    if args.debug:
        MODE = "debug"
    elif args.full:
        MODE = "full"
    else:
        MODE = "full"  # 默认完整模式

    print("=" * 50)
    print(f"数据更新模块 [{MODE.upper()} 模式]")
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
            print("\n提示: 切换到 full 模式执行完整数据更新")
            print("  修改 MODE = 'full' 后重新运行")

        elif MODE == "full":
            # Full 模式：执行完整更新
            stats = updater.run(days=10, max_workers=1)

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