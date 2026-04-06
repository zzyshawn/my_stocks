"""
TDX 历史数据模块测试脚本

运行前请确保：
1. 通达信客户端已启动并登录
2. 已下载对应的盘后数据
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.history_tdx import tdx_login, get_tdx_data, get_exchange_all_tdx


def test_tdx_module():
    """测试 TDX 模块功能"""

    print("=" * 60)
    print("TDX 历史数据模块测试")
    print("=" * 60)

    # 1. 测试代码转换
    print("\n[1] 测试代码转换:")
    codes = ['600000', '000001', '300001', '830001']
    for code in codes:
        print(f"  {code} -> {get_exchange_all_tdx(code)}")

    # 2. 登录
    print("\n[2] 登录通达信:")
    tdx_login(1)

    # 3. 测试日线数据
    print("\n[3] 获取日线数据 (600000 浦发银行):")
    df = get_tdx_data("600000", "d", "2025-01-01", "2025-03-01")
    if not df.empty:
        print(f"  获取 {len(df)} 条记录")
        print(f"  列名: {df.columns.tolist()}")
        print(f"\n  前5条数据:")
        print(df.head().to_string(index=False))
    else:
        print("  获取失败或无数据")

    # 4. 测试5分钟数据
    print("\n[4] 获取5分钟数据 (000001 平安银行):")
    df = get_tdx_data("000001", "5", "2025-03-01", "2025-03-15")
    if not df.empty:
        print(f"  获取 {len(df)} 条记录")
        print(f"  列名: {df.columns.tolist()}")
        print(f"\n  前5条数据:")
        print(df.head().to_string(index=False))
    else:
        print("  获取失败或无数据")

    # 5. 测试创业板
    print("\n[5] 获取创业板日线数据 (300750 宁德时代):")
    df = get_tdx_data("300750", "d", "2025-01-01", "2025-03-01")
    if not df.empty:
        print(f"  获取 {len(df)} 条记录")
        print(f"\n  前3条数据:")
        print(df.head(3).to_string(index=False))
    else:
        print("  获取失败或无数据")

    # 6. 登出
    print("\n[6] 登出通达信:")
    tdx_login(0)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_tdx_module()