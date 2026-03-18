"""
My Stocks 数据获取模块

提供股票历史数据的加载、合并、导出和更新功能。

子模块:
    - history: 历史数据获取和更新
    - history_demo: 演示文件
    - realtime_demo: 实时数据演示
    - realtime: 实时数据获取、存储和调度
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

# 从 realtime 子模块导入
from .realtime import (
    # 核心类
    RealtimeFetcher,
    RealtimeScheduler,
    RealtimeStorage,
    # 便捷函数
    create_scheduler_from_config,
    create_storage_from_config,
    load_target_list,
    run_realtime_task,
    # 工具函数
    get_exchange_code,
    is_trading_time,
    should_execute,
    get_time_slots,
    get_time_slots_0936,
    get_debug_time_slots,
    get_seconds_to_next_slot,
    get_current_position,
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
    # realtime
    "RealtimeFetcher",
    "RealtimeScheduler",
    "RealtimeStorage",
    "create_scheduler_from_config",
    "create_storage_from_config",
    "load_target_list",
    "run_realtime_task",
    "get_exchange_code",
    "is_trading_time",
    "should_execute",
    "get_time_slots",
    "get_time_slots_0936",
    "get_debug_time_slots",
    "get_seconds_to_next_slot",
    "get_current_position",
]