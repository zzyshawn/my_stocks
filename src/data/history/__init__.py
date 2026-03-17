"""
历史数据模块

提供股票历史数据的获取、更新和管理功能。

模块:
    - data_merger: 数据加载、合并和导出
    - data_updater: 数据更新主入口
    - zt_pool_fetcher: 涨停池获取
    - kline_fetcher: K线数据获取
    - baostock_client: Baostock 数据客户端
    - globals: 全局状态管理
"""

from .data_merger import (
    KLineDataLoader,
    DataMerger,
    DataExporter,
    load_kline,
    load_multiple_klines,
    merge_by_date,
    merge_by_symbol,
)

from .data_updater import (
    DataUpdater,
    create_updater_from_config,
    send_notification,
)

from .zt_pool_fetcher import (
    ZtPoolFetcher,
    get_trading_date,
    get_zt_pool,
)

from .kline_fetcher import (
    KLineFetcher,
    update_kline,
)

__all__ = [
    # data_merger
    "KLineDataLoader",
    "DataMerger",
    "DataExporter",
    "load_kline",
    "load_multiple_klines",
    "merge_by_date",
    "merge_by_symbol",
    # data_updater
    "DataUpdater",
    "create_updater_from_config",
    "send_notification",
    # zt_pool_fetcher
    "ZtPoolFetcher",
    "get_trading_date",
    "get_zt_pool",
    # kline_fetcher
    "KLineFetcher",
    "update_kline",
]