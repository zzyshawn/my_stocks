"""
通达信(TDX)历史数据模块

提供与 baostock 兼容的接口，支持日线和5分钟线数据获取。

使用方式与 baostock_client 一致：

    from src.data.history_tdx import tdx_login, get_tdx_data

    # 登录
    tdx_login(1)

    # 获取日线
    df = get_tdx_data("000001", "d", "2025-01-01", "2025-03-01")

    # 获取5分钟线
    df = get_tdx_data("000001", "5", "2025-01-01", "2025-03-01")

    # 登出
    tdx_login(0)
"""

from .tdx_client import (
    tdx_login,
    get_tdx_data,
    get_exchange_all_tdx,
)

__all__ = [
    "tdx_login",
    "get_tdx_data",
    "get_exchange_all_tdx",
]