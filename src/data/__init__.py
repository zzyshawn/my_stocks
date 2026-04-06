"""
My Stocks 数据获取模块

提供股票历史数据的加载、合并、导出和更新功能。

子模块:
    - history: 历史数据获取和更新
    - realtime: 实时数据获取
"""

# 从 history 子模块导入所有功能
from .history import (
    # data_merger
    KLineDataLoader,
    DataMerger,
    DataExporter,
    load_kline,
    load_multiple_klines,
    merge_by_date,
    merge_by_symbol,
    # data_updater
    DataUpdater,
    create_updater_from_config,
    send_notification,
    # zt_pool_fetcher
    ZtPoolFetcher,
    get_trading_date,
    get_zt_pool,
    # kline_fetcher
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