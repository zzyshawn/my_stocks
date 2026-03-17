"""
My Stocks 工具模块
"""

from .config import (
    ConfigManager,
    get_config,
    reload_config,
    get,
    set_value,
    get_data_dir,
    format_folder_name,
    format_file_name,
)

__all__ = [
    "ConfigManager",
    "get_config",
    "reload_config",
    "get",
    "set_value",
    "get_data_dir",
    "format_folder_name",
    "format_file_name",
]

# 在 ConfigManager 类中添加的新方法，通过 get_config() 访问
# get_kline_file_path(symbol, period) - 获取K线数据文件路径
# list_available_periods(symbol) - 列出股票可用的数据周期