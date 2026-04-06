import sys
import yaml
import pandas as pd
from pathlib import Path

# 确保在导入 qlib 前挂载源码路径
sys.path.insert(0, r"D:\code\qlib")

try:
    import qlib
    from qlib.constant import REG_CN
    from qlib.utils import init_instance_by_config
    from qlib.contrib.data.handler import Alpha158
    from qlib.data.dataset.handler import DataHandlerLP
    from qlib.data.dataset import DatasetH
    from qlib.data.dataset.processor import DropnaProcessor, RobustZScoreNorm, Fillna
    from qlib.contrib.model.gbdt import LGBModel
except ImportError:
    qlib = None

root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.analysis.factors import QlibFactorEngine
from src.data.qlib_dump import load_backtest_targets

def get_ml_split_config():
    root_dir = Path(__file__).resolve().parent.parent.parent
    config_path = root_dir / "config" / "config.yaml"
    
    if not config_path.exists():
        return ("2024-01-01", "2024-06-30"), ("2024-07-01", "2024-08-31"), ("2024-09-01", "2024-12-31")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f).get("backtest", {})
        
    train = (cfg.get("train_start", "2024-01-01"), cfg.get("train_end", "2024-06-30"))
    valid = (cfg.get("valid_start", "2024-07-01"), cfg.get("valid_end", "2024-08-31"))
    test = (cfg.get("start_time", "2024-09-01"), cfg.get("end_time", "2024-12-31"))
    return train, valid, test

def train_lightgbm_model():
    """使用原生 QLib 构建 Dataset 并训练 LightGBM"""
    if qlib is None:
        raise ImportError("Qlib is missing or source path is incorrect.")
        
    # 1. 挂载 QLib 中心数据库
    QlibFactorEngine.init_qlib()
    
    symbols = load_backtest_targets()
    if not symbols:
        print("无回测目标数据")
        return None
    
    sz_sh_symbols = [f"SH{s}" if str(s).startswith('6') else f"SZ{s}" for s in symbols]
    
    # 2. 从配置获取时间切片
    train_period, valid_period, test_period = get_ml_split_config()
    print(f"================ ML 数据切分 ================")
    print(f"Train: {train_period[0]} ~ {train_period[1]}")
    print(f"Valid: {valid_period[0]} ~ {valid_period[1]}")
    print(f"Test : {test_period[0]} ~ {test_period[1]}")
    
    # 3. 构造 DataHandler (使用 Alpha158 提取特征 + 未来 5 天收益作为 Label)
    print("正在计算 Alpha158 特征与未来 5 日收益 Label，请稍候...")
    
    data_handler_config = {
        "class": "Alpha158",
        "module_path": "qlib.contrib.data.handler",
        "kwargs": {
            "start_time": train_period[0],
            "end_time": test_period[1],
            "instruments": sz_sh_symbols,
            # 添加预测的 Label: 以开盘价买入并在 5 个交易日后以开盘价卖出的收益作为基础
            "infer_processors": [
                {"class": "RobustZScoreNorm", "kwargs": {"fields_group": "feature", "clip_outlier": True}},
                {"class": "Fillna", "kwargs": {"fields_group": "feature"}}
            ],
            "learn_processors": [
                {"class": "DropnaProcessor", "kwargs": {"fields_group": "label"}},
            ],
            # 计算 Label 公式
            "label": ["Ref($open, -5) / $open - 1"],
        }
    }
    
    handler = init_instance_by_config(data_handler_config)
    
    # 4. 构建 Dataset 区间
    dataset_config = {
        "class": "DatasetH",
        "module_path": "qlib.data.dataset",
        "kwargs": {
            "handler": handler,
            "segments": {
                "train": train_period,
                "valid": valid_period,
                "test": test_period
            }
        }
    }
    
    dataset = init_instance_by_config(dataset_config)
    
    # 5. 配置 LightGBM 模型
    model_config = {
        "class": "LGBModel",
        "module_path": "qlib.contrib.model.gbdt",
        "kwargs": {
            "loss": "mse",
            "colsample_bytree": 0.8879,
            "learning_rate": 0.042,
            "subsample": 0.8789,
            "lambda_l1": 205.69,
            "lambda_l2": 580.97,
            "max_depth": 8,
            "num_leaves": 210,
            "num_threads": 4,
        }
    }
    
    print("================ 开始训练 LightGBM ================")
    model = init_instance_by_config(model_config)
    # 调用原生的 fit 方法
    model.fit(dataset)
    print("================ 训练完成！ ================")
    
    # 6. 推理并在 test 集上给出每日个股的预测得分
    pred = model.predict(dataset, segment="test")
    
    if isinstance(pred, pd.Series):
        pred.name = "score"
    elif isinstance(pred, pd.DataFrame) and not pred.empty:
        pred = pred.iloc[:, 0]
        pred.name = "score"
        
    return pred, test_period

if __name__ == "__main__":
    preds, test_p = train_lightgbm_model()
    if preds is not None:
        print(f"生成的预测信号矩阵预览：\n{preds.head()}")
