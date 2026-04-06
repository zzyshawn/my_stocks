import sys
import yaml
import pandas as pd
from pathlib import Path
from typing import List

sys.path.insert(0, r"D:\code\qlib")

try:
    import qlib
    from qlib.backtest import backtest, executor
    from qlib.contrib.strategy import TopkDropoutStrategy
    from qlib.contrib.evaluate import risk_analysis
except ImportError:
    qlib = None

root_dir = str(Path(__file__).parent.parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.analysis.factors import QlibFactorEngine
from src.data.qlib_dump import load_backtest_targets

def run_qlib_demo_lgbm():
    """使用 src/models/train_lgb 训练出来的真实 LightGBM 结果执行回测"""
    if qlib is None:
        print("Warning: QLib is not installed.")
        return
        
    try:
        from src.models.train_lgb import train_lightgbm_model
    except ImportError as e:
        print(f"无法导入 train_lgb: {e}")
        return
        
    print("========== 第一阶段：模型训练 ==========")
    preds, test_period = train_lightgbm_model()
    if preds is None or preds.empty:
        print("未生成有效的预测打分。")
        return
        
    start_time, end_time = test_period
    sz_sh_symbols = list(preds.index.get_level_values('instrument').unique())
    print(f"========== 第二阶段：回测执行 ==========")
    print(f"回测标的池: {sz_sh_symbols}")
    
    topk = max(1, len(sz_sh_symbols) // 3)
    
    strategy_config = {
        "class": "TopkDropoutStrategy",
        "module_path": "qlib.contrib.strategy",
        "kwargs": {
            "signal": preds,      # 直接将模型在 TEST 集上的每日得分丢入
            "topk": topk,
            "n_drop": max(1, topk // 2),
        },
    }

    executor_config = {
        "class": "SimulatorExecutor",
        "module_path": "qlib.backtest.executor",
        "kwargs": {
            "time_per_step": "day",
            "generate_portfolio_metrics": True,
        },
    }

    try:
        portfolio_metric_dict, indicator_dict = backtest(
            executor=executor_config,
            strategy=strategy_config,
            start_time=start_time,
            end_time=end_time
        )

        print("\n================== LightGBM 回测结果指标 ==================")
        for k, v in indicator_dict.items():
            print(f"[{k}]")
            print(v)
            print("-" * 50)
    except Exception as e:
        print(f"原生回测执行异常: {e}")

if __name__ == "__main__":
    # 执行基于真实 ML 模型的完整预测回测流水线
    run_qlib_demo_lgbm()
