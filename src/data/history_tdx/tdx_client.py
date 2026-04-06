"""
通达信(TDX)数据客户端

提供与 baostock 兼容的接口，支持日线和5分钟线数据获取。

使用前需：
1. 启动通达信客户端并登录
2. 确保已下载对应的盘后数据
"""

import sys
import os
from pathlib import Path
from typing import Optional
import pandas as pd


# ============================================================
# 路径设置
# ============================================================

# TDX 插件路径 - tqcenter 在 user 目录下
_tdx_user_path = r"D:\8TDX\PYPlugins\user"
if _tdx_user_path not in sys.path:
    sys.path.insert(0, _tdx_user_path)

# 工作目录
TDX_WORK_DIR = Path(r"D:\8TDX\PYPlugins\user\txd_first")


# ============================================================
# 全局状态
# ============================================================

_initialized = False
_tq = None
TDX_AVAILABLE = False

try:
    from tqcenter import tq
    TDX_AVAILABLE = True
except ImportError:
    TDX_AVAILABLE = False
    print("警告: tqcenter模块未安装，请确保通达信客户端已安装并运行")


# ============================================================
# 兼容 baostock 的接口
# ============================================================

def tdx_login(login: int) -> None:
    """
    登录/登出通达信客户端

    Args:
        login: 1=登录, 0=登出

    兼容 baostock 的 bs_login 接口
    """
    global _initialized

    if not TDX_AVAILABLE:
        print('TDX login error: tqcenter模块不可用')
        return

    if login == 1:
        if not _initialized:
            # 设置工作目录
            os.chdir(str(TDX_WORK_DIR))
            tq.initialize(__file__)
            _initialized = True
            print('TDX login: 连接成功')
    else:
        if _initialized:
            tq.close()
            _initialized = False
            print('TDX logout: 已断开连接')


def get_tdx_data(
    symbol: str,
    period: str,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    获取K线数据

    Args:
        symbol: 6位股票代码，如 "000001"
        period: 周期，"d"=日线, "5"=5分钟
        start_date: 开始日期 YYYY-MM-DD 或 YYYYMMDD
        end_date: 结束日期 YYYY-MM-DD 或 YYYYMMDD

    Returns:
        DataFrame，列格式与 baostock 一致：
        - 日线: date, code, open, close, high, low, volume, amount
        - 5分钟: date, code, open, close, high, low, volume, amount

    兼容 baostock 的 get_bao_data 接口
    """
    # 参数验证
    if period not in ("d", "5", "30"):
        print(f'get_tdx_data error: 不支持的周期 "{period}"，仅支持 "d", "5" 或 "30"')
        return pd.DataFrame()

    if not TDX_AVAILABLE:
        print('get_tdx_data error: tqcenter模块不可用')
        return pd.DataFrame()

    # 转换周期格式
    period_map = {"d": "1d", "5": "5m", "30": "30m"}
    tdx_period = period_map[period]

    # 转换日期格式: YYYY-MM-DD -> YYYYMMDD
    start = start_date.replace("-", "")
    end = end_date.replace("-", "")

    # 转换股票代码
    code = _format_stock_code(symbol)

    # 调用 TDX API
    try:
        # tq.get_market_data 返回字典格式:
        # {'Open': DataFrame, 'Close': DataFrame, ...}
        data_dict = tq.get_market_data(
            stock_list=[code],
            start_time=start,
            end_time=end,
            period=tdx_period,
            dividend_type='none',
            fill_data=False
        )
    except Exception as e:
        print(f'get_tdx_data error: {e}')
        return pd.DataFrame()

    # 标准化输出
    return _normalize_data(data_dict, symbol, code, period)


def _format_stock_code(symbol: str) -> str:
    """
    转换股票代码格式

    Args:
        symbol: 6位代码，如 "000001"

    Returns:
        TDX格式: "000001.SZ"
    """
    if symbol.startswith('6'):
        return f"{symbol}.SH"
    elif symbol.startswith(('0', '3')):
        return f"{symbol}.SZ"
    elif symbol.startswith(('8', '9', '4')):
        return f"{symbol}.BJ"
    return f"{symbol}.SZ"


def _normalize_data(data_dict: dict, symbol: str, tdx_code: str, period: str) -> pd.DataFrame:
    """
    标准化数据格式，与 baostock 输出一致

    TQ 返回格式: {'Open': DataFrame, 'Close': DataFrame, ...}
    每个 DataFrame 的 index 是时间，columns 是股票代码

    目标格式:
    - 日线: date, code, open, close, high, low, volume, amount, turn
    - 分钟线: time, code, open, close, high, low, volume, amount
    """
    if not data_dict:
        return pd.DataFrame()

    # 检查必需字段
    required_fields = ['Open', 'Close', 'High', 'Low']
    if not all(f in data_dict for f in required_fields):
        print(f'get_tdx_data error: 缺少必需字段，返回: {list(data_dict.keys())}')
        return pd.DataFrame()

    # 获取时间索引
    close_df = data_dict['Close']
    if close_df.empty:
        return pd.DataFrame()

    # 提取时间索引
    dates = close_df.index

    # 构建结果 DataFrame
    result = pd.DataFrame()

    # 根据周期设置时间列
    # 日线用 date，分钟线用 time（与 baostock 一致）
    if period == "d":
        result['date'] = dates.strftime('%Y-%m-%d')
    else:
        # 分钟线：格式 YYYYMMDDHHMMSS000 (兼容 baostock)
        result['time'] = dates.strftime('%Y%m%d%H%M%S000')

    result['code'] = symbol

    # 提取各字段数据
    field_map = {
        'Open': 'open',
        'Close': 'close',
        'High': 'high',
        'Low': 'low',
        'Volume': 'volume',
        'Amount': 'amount'
    }

    for tdx_field, output_field in field_map.items():
        if tdx_field in data_dict:
            df = data_dict[tdx_field]
            if tdx_code in df.columns:
                result[output_field] = df[tdx_code].values
            elif len(df.columns) > 0:
                result[output_field] = df.iloc[:, 0].values

    # 日线数据：计算换手率
    if period == "d" and 'volume' in result.columns:
        free_float = _get_free_float_shares(tdx_code)
        if free_float and free_float > 0:
            result['turn'] = (result['volume'] / free_float * 100).round(4)
        else:
            result['turn'] = None

    # 统一列顺序
    if period == "d":
        columns = ['date', 'code', 'open', 'close', 'high', 'low', 'volume', 'amount', 'turn']
    else:
        columns = ['time', 'code', 'open', 'close', 'high', 'low', 'volume', 'amount']
    existing_cols = [c for c in columns if c in result.columns]

    return result[existing_cols]


def _get_free_float_shares(tdx_code: str) -> float:
    """
    从 TDX 获取流通股本

    Args:
        tdx_code: TDX 格式代码 (如 000001.SZ)

    Returns:
        流通股本（股数），失败返回 0
    """
    try:
        if not TDX_AVAILABLE:
            return 0
        info = tq.get_stock_info(tdx_code)
        if info and 'VolBase' in info:
            # VolBase 单位为万手，1手=100股
            vol_base = float(info['VolBase'])
            return vol_base * 10000 * 100  # 转换为股数
    except Exception as e:
        print(f"获取流通股本失败 {tdx_code}: {e}")
    return 0


# ============================================================
# 便捷函数
# ============================================================

def get_exchange_all_tdx(stock_code: str) -> str:
    """
    转换股票代码格式（兼容 baostock 的 get_exchange_all_bao）

    Args:
        stock_code: 6位代码

    Returns:
        TDX格式代码
    """
    return _format_stock_code(stock_code)