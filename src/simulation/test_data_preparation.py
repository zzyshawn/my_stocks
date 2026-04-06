"""
测试数据准备模块

运行方式:
    python -m src.simulation.test_data_preparation [stock_code]

示例:
    python -m src.simulation.test_data_preparation 000001
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.simulation.data_preparation import DataPreparation, prepare_single_stock


def test_data_preparation(stock_code: str = "000001"):
    """测试数据准备功能"""

    print(f"\n{'='*60}")
    print(f"测试数据准备模块 - 股票代码: {stock_code}")
    print(f"{'='*60}\n")

    try:
        # 1. 初始化数据准备模块
        print("步骤1: 初始化数据准备模块...")
        prep = DataPreparation()
        print(f"[OK] 初始化成功")
        print(f"  - 数据目录: {prep.base_dir}")
        print(f"  - 训练集截止: {prep.train_end}")
        print(f"  - 测试集区间: {prep.test_start} ~ {prep.test_end}")

        # 2. 加载日线数据
        print(f"\n步骤2: 加载 {stock_code} 日线数据...")
        df_daily = prep.load_kline_data(stock_code, "d")
        print(f"[OK] 加载成功，共 {len(df_daily)} 条记录")
        print(f"  - 日期范围: {df_daily['日期'].min()} ~ {df_daily['日期'].max()}")
        print(f"  - 列名: {list(df_daily.columns)}")

        # 3. 分割数据
        print(f"\n步骤3: 分割数据...")
        train_data, test_data = prep.split_data(df_daily)
        print(f"[OK] 分割完成")
        print(f"  - 训练集: {len(train_data)} 条")
        print(f"  - 测试集: {len(test_data)} 条")

        # 4. 保存分割后的数据
        print(f"\n步骤4: 保存分割后的数据...")
        train_file, test_file = prep.save_split_data(
            stock_code, "d", train_data, test_data
        )
        print(f"[OK] 保存成功")
        print(f"  - 训练集: {train_file}")
        print(f"  - 测试集: {test_file}")

        # 5. 验证保存的数据
        print(f"\n步骤5: 验证保存的数据...")
        train_check = pd.read_excel(train_file)
        test_check = pd.read_excel(test_file)
        print(f"[OK] 验证成功")
        print(f"  - 训练集文件: {len(train_check)} 条记录")
        print(f"  - 测试集文件: {len(test_check)} 条记录")

        # 6. 测试30分钟和5分钟数据
        print(f"\n步骤6: 测试30分钟数据...")
        try:
            df_30 = prep.load_kline_data(stock_code, "30")
            train_30, test_30 = prep.split_data(df_30)
            train_file_30, test_file_30 = prep.save_split_data(
                stock_code, "30", train_30, test_30
            )
            print(f"[OK] 30分钟数据处理成功")
            print(f"  - 训练集: {len(train_30)} 条")
            print(f"  - 测试集: {len(test_30)} 条")
        except FileNotFoundError:
            print(f"[!] 30分钟数据文件不存在，跳过")

        print(f"\n步骤7: 测试5分钟数据...")
        try:
            df_5 = prep.load_kline_data(stock_code, "5")
            train_5, test_5 = prep.split_data(df_5)
            train_file_5, test_file_5 = prep.save_split_data(
                stock_code, "5", train_5, test_5
            )
            print(f"[OK] 5分钟数据处理成功")
            print(f"  - 训练集: {len(train_5)} 条")
            print(f"  - 测试集: {len(test_5)} 条")
        except FileNotFoundError:
            print(f"[!] 5分钟数据文件不存在，跳过")

        print(f"\n{'='*60}")
        print(f"[PASS] 所有测试通过！")
        print(f"{'='*60}\n")

        return True

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_process_stock(stock_code: str = "000001"):
    """测试完整的股票处理流程"""

    print(f"\n{'='*60}")
    print(f"测试完整处理流程 - {stock_code}")
    print(f"{'='*60}\n")

    try:
        result = prepare_single_stock(stock_code, periods=["d", "30", "5"])

        print(f"\n处理结果:")
        print(f"  股票代码: {result['stock_code']}")
        print(f"  状态: {result['status']}")

        for period, info in result['periods'].items():
            print(f"\n  [{period}]:")
            print(f"    状态: {info['status']}")
            if info['status'] == 'success':
                print(f"    训练集: {info['train_count']} 条")
                print(f"    测试集: {info['test_count']} 条")
                print(f"    训练文件: {Path(info['train_file']).name}")
                print(f"    测试文件: {Path(info['test_file']).name}")
            elif 'error' in info:
                print(f"    错误: {info['error']}")

        return result['status'] == 'success'

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import pandas as pd

    # 获取股票代码
    stock_code = "000001"
    if len(sys.argv) > 1:
        stock_code = sys.argv[1].zfill(6)

    # 配置日志
    logger.remove()
    logger.add(sys.stdout, level="INFO")

    # 运行测试
    success = test_data_preparation(stock_code)

    if success:
        print("\n" + "="*60)
        print("运行完整处理流程测试...")
        print("="*60)
        test_process_stock(stock_code)
